from pathlib import Path
from io import BytesIO
import json
import pytest
import requests
from requests.adapters import BaseAdapter
from google_maps_collector.google_maps import (
    GoogleMaps, InvalidCookieFile, InvalidData, InvalidSession, NetworkFailure,
    UnexpectedRedirect, URL, parse_cookies, parse_response,
)

BODY = b")]}'\n" + (Path(__file__).parent / "fixtures/google_response.json").read_bytes()
COOKIE = b"# Netscape HTTP Cookie File\n.google.com\tTRUE\t/\tTRUE\t0\t__Secure-1PSID\tSYNTHETIC_SECRET\n"


class Adapter(BaseAdapter):
    def __init__(self, status=200, body=BODY, error=None):
        self.status, self.body, self.error = status, body, error
        self.calls = []

    def send(self, request, **kwargs):
        self.calls.append((request, kwargs))
        if self.error:
            raise self.error
        response = requests.Response()
        response.status_code = self.status
        response.url = request.url
        response.request = request
        response.raw = BytesIO(self.body)
        return response

    def close(self):
        pass


def client(adapter):
    session = requests.Session()
    session.mount("https://", adapter)
    return GoogleMaps(session)


def test_constructed_request(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://example.invalid")
    adapter = Adapter()
    api = client(adapter)
    people, jar = api.poll(parse_cookies(COOKIE))
    request, options = adapter.calls[0]
    assert request.url.startswith(URL + "?")
    assert "authuser=2" in request.url
    assert request.headers["Cookie"] == "__Secure-1PSID=SYNTHETIC_SECRET"
    assert options["verify"] is True
    assert options["proxies"] == {}
    assert options["timeout"] == (10, 60)
    assert api.session.trust_env is False
    assert people[0].id == "synthetic-person"
    assert (people[0].latitude, people[0].longitude) == (0.5, 0.25)
    assert people[0].source_timestamp == 1800000000
    assert people[0].battery == 73
    assert people[0].display_name == "SYNTHETIC_NAME"
    assert "SYNTHETIC" not in repr(people[0])


@pytest.mark.parametrize("status,error", [(302, UnexpectedRedirect), (307, UnexpectedRedirect),
    (401, InvalidSession), (403, InvalidSession), (429, NetworkFailure), (500, NetworkFailure)])
def test_http_errors_do_not_follow_or_leak(status, error):
    adapter = Adapter(status, b"SYNTHETIC_SECRET")
    with pytest.raises(error) as caught:
        client(adapter).poll(parse_cookies(COOKIE))
    assert len(adapter.calls) == 1
    assert "SYNTHETIC" not in str(caught.value)


def test_transport_errors_are_sanitized():
    with pytest.raises(NetworkFailure) as caught:
        client(Adapter(error=requests.ConnectionError("SYNTHETIC_SECRET"))).poll(parse_cookies(COOKIE))
    assert str(caught.value) == "NetworkFailure"
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("body", [b"SYNTHETIC_SECRET", b")]}'\n{}", b")]}'\n[]", b")]}'\n[null]",
    b")]}'\n[[[]],null,null,null,null,null,null]", b")]}'\n" + b"x" * 4_194_304], ids=["text", "object", "empty", "short", "bad-contact", "oversized"])
def test_malformed_body(body):
    with pytest.raises(InvalidData):
        client(Adapter(body=body)).poll(parse_cookies(COOKIE))


def test_invalid_session_and_no_data():
    with pytest.raises(InvalidSession):
        parse_response(b")]}'\n[null,null,null,null,null,null,\"GgA=\"]")
    assert parse_response(b")]}'\n[null,null,null,null,null,null,null]") == []


@pytest.mark.parametrize("domain", [b"evilgoogle.com", b"google.com.evil.test", b"accounts.google.com"])
def test_domains_are_filtered(domain):
    with pytest.raises(InvalidCookieFile):
        parse_cookies(COOKIE.replace(b".google.com", domain))


def test_cookie_attributes_and_unrelated_cookies():
    jar = parse_cookies(COOKIE + b".example.test\tTRUE\t/\tTRUE\t0\tother\tSYNTHETIC_OTHER\n")
    assert len(jar) == 1
    cookie = next(iter(jar))
    assert cookie.secure and cookie.path == "/" and cookie.domain == ".google.com"
    with pytest.raises(InvalidCookieFile):
        parse_cookies(b"invalid SYNTHETIC_SECRET")


def test_invalid_coordinates_and_duplicates():
    data = json.loads(BODY[5:])
    data[0][0][1][1][2] = float("nan")
    with pytest.raises(InvalidData):
        parse_response(b")]}'\n" + json.dumps(data).encode())


def test_optional_name_fallback_and_normalization():
    from google_maps_collector.google_maps import display_name
    assert display_name("  Synthetic\x00 Name ") == "Synthetic Name"
    assert len(display_name("x" * 1000)) == 128
    data = json.loads(BODY[5:])
    data[0][0][6] = ["synthetic-person"]
    people = parse_response(b")]}'\n" + json.dumps(data).encode())
    assert people[0].display_name == ""


def test_all_shared_fields_match_pinned_upstream():
    # Load the unchanged standalone upstream parser, without importing HA.
    import importlib.util
    import sys
    path = Path(__file__).resolve().parents[2] / "custom_components/google_maps/gm_loc_sharing.py"
    spec = importlib.util.spec_from_file_location("upstream_gm_reference", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    upstream = module.GMPerson.shared_from_data(json.loads(BODY[5:])[0][0])
    person = parse_response(BODY)[0]
    for our, original in {"id": "id", "latitude": "latitude", "longitude": "longitude",
        "gps_accuracy": "gps_accuracy", "source_timestamp": "last_seen", "battery": "battery_level",
        "display_name": "full_name", "nickname": "nickname", "picture_url": "picture_url",
        "address": "address", "country_code": "country_code", "battery_charging": "battery_charging"}.items():
        assert getattr(person, our) == getattr(upstream, original)


def test_account_holder_location_without_account_email():
    data = json.loads(BODY[5:])
    data.extend([None, None, data[0][0]])
    people = parse_response(b")]}'\n" + json.dumps(data).encode())
    assert len(people) == 2
    account = people[1]
    assert account.id == "google-maps-account" and account.display_name == "Account holder"
    assert account.latitude == people[0].latitude and account.address == "SYNTHETIC_ADDRESS"
    assert account.battery is None and account.battery_charging is None
    assert account.picture_url is None
    data[0] = None
    assert len(parse_response(b")]}'\n" + json.dumps(data).encode())) == 1


@pytest.mark.parametrize("url", ["http://lh3.googleusercontent.com/p", "https://example.invalid/p",
    "https://secret@lh3.googleusercontent.com/p", "https://google.com.evil.test/p", "https://google.com:bad/p"])
def test_picture_urls_cannot_expose_credentials_or_arbitrary_origins(url):
    from google_maps_collector.google_maps import picture_url
    assert picture_url(url) is None
