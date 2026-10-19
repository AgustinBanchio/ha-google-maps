from dataclasses import replace
from threading import Event, Thread
import pytest
from google_maps_collector.config import Config
from google_maps_collector.google_maps import InvalidSession, InvalidData, NetworkFailure, Person, parse_cookies
from google_maps_collector.service import Service
from google_maps_collector.store import EncryptedStore, StoreError
from test_google_maps import COOKIE


class Google:
    def __init__(self):
        self.people = [Person("synthetic", 0.5, 0.25, 25, 1800000000, 73)]
        self.error = None

    def poll(self, jar):
        if self.error:
            raise self.error()
        return self.people, jar


@pytest.fixture
def setup(tmp_path):
    (tmp_path / "key").write_bytes(b"k" * 32)
    store = EncryptedStore(tmp_path / "session.json", tmp_path / "key")
    google = Google()
    now = [1800000001]
    service = Service(Config(), store, google, lambda: now[0])
    return service, google, now


def test_timestamp_freshness_and_restart(setup):
    service, google, now = setup
    service.import_cookies(parse_cookies(COOKIE))
    original = service.people["synthetic"]
    google.people = [replace(original, latitude=0.75, battery=50)]
    service.poll()
    assert service.people["synthetic"].latitude == 0.5
    assert service.people["synthetic"].battery == 50
    google.people = [replace(original, source_timestamp=original.source_timestamp - 1)]
    service.poll()
    assert service.people["synthetic"].source_timestamp == original.source_timestamp
    rebuilt = Service(service.config, service.store, google, lambda: now[0])
    assert rebuilt.people == service.people
    assert rebuilt.status == "starting"
    rebuilt.poll()
    assert rebuilt.snapshot()["available"] == {"synthetic"}
    now[0] += 900
    assert rebuilt.snapshot()["available"] == set()


def test_invalid_import_preserves_session_and_store(setup):
    service, google, _ = setup
    service.import_cookies(parse_cookies(COOKIE))
    before = service.store.path.read_bytes()
    google.error = InvalidSession
    with pytest.raises(InvalidSession):
        service.import_cookies(parse_cookies(COOKIE.replace(b"SYNTHETIC_SECRET", b"SYNTHETIC_BAD")))
    assert service.status == "ready"
    assert service.store.path.read_bytes() == before
    assert next(iter(service.cookies)).value == "SYNTHETIC_SECRET"


@pytest.mark.parametrize("error,status", [(InvalidSession, "credential_required"),
    (NetworkFailure, "network_failure"), (InvalidData, "parser_failure"), (StoreError, "storage_error")])
def test_failure_and_recovery(setup, error, status):
    service, google, _ = setup
    service.import_cookies(parse_cookies(COOKIE))
    before = service.store.path.read_bytes()
    google.error = error
    service.poll()
    assert service.status == status
    assert service.retry_seconds == 120
    assert service.store.path.read_bytes() == before
    assert len(service.cookies) == 1
    google.error = None
    service.poll()
    assert service.status == "ready" and service.retry_seconds == 60


def test_no_data_and_future_fix(setup):
    service, google, now = setup
    service.poll()
    assert service.status == "credential_required"
    google.people = []
    service.import_cookies(parse_cookies(COOKIE))
    assert service.status == "no_data"
    google.people = [Person("future", 0, 0, 1, now[0] + 61)]
    service.poll()
    assert service.status == "parser_failure"


def test_cookie_rotation_saved(setup):
    service, google, _ = setup
    def rotate(jar):
        return google.people, parse_cookies(COOKIE.replace(b"SYNTHETIC_SECRET", b"SYNTHETIC_ROTATED"))
    google.poll = rotate
    service.import_cookies(parse_cookies(COOKIE))
    rebuilt = Service(service.config, service.store, google)
    assert next(iter(rebuilt.cookies)).value == "SYNTHETIC_ROTATED"


def test_import_waits_for_poll(setup):
    service, google, _ = setup
    service.import_cookies(parse_cookies(COOKIE))
    entered, release, imported = Event(), Event(), Event()
    def blocked(jar):
        entered.set()
        assert release.wait(5)
        return google.people, jar
    google.poll = blocked
    polling = Thread(target=service.poll)
    def importing():
        service.import_cookies(parse_cookies(COOKIE))
        imported.set()
    polling.start()
    assert entered.wait(5)
    importer = Thread(target=importing)
    importer.start()
    assert not imported.wait(0.05)
    release.set()
    polling.join(5)
    importer.join(5)
    assert imported.is_set() and not polling.is_alive()


def test_management_has_only_permitted_fields(setup):
    service, _, _ = setup
    service.import_cookies(parse_cookies(COOKIE))
    assert set(service.management_status()) == {"session_status", "last_successful_poll",
        "contact_count", "approximate_cookie_expiry"}
    assert "SYNTHETIC_SECRET" not in str(service.management_status())


def test_staleness_is_not_blocked_by_network_poll(setup):
    service, google, now = setup
    service.import_cookies(parse_cookies(COOKIE))
    entered, release, finished = Event(), Event(), Event()
    def blocked(jar):
        entered.set()
        assert release.wait(5)
        return google.people, jar
    google.poll = blocked
    poller = Thread(target=service.poll)
    poller.start()
    assert entered.wait(5)
    now[0] += 901
    def read_view():
        assert not service.snapshot()["available"]
        assert service.management_status()["session_status"] == "ready"
        finished.set()
    reader = Thread(target=read_view)
    reader.start()
    try:
        assert finished.wait(1)
    finally:
        release.set()
        poller.join(5)
        reader.join(5)


def test_invalid_session_remains_required_after_network_failure(setup):
    service, google, _ = setup
    service.import_cookies(parse_cookies(COOKIE))
    google.error = InvalidSession
    service.poll()
    google.error = NetworkFailure
    service.poll()
    assert service.status == "credential_required"
    assert not service.snapshot()["session_valid"]
    assert not service.snapshot()["available"]


def test_restart_network_failure_does_not_validate_stored_session(setup):
    service, google, now = setup
    service.import_cookies(parse_cookies(COOKIE))
    rebuilt = Service(service.config, service.store, google, lambda: now[0])
    google.error = NetworkFailure
    rebuilt.poll()
    assert rebuilt.status == "network_failure"
    assert not rebuilt.snapshot()["session_valid"]
    assert not rebuilt.snapshot()["available"]
