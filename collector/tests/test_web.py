import json
import pytest
from starlette.testclient import TestClient
from google_maps_collector.config import Config
from google_maps_collector.google_maps import InvalidSession
from google_maps_collector.web import create_app, password_verifier
from test_google_maps import COOKIE

PASSWORD = "synthetic-admin-password"
ORIGIN = "http://127.0.0.1:8787"


class Service:
    def __init__(self):
        self.saved = 0
        self.error = False

    def management_status(self):
        return {"session_status": "ready", "last_successful_poll": None,
                "contact_count": 1, "approximate_cookie_expiry": None}

    def import_cookies(self, jar):
        if self.error:
            raise InvalidSession()
        self.saved += 1


@pytest.fixture(scope="module")
def verifier():
    return password_verifier(PASSWORD)


@pytest.fixture
def setup(verifier):
    now = [1000]
    service = Service()
    app = create_app(service, Config(), verifier, lambda: now[0])
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, service, now


def login(client):
    response = client.post("/login", json={"password": PASSWORD}, headers={"Origin": ORIGIN})
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"] and "SameSite=strict" in response.headers["set-cookie"]
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}


def test_authentication_status_and_expiry(setup):
    client, service, now = setup
    assert client.get("/status").status_code == 401
    headers = login(client)
    response = client.get("/status")
    assert response.status_code == 200
    assert "SYNTHETIC" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert set(response.json()) == {"session_status", "last_successful_poll", "contact_count", "approximate_cookie_expiry"}
    now[0] += 3601
    assert client.get("/status").status_code == 401


def test_valid_and_failed_replacement(setup):
    client, service, _ = setup
    headers = login(client)
    response = client.post("/cookies", files={"cookies": ("cookies.txt", COOKIE)}, headers=headers)
    assert response.status_code == 200
    assert service.saved == 1
    service.error = True
    response = client.post("/cookies", files={"cookies": ("cookies.txt", COOKIE)}, headers=headers)
    assert response.status_code == 400
    assert service.saved == 1
    assert "SYNTHETIC_SECRET" not in response.text


def test_csrf_host_origin_and_no_export(setup):
    client, service, _ = setup
    headers = login(client)
    for invalid in ({"Origin": ORIGIN}, {**headers, "Origin": "http://evil.test"},
                    {**headers, "Host": "evil.test"}, {"X-CSRF-Token": headers["X-CSRF-Token"]}):
        response = client.post("/cookies", files={"cookies": ("cookies.txt", COOKIE)}, headers=invalid)
        assert response.status_code in {400, 403}
    assert service.saved == 0
    assert client.get("/cookies").status_code == 405
    assert client.get("/status", headers={"Host": "evil.test"}).status_code == 400
    assert client.post("/proxy", json={"url": "https://evil.test"}).status_code == 404


def test_login_throttled_and_recovers(setup):
    client, _, now = setup
    for _ in range(5):
        assert client.post("/login", json={"password": "SYNTHETIC_WRONG"}, headers={"Origin": ORIGIN}).status_code == 401
    assert client.post("/login", json={"password": PASSWORD}, headers={"Origin": ORIGIN}).status_code == 429
    now[0] += 301
    login(client)


def test_chunked_oversized_and_false_content_length(setup):
    client, service, _ = setup
    headers = login(client)
    def chunks():
        for _ in range(17):
            yield b"x" * 65536
    for extra in ({}, {"Content-Length": "1"}, {"Content-Length": "-1"}):
        response = client.post("/cookies", content=chunks(), headers={**headers, **extra,
            "Content-Type": "multipart/form-data; boundary=synthetic"})
        assert response.status_code == 413
    assert service.saved == 0


def test_malformed_uploads_are_redacted(setup, caplog):
    client, service, _ = setup
    headers = login(client)
    for raw in (b"invalid SYNTHETIC_SECRET", COOKIE.replace(b".google.com\tTRUE", b"google.com\tTRUE")):
        response = client.post("/cookies", files={"cookies": ("cookies.txt", raw)}, headers=headers)
        assert response.status_code == 400
        assert "SYNTHETIC_SECRET" not in response.text
    response = client.post("/cookies", content=b"SYNTHETIC_SECRET", headers={**headers,
        "Content-Type": "multipart/form-data; boundary=synthetic"})
    assert response.status_code == 400
    assert "SYNTHETIC_SECRET" not in caplog.text


def test_restart_and_logout_invalidate_session(setup, verifier):
    client, _, _ = setup
    headers = login(client)
    cookie = client.cookies.get("collector_session")
    assert client.post("/logout", headers=headers).status_code == 200
    assert client.get("/status").status_code == 401
    app = create_app(Service(), Config(), verifier)
    with TestClient(app, base_url=ORIGIN) as fresh:
        fresh.cookies.set("collector_session", cookie)
        assert fresh.get("/status").status_code == 401


def test_salted_verifier_and_bad_password(setup, verifier):
    assert password_verifier(PASSWORD) != verifier
    assert PASSWORD not in json.dumps(verifier)
    client, _, _ = setup
    for body in ({}, [], {"password": "x" * 1025}, {"password": None}):
        assert client.post("/login", json=body, headers={"Origin": ORIGIN}).status_code == 401


def test_concurrent_login_bodies_cannot_bypass_throttle(verifier):
    import asyncio
    import httpx
    app = create_app(Service(), Config(), verifier)
    async def exercise():
        release = asyncio.Event()
        async def slow_body():
            await release.wait()
            yield b'{"password":"synthetic-wrong"}'
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client:
            tasks = [asyncio.create_task(client.post('/login', content=slow_body(),
                headers={'Origin': ORIGIN})) for _ in range(10)]
            await asyncio.sleep(0.05)
            release.set()
            results = await asyncio.gather(*tasks)
            assert sorted(r.status_code for r in results) == [401] * 5 + [429] * 5
    asyncio.run(exercise())


def test_asgi_stream_bound_stops_reading_after_limit(setup):
    import asyncio
    client, _, _ = setup
    headers = login(client)
    cookie = 'collector_session=' + client.cookies.get('collector_session')
    app = client.app
    reads = []
    responses = []
    async def receive():
        reads.append(1)
        return {'type': 'http.request', 'body': b'x' * 65536, 'more_body': True}
    async def send(message):
        responses.append(message)
    scope = {'type':'http','asgi':{'version':'3.0'},'http_version':'1.1',
        'method':'POST','scheme':'http','path':'/cookies','raw_path':b'/cookies',
        'query_string':b'','root_path':'','server':('127.0.0.1',8787),'client':('synthetic',1),
        'headers':[(b'host',b'127.0.0.1:8787'),(b'origin',ORIGIN.encode()),
            (b'cookie',cookie.encode()),(b'x-csrf-token',headers['X-CSRF-Token'].encode()),
            (b'content-type',b'multipart/form-data; boundary=synthetic')]}
    asyncio.run(app(scope,receive,send))
    assert responses[0]['status'] == 413
    assert len(reads) == 17
