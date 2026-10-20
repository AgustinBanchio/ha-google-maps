from email.message import Message
import json
from types import SimpleNamespace

import pytest
import requests

from google_maps_collector.diagnostics import (
    Diagnostics, LIMIT, LOGGER, MAX_BYTES, Reason, configure_logging,
)
from google_maps_collector.google_maps import InvalidSession, InvalidData, NetworkFailure
from google_maps_collector.service import Service
from google_maps_collector.store import StoreError
from test_google_maps import Adapter, BODY, COOKIE, client, parse_cookies
from test_native_api import api, TOKEN


@pytest.fixture(autouse=True)
def event_logging(capsys):
    handlers, level, propagate = LOGGER.handlers, LOGGER.level, LOGGER.propagate
    configure_logging()
    yield
    LOGGER.handlers, LOGGER.level, LOGGER.propagate = handlers, level, propagate


@pytest.mark.parametrize("adapter,reason,status", [
    (Adapter(body=b")]}'\n[null,null,null,null,null,null,\"GgA=\"]"), Reason.INVALID_SESSION, 200),
    (Adapter(status=401), Reason.HTTP_AUTH, 401),
    (Adapter(status=403), Reason.HTTP_AUTH, 403),
    (Adapter(status=302), Reason.REDIRECT, 302),
    (Adapter(status=500), Reason.HTTP_ERROR, 500),
    (Adapter(error=requests.exceptions.SSLError("SYNTHETIC_SECRET")), Reason.TLS, None),
    (Adapter(error=requests.Timeout("SYNTHETIC_SECRET")), Reason.TIMEOUT, None),
    (Adapter(error=requests.ConnectionError("SYNTHETIC_SECRET")), Reason.CONNECTION, None),
    (Adapter(error=requests.exceptions.RetryError("SYNTHETIC_SECRET")), Reason.RETRIES, None),
    (Adapter(body=b"SYNTHETIC_SECRET SYNTHETIC_PRIVATE_LOCATION"), Reason.DATA, 200),
    (Adapter(body=b"\xff"), Reason.ENCODING, 200),
    (Adapter(body=b"x" * 4_194_305), Reason.TOO_LARGE, 200),
])
def test_failure_reason_is_safe_and_distinct(api, adapter, reason, status, capsys):
    browser, service, google = api
    google.session.mount("https://", adapter)
    response = browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code in {409, 502, 503}
    snapshot = service.management_status()["diagnostics"]
    failure = snapshot["last_source_failure"]
    assert failure["reason"] == reason and failure["http_status"] == status
    assert failure["operation"] == "native_poll"
    assert "diagnostics" not in response.json()  # Native wire contract unchanged.
    lines = capsys.readouterr().err
    output = lines + json.dumps(snapshot) + service.diagnostics.path.read_text()
    for forbidden in ("SYNTHETIC_SECRET", "SYNTHETIC_PRIVATE_LOCATION", "SYNTHETIC_NAME", TOKEN,
            "Cookie", "__Secure-1PSID", "https://", "Traceback"):
        assert forbidden not in output
    assert lines
    for line in lines.splitlines():
        assert json.loads(line)["event"] == "collector_operation"


class RotatingAdapter(Adapter):
    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        headers = Message()
        headers.add_header("Set-Cookie", "__Secure-1PSID=SYNTHETIC_ROTATED; Domain=.google.com; Path=/; Secure; Expires=Wed, 18 May 2033 03:33:20 GMT")
        headers.add_header("Set-Cookie", "__Secure-1PSIDCC=SYNTHETIC_REFRESH; Domain=.google.com; Path=/; Secure")
        response.raw._original_response = SimpleNamespace(msg=headers)
        return response


def test_actual_requests_rotation_persisted_and_reported_without_values(api, capsys):
    browser, service, google = api
    google.session.mount("https://", RotatingAdapter())
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
    diag = service.management_status()["diagnostics"]
    assert diag["last_success"]["cookie_changes"] == {"added": 1, "changed": 1, "removed": 0}
    restored = Service(service.config, service.store, google, service.clock)
    assert {c.name: c.value for c in restored.cookies}["__Secure-1PSID"] == "SYNTHETIC_ROTATED"
    assert restored.diagnostics.snapshot()["last_success"] == diag["last_success"]
    assert b"SYNTHETIC_ROTATED" not in service.store.path.read_bytes()
    output = capsys.readouterr().err + service.diagnostics.path.read_text()
    assert all(secret not in output for secret in ("SYNTHETIC_ROTATED", "SYNTHETIC_REFRESH", "__Secure-1PSID"))


def test_last_source_failure_survives_recovery_access_denial_and_restart(api):
    browser, service, google = api
    google.session.mount("https://", Adapter(status=403))
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).status_code == 409
    failure = service.diagnostics.snapshot()["last_source_failure"]
    google.session.mount("https://", Adapter())
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer SYNTHETIC_WRONG_KEY"}).status_code == 401
    restored = Service(service.config, service.store, google, service.clock)
    diag = restored.diagnostics.snapshot()
    assert diag["last_source_failure"] == failure
    assert diag["last_success"]["operation"] == "native_poll"
    assert diag["last_failure"]["reason"] == Reason.DATA_KEY


def test_failed_import_retains_working_session_but_records_reason(api):
    _, service, google = api
    before = service.store.path.read_bytes()
    google.session.mount("https://", Adapter(status=403))
    with pytest.raises(InvalidSession):
        service.import_cookies(parse_cookies(COOKIE))
    assert service.status == "ready" and service.store.path.read_bytes() == before
    assert service.diagnostics.snapshot()["last_source_failure"]["operation"] == "session_import"


def test_real_store_failure_is_separate_from_google_rejection(api, monkeypatch):
    browser, service, _ = api
    def fail(_): raise StoreError()
    monkeypatch.setattr(service.store, "save", fail)
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).status_code == 503
    assert service.diagnostics.snapshot()["last_source_failure"]["reason"] == Reason.STORAGE


def test_optional_history_write_failure_does_not_break_tracking(api, monkeypatch, capsys):
    browser, service, _ = api
    def fail(*_): raise OSError("SYNTHETIC_SECRET PRIVATE_HOST_PATH")
    monkeypatch.setattr("google_maps_collector.diagnostics.atomic_write", fail)
    assert browser.get("/v1/locations", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
    assert not service.diagnostics.snapshot()["persistence_available"]
    assert "SYNTHETIC" not in capsys.readouterr().err


def test_history_is_bounded_deduplicated_and_defensive(tmp_path):
    now = [1800000000]
    diag = Diagnostics(tmp_path / "diagnostics.json", lambda: now[0])
    for _ in range(100): diag.record("native_poll", error=InvalidSession())
    assert len(diag.snapshot()["events"]) == 1
    for i in range(100):
        now[0] += 1
        diag.record("native_poll", error=InvalidData() if i % 2 else NetworkFailure())
    assert len(diag.snapshot()["events"]) == LIMIT
    assert diag.path.stat().st_size < MAX_BYTES
    snapshot = diag.snapshot();snapshot["events"].clear()
    assert len(diag.snapshot()["events"]) == LIMIT


@pytest.mark.parametrize("bad", [b"SYNTHETIC_SECRET", b"x" * (MAX_BYTES+1)], ids=["invalid-json", "oversized"])
def test_corrupt_or_oversized_history_not_exposed(tmp_path, bad, capsys):
    path = tmp_path / "diagnostics.json";path.write_bytes(bad)
    diag = Diagnostics(path)
    assert diag.snapshot()["history_reset"] and not diag.snapshot()["events"]
    diag.record("native_poll")
    assert "SYNTHETIC_SECRET" not in path.read_text() + capsys.readouterr().err


def test_untrusted_history_fields_and_error_metadata_rejected(tmp_path, capsys):
    path = tmp_path / "diagnostics.json";diag = Diagnostics(path);diag.record("native_poll")
    data = json.loads(path.read_text());data["events"][0]["reason"] = "SYNTHETIC_SECRET"
    path.write_text(json.dumps(data));diag = Diagnostics(path)
    assert diag.snapshot()["history_reset"]
    error = InvalidSession();error.reason = "SYNTHETIC_SECRET";error.http_status = "SYNTHETIC_SECRET"
    diag.record("native_poll", error=error)
    assert diag.snapshot()["last_failure"]["reason"] == Reason.SESSION
    assert "SYNTHETIC_SECRET" not in path.read_text() + capsys.readouterr().err


def test_broken_log_stream_does_not_dump_exception_context(tmp_path, monkeypatch):
    class BrokenStream:
        def write(self, _): raise OSError("SYNTHETIC_SECRET")
    diag = Diagnostics(tmp_path / "diagnostics.json")
    with monkeypatch.context() as patch:
        patch.setattr("sys.stderr", BrokenStream())
        try:
            raise RuntimeError("SYNTHETIC_PRIVATE_LOCATION")
        except RuntimeError:
            diag.record("native_poll", error=InvalidSession(Reason.INVALID_SESSION, 200))
    assert diag.snapshot()["last_failure"]["reason"] == Reason.INVALID_SESSION
    assert "SYNTHETIC" not in diag.path.read_text()


def test_metadata_cli_needs_no_google_or_management_credentials(tmp_path, monkeypatch, capsys):
    import sys
    from google_maps_collector.__main__ import main
    monkeypatch.setenv("STORE_FILE", str(tmp_path / "session.json"))
    monkeypatch.setattr(sys, "argv", ["collector", "--diagnostics"])
    (tmp_path / "session.json").write_bytes(b"SYNTHETIC_CREDENTIAL_FILE_MUST_NOT_BE_READ")
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["schema"] == 1 and output["last_failure"] is None
    assert not output["events"] and not output["history_reset"]


def test_management_diagnostics_requires_management_login_not_data_key(api):
    browser, _, _ = api
    assert browser.get("/status", headers={"Authorization": "Bearer " + TOKEN}).status_code == 401
    assert browser.post("/login", json={"password": "synthetic-admin-password"},
        headers={"Origin": "http://127.0.0.1:8787"}).status_code == 200
    data = browser.get("/status").json()
    assert data["diagnostics"]["last_success"]["operation"] == "session_import"
    assert "SYNTHETIC" not in json.dumps(data["diagnostics"])
