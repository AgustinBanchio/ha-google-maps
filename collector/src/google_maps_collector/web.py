"""Loopback management with bounded input and fixed public errors."""

import asyncio
from collections import OrderedDict
import hashlib
import hmac
import json
import logging
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from .google_maps import GoogleError, InvalidSession, InvalidData, NetworkFailure, parse_cookies
from .store import StoreError

SESSION_SECONDS = 3600


def password_verifier(password: str) -> dict:
    if not 12 <= len(password) <= 1024:
        raise ValueError("admin password must contain 12 to 1024 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=64*1024*1024)
    return {"version": 1, "salt": salt.hex(), "digest": digest.hex()}


def check_password(password, verifier):
    if not isinstance(password, str) or len(password) > 1024:
        return False
    candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(verifier["salt"]),
        n=32768, r=8, p=1, maxmem=64*1024*1024)
    return hmac.compare_digest(candidate, bytes.fromhex(verifier["digest"]))


async def bounded_body(request, limit):
    lengths = request.headers.getlist("content-length")
    if lengths:
        if len(lengths) != 1 or not lengths[0].isdigit() or int(lengths[0]) > limit:
            raise HTTPException(413)
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > limit:
            raise HTTPException(413)
        data.extend(chunk)
    return bytes(data)


def create_app(service, config, verifier, clock=time.monotonic):
    try:
        if verifier["version"] != 1 or len(bytes.fromhex(verifier["salt"])) != 16 or len(bytes.fromhex(verifier["digest"])) != 64:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise ValueError("invalid admin verifier") from None
    sessions = OrderedDict()
    failures = OrderedDict()
    login_slots = asyncio.Semaphore(2)
    origin = config.management_origin
    host = urlsplit(origin).netloc

    # Malformed multipart input must never reach logger handlers with upload content.
    for name in ("python_multipart.multipart", "multipart.multipart"):
        logger = logging.getLogger(name)
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False

    def boundary(request, mutation=False):
        if request.headers.getlist("host") != [host]:
            raise HTTPException(400)
        if mutation and request.headers.getlist("origin") != [origin]:
            raise HTTPException(403)

    def authenticated(request, mutation=False):
        boundary(request, mutation)
        token = request.cookies.get("collector_session", "")
        session = sessions.get(token)
        if session is None or session[0] <= clock():
            sessions.pop(token, None)
            raise HTTPException(401)
        if mutation and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), session[1]):
            raise HTTPException(403)
        return session

    async def index(request):
        boundary(request)
        return HTMLResponse(Path(__file__).with_name("static").joinpath("index.html").read_text())

    async def login(request):
        boundary(request, True)
        client = request.client.host if request.client else "local"
        now = clock()
        count, until = failures.get(client, (0, now + 300))
        if until <= now:
            count, until = 0, now + 300
        if count >= 5:
            raise HTTPException(429)
        # Count before yielding so simultaneous failures cannot bypass throttling.
        failures[client] = (count + 1, until)
        failures.move_to_end(client)
        while len(failures) > 1024:
            failures.popitem(last=False)
        data = await bounded_body(request, 4096)
        try:
            password = json.loads(data)["password"]
        except (ValueError, TypeError, KeyError, RecursionError):
            password = None
        async with login_slots:
            valid = await run_in_threadpool(check_password, password, verifier)
        if not valid:
            raise HTTPException(401)
        failures.pop(client, None)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        sessions[token] = (now + SESSION_SECONDS, csrf)
        while len(sessions) > 128:
            sessions.popitem(last=False)
        response = JSONResponse({"csrf_token": csrf})
        response.set_cookie("collector_session", token, httponly=True, samesite="strict",
                            max_age=SESSION_SECONDS, path="/")
        return response

    async def session(request):
        current = authenticated(request)
        return JSONResponse({"csrf_token": current[1]})

    async def logout(request):
        authenticated(request, True)
        sessions.pop(request.cookies.get("collector_session"), None)
        response = JSONResponse({"status": "logged_out"})
        response.delete_cookie("collector_session")
        return response

    async def status(request):
        authenticated(request)
        return JSONResponse(await run_in_threadpool(service.management_status))

    async def upload(request):
        authenticated(request, True)
        data = await bounded_body(request, config.upload_bytes)
        if not request.headers.get("content-type", "").startswith("multipart/form-data;"):
            raise HTTPException(400)
        try:
            # Prebuffering is bounded above; file content stays below spool threshold.
            request._body = data
            async with request.form(max_files=1, max_fields=0, max_part_size=config.upload_bytes) as form:
                if list(form) != ["cookies"] or len(form.multi_items()) != 1:
                    raise HTTPException(400)
                file = form["cookies"]
                if not hasattr(file, "read"):
                    raise HTTPException(400)
                candidate = parse_cookies(await file.read())
            await run_in_threadpool(service.import_cookies, candidate)
        except (GoogleError, StoreError, ValueError, UnicodeError):
            raise HTTPException(400) from None
        return JSONResponse({"status": "session_saved"})

    async def locations(request):
        # This bearer grants only the fixed data operation. It is never accepted
        # by management auth, cookie upload or arbitrary URL/command endpoints.
        if request.headers.getlist("host") not in (["127.0.0.1:8787"], ["localhost:8787"]):
            raise HTTPException(400)
        expected = None
        try:
            expected = config.data_token_file.read_text().strip()
        except OSError:
            pass
        supplied = request.headers.getlist("authorization")
        if (not expected or not 32 <= len(expected) <= 256 or len(supplied) != 1
                or not hmac.compare_digest(supplied[0].encode(), ("Bearer " + expected).encode())):
            raise HTTPException(401)
        if request.query_params or request.method != "GET":
            raise HTTPException(400)
        try:
            document = await run_in_threadpool(service.upstream_observations)
            return JSONResponse(document)
        except InvalidSession:
            return JSONResponse({"error": "google_session_required"}, status_code=409)
        except InvalidData:
            return JSONResponse({"error": "invalid_google_data"}, status_code=502)
        except NetworkFailure:
            return JSONResponse({"error": "google_unavailable"}, status_code=503)
        except (StoreError, GoogleError):
            return JSONResponse({"error": "source_unavailable"}, status_code=503)

    async def error(request, exception):
        codes = {400: "invalid_request", 401: "authentication_required", 403: "request_rejected",
                 404: "not_found", 405: "method_not_allowed", 413: "upload_too_large", 429: "try_later"}
        status = exception.status_code if isinstance(exception, HTTPException) else 500
        return JSONResponse({"error": codes.get(status, "request_failed")}, status_code=status)

    app = Starlette(routes=[Route("/", index), Route("/login", login, methods=["POST"]),
        Route("/session", session), Route("/logout", logout, methods=["POST"]),
        Route("/v1/locations", locations), Route("/status", status), Route("/cookies", upload, methods=["POST"])],
        exception_handlers={HTTPException: error, Exception: error})
    return SecurityHeaders(app)


class SecurityHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def secured(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([
                    (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"content-security-policy", b"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"),
                ])
            await send(message)
        await self.app(scope, receive, secured)
