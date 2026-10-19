"""Hardened client derived from upstream b2132123 (see UPSTREAM_PROVENANCE)."""

from dataclasses import dataclass
from http.cookiejar import Cookie, CookieJar
import copy
import json
import math
import time
from urllib.parse import urlsplit

import requests

URL = "https://www.google.com/maps/rpc/locationsharing/read"
PARAMS = {
    "authuser": 2, "hl": "en", "gl": "us",
    "pb": (
        "!1m7!8m6!1m3!1i14!2i8413!3i5385!2i6!3x4095"
        "!2m3!1e0!2sm!3i407105169!3m7!2sen!5e1105!12m4"
        "!1e68!2m2!1sset!2sRoadmap!4e1!5m4!1e4!8m2!1e0!"
        "1e1!6m9!1e12!2i2!26m1!4b1!30m1!"
        "1f1.3953487873077393!39b1!44e1!50e0!23i4111425"
    ),
}
AUTH_NAMES = {"__Secure-1PSID", "__Secure-3PSID"}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class GoogleError(Exception):
    """A fixed public code, never a response, URL or transport exception."""

    def __init__(self):
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


def parse_response(body: bytes) -> list[Person]:
    try:
        if not body.startswith(b")]}'\n"):
            raise InvalidData()
        data = json.loads(body[5:])
        if not isinstance(data, list) or len(data) < 7:
            raise InvalidData()
        if data[6] == "GgA=":
            raise InvalidSession()
        if data[0] is None:
            data[0] = []
        if not isinstance(data[0], list):
            raise InvalidData()
        people = []
        seen = set()
        entries = [(entry, False) for entry in data[0]]
        # Upstream's optional account-holder location has no profile metadata.
        # A local stable ID avoids requiring or publishing the account email.
        if len(data) > 9 and data[9] is not None:
            entries.append((data[9], True))
        for entry, account in entries:
            # Upstream shared_from_data/acct_from_data indices.
            if not isinstance(entry, list) or len(entry) < (2 if account else 7):
                raise InvalidData()
            if entry[1] is None:  # A shared contact with no fix is not a parser failure.
                continue
            profile = ["google-maps-account", None, "Account holder", "Account holder"] if account else entry[6]
            identity = profile[0]
            if not isinstance(identity, str) or not identity or len(identity) > 512 or identity in seen:
                raise InvalidData()
            seen.add(identity)
            battery = None
            if not account and len(entry) > 13 and isinstance(entry[13], list) and len(entry[13]) > 1:
                battery = entry[13][1]
                if type(battery) is not int or not 0 <= battery <= 100:
                    battery = None
            people.append(Person(
                identity, _number(entry[1][1][2], -90, 90),
                _number(entry[1][1][1], -180, 180),
                _number(entry[1][3], 0, 1_000_000),
                _number(entry[1][2], 0, 100_000_000_000_000) / 1000, battery,
                display_name(profile[2]) if len(profile) > 2 else "",
                display_name(profile[3]) if len(profile) > 3 else "",
                picture_url(profile[1]) if len(profile) > 1 else None,
                display_name(entry[1][4]) if len(entry[1]) > 4 else "",
                display_name(entry[1][6]) if len(entry[1]) > 6 else "",
                bool(entry[13][0]) if not account and len(entry) > 13
                    and isinstance(entry[13], list) and entry[13] else None,
            ))
        return people
    except (ValueError, TypeError, IndexError, KeyError, RecursionError):
        raise InvalidData() from None


class GoogleMaps:
    def __init__(self, session=None):
        self.session = session if session is not None else requests.Session()
        self.session.trust_env = False  # Ignore proxy, netrc and CA environment overrides.

    def close(self):
        self.session.close()

    def poll(self, cookies: CookieJar) -> tuple[list[Person], CookieJar]:
        # This URL is fixed and independently checked; no caller-supplied endpoint.
        parsed = urlsplit(URL)
        if (parsed.scheme, parsed.netloc, parsed.path) != (
            "https", "www.google.com", "/maps/rpc/locationsharing/read"
        ) or parsed.query or parsed.fragment:
            raise NetworkFailure()
        self.session.cookies = filter_cookies(cookies)
        response = None
        try:
            response = self.session.get(URL, params=PARAMS, timeout=(10, 60),
                                        verify=True, allow_redirects=False, stream=True)
            if 300 <= response.status_code < 400:
                raise UnexpectedRedirect()
            if response.status_code in {401, 403}:
                raise InvalidSession()
            if response.status_code != 200:
                raise NetworkFailure()
            body = bytearray()
            for chunk in response.iter_content(65536):
                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise InvalidData()
                body.extend(chunk)
            people = parse_response(bytes(body))
            return people, filter_cookies(self.session.cookies)
        except requests.RequestException:
            raise NetworkFailure() from None
        finally:
            if response is not None:
                response.close()
