"""Hardened client derived from upstream b2132123 (see UPSTREAM_PROVENANCE)."""

from dataclasses import dataclass
from http.cookiejar import Cookie, CookieJar
import copy
import json
import math
import time
from urllib.parse import urlsplit

URL = "https://www.google.com/maps/rpc/locationsharing/read"
AUTH_NAMES = {"__Secure-1PSID", "__Secure-3PSID"}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class GoogleError(Exception):
    """A fixed public code, never a response, URL or transport exception."""

    def __init__(self, reason=None, http_status=None):
        from .diagnostics import Reason
        self.reason = reason if isinstance(reason, Reason) else None
        self.http_status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None
        super().__init__(self.__class__.__name__)


class InvalidSession(GoogleError):
    pass


class InvalidData(GoogleError):
    pass


class NetworkFailure(GoogleError):
    pass


class UnexpectedRedirect(InvalidSession):
    pass


class InvalidCookieFile(GoogleError):
    pass


@dataclass(frozen=True, repr=False)
class Person:
    id: str
    latitude: float
    longitude: float
    gps_accuracy: float
    source_timestamp: float
    battery: int | None = None
    display_name: str = ""
    nickname: str = ""
    picture_url: str | None = None
    address: str = ""
    country_code: str = ""
    battery_charging: bool | None = None


def filter_cookies(jar: CookieJar) -> CookieJar:
    result = CookieJar()
    for cookie in jar:
        if (cookie.domain in {".google.com", "google.com", "www.google.com", ".www.google.com"}
                and cookie.secure and cookie.path.startswith("/")
                and cookie.name and cookie.value is not None):
            result.set_cookie(copy.copy(cookie))
    return result


def parse_cookies(data: bytes) -> CookieJar:
    if len(data) > 1_048_576:
        raise InvalidCookieFile()
    jar = CookieJar()
    try:
        lines = data.decode("utf-8").splitlines()
        if not lines or lines[0] not in {"# Netscape HTTP Cookie File", "# HTTP Cookie File"}:
            raise ValueError()
        for line in lines[1:]:
            httponly = line.startswith("#HttpOnly_")
            if httponly:
                line = line[10:]
            if not line.strip() or line.startswith(("#", "$")):
                continue
            domain, domain_flag, path, secure, expiry, name, value = line.split("\t")
            if (domain_flag not in {"TRUE", "FALSE"} or secure not in {"TRUE", "FALSE"}
                    or (domain_flag == "TRUE") != domain.startswith(".")
                    or not name or any(ord(char) < 33 or ord(char) > 126 for char in name + value)
                    or any(char in name for char in '()<>@,;:\\"/[]?={}')):
                raise ValueError()
            expires = int(expiry) if expiry else 0
            if expires < 0:
                raise ValueError()
            if expires and expires <= time.time():
                continue
            jar.set_cookie(Cookie(0, name, value, None, False, domain,
                domain_flag == "TRUE", domain.startswith("."), path, True,
                secure == "TRUE", expires or None, not expires, None, None,
                {"HTTPOnly": None} if httponly else {}))
    except (ValueError, UnicodeError):
        raise InvalidCookieFile() from None
    result = filter_cookies(jar)
    if not any(cookie.name in AUTH_NAMES for cookie in result):
        raise InvalidCookieFile()
    return result


def _number(value, low, high):
    if (type(value) not in {int, float} or not math.isfinite(value)
            or not low <= value <= high):
        raise InvalidData()
    return value


def display_name(value) -> str:
    """A bounded human label; never an identity or a log field."""
    if not isinstance(value, str):
        return ""
    return " ".join("".join(c for c in value if c.isprintable()).split())[:128]


def picture_url(value) -> str | None:
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        if (url.scheme == "https" and not url.username and not url.password
                and url.port in {None, 443}
                and any(host == domain or host.endswith("." + domain)
                        for domain in ("googleusercontent.com", "ggpht.com", "google.com"))):
            return value
    except ValueError:
        pass
    return None


def _legacy_people(observations, include_account=True):
    records = list(observations.people)
    if include_account and observations.account:
        records.append(observations.account)
    return [Person("google-maps-account" if p.id == "__collector_account__" else p.id,
        p.latitude, p.longitude, p.gps_accuracy, p.last_seen, p.battery_level,
        "Account holder" if p.id == "__collector_account__" else display_name(p.full_name),
        display_name(p.nickname), picture_url(p.picture_url), display_name(p.address),
        display_name(p.country_code), p.battery_charging) for p in records]


def parse_response(body: bytes, include_account=True) -> list[Person]:
    # Tests/legacy adapter use the upstream client through an in-memory transport.
    from .upstream import UpstreamSource
    class Response:
        status_code = 200
        def iter_content(self, size): yield body
        def close(self): pass
    class MemorySession:
        cookies = CookieJar()
        def get(self, *args, **kwargs): return Response()
        def close(self): pass
    source = UpstreamSource(MemorySession())
    observations, _ = source.poll(CookieJar())
    return _legacy_people(observations, include_account)


class GoogleMaps:
    def __init__(self, session=None, *, include_account=True):
        from .upstream import UpstreamSource
        self.include_account = include_account
        self.source = UpstreamSource(session)
        self.session = self.source.session

    def close(self):
        self.source.close()

    def poll_upstream(self, cookies):
        return self.source.poll(cookies)

    def poll(self, cookies):
        observations, rotated = self.poll_upstream(cookies)
        return _legacy_people(observations, self.include_account), rotated
