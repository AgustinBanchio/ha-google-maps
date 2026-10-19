from dataclasses import replace, asdict
from http.cookiejar import CookieJar
import json
import importlib
from pathlib import Path
import sys
import types
import pytest
from starlette.testclient import TestClient
from google_maps_collector.config import Config
from google_maps_collector.service import Service
from google_maps_collector.store import EncryptedStore
from google_maps_collector.web import create_app, password_verifier
from google_maps_collector.upstream import UpstreamSource, REVISION
from test_google_maps import Adapter, BODY, COOKIE, parse_cookies, client

TOKEN = "SYNTHETIC_DATA_ACCESS_KEY_000000000000000000000"
ORIGIN = "http://127.0.0.1:8787"


def native_module():
    # Load the production adapter without HA package initialization; full HA
    # runtime/entity tests run separately in tests/native/.
    name = "native_contract"
    package = types.ModuleType(name)
    package.__path__ = [str(Path(__file__).resolve().parents[2] / "custom_components/google_maps")]
    sys.modules[name] = package
    return importlib.import_module(name + ".collector_client")


@pytest.fixture
def api(tmp_path):
    (tmp_path / "key").write_bytes(b"k" * 32)
    (tmp_path / "data-token").write_text(TOKEN)
    config = Config(data_token_file=tmp_path / "data-token")
    google = client(Adapter())
    service = Service(config, EncryptedStore(tmp_path / "session.json", tmp_path / "key"), google,
        lambda: 1800000001)
    service.import_cookies(parse_cookies(COOKIE))
    with TestClient(create_app(service, config, password_verifier("synthetic-admin-password")), base_url=ORIGIN) as browser:
        yield browser, service, google


def test_scoped_data_access_never_grants_management(api):
    browser, service, google = api
    assert browser.get("/v1/locations").status_code == 401
    headers = {"Authorization": "Bearer " + TOKEN}
    response = browser.get("/v1/locations", headers=headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["upstream_revision"] == REVISION
    assert data["people"][0]["full_name"] == "SYNTHETIC_NAME"
    assert "SYNTHETIC_SECRET" not in response.text and TOKEN not in response.text
    assert not response.cookies
    for path in ("/status", "/session"):
        assert browser.get(path, headers=headers).status_code == 401
    assert browser.post("/cookies", headers=headers).status_code in {401,403}
    assert browser.post("/logout", headers=headers).status_code in {401,403}
    assert browser.get("/v1/locations?url=https://example.invalid", headers=headers).status_code == 400
    assert browser.post("/v1/locations", headers=headers).status_code == 405


def test_native_api_bypasses_legacy_filter_and_preserves_full_names(api):
    browser, service, google = api
    raw = json.loads(BODY[5:])
    raw[0][0][1][1][2] = 1.25
    raw[0][0][1][2] -= 1000
    raw[0][0][1][3] = 9999
    raw[0][0][6][2] = "Synthetic " + "Name" * 100
    google.session.mount("https://", Adapter(body=b")]}'\n" + json.dumps(raw).encode()))
    response = browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 200
    record = response.json()["people"][0]
    assert record["latitude"] == 1.25 and record["gps_accuracy"] == 9999
    assert record["last_seen"] == 1799999999
    assert len(record["full_name"]) > 128
    assert service.people["synthetic-person"].latitude == 0.5
    assert "SYNTHETIC_SECRET" not in response.text


def test_api_auth_failure_is_fixed_and_keeps_store(api):
    browser, service, google = api
    before = service.store.path.read_bytes()
    google.session.mount("https://", Adapter(status=403, body=b"SYNTHETIC_SECRET"))
    response = browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 409 and response.json() == {"error":"google_session_required"}
    assert service.store.path.read_bytes() == before


def test_native_wire_roundtrip_and_account_semantics(api):
    browser, service, google = api
    raw = json.loads(BODY[5:]); raw[0][0][1][2] += 1
    raw.extend([None, None, raw[0][0]])
    google.session.mount("https://", Adapter(body=b")]}'\n" + json.dumps(raw).encode()))
    data = browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).json()
    module = native_module()
    session = __import__("requests").Session()
    adapter = Adapter(body=json.dumps(data).encode());session.mount("http://", adapter)
    source = module.CollectorClient(ORIGIN, TOKEN, "synthetic-owner@example.invalid", session)
    source.get_new_data()
    records = source.get_people(True)
    assert records[0].last_seen == 1800000000.001
    assert records[1].id == records[1].full_name == records[1].nickname == "synthetic-owner@example.invalid"
    assert len(source.get_people(False)) == 1
    assert len(adapter.calls) == 1
    request, options = adapter.calls[0]
    assert request.headers["Authorization"] == "Bearer " + TOKEN
    assert "Cookie" not in request.headers and options["proxies"] == {}


@pytest.mark.parametrize("endpoint", ["https://www.google.com", "http://evil.test:8787", "http://127.0.0.1:8787/x", "http://secret@localhost:8787", "http://localhost:8787?token=x"])
def test_native_adapter_cannot_be_an_arbitrary_proxy(endpoint):
    with pytest.raises(ValueError): native_module().CollectorClient(endpoint, TOKEN, "synthetic@example.invalid")


def test_upstream_malformed_contact_skip_and_sanitized_errors(caplog):
    raw = json.loads(BODY[5:]);raw[0].append([])
    source = client(Adapter(body=b")]}'\n" + json.dumps(raw).encode()))
    observations, _ = source.poll_upstream(parse_cookies(COOKIE))
    assert len(observations.people) == 1
    from google_maps_collector.google_maps import InvalidData
    with pytest.raises(InvalidData) as error:
        client(Adapter(body=b"SYNTHETIC_SECRET SYNTHETIC_NAME")).poll_upstream(parse_cookies(COOKIE))
    assert str(error.value) == "InvalidData"
    assert "SYNTHETIC" not in caplog.text
