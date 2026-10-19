"""One lock owns polling, candidate validation, store commit and snapshots."""

from dataclasses import asdict, replace
from datetime import datetime, UTC
from http.cookiejar import Cookie, CookieJar
import time

from .config import Config
from .google_maps import (
    AUTH_NAMES, GoogleMaps, GoogleError, InvalidData, InvalidSession,
    NetworkFailure, Person, filter_cookies,
)
from .store import EncryptedStore, StoreError

COOKIE_FIELDS = ("version", "name", "value", "port", "port_specified", "domain",
    "domain_specified", "domain_initial_dot", "path", "path_specified", "secure",
    "expires", "discard", "comment", "comment_url")


class Service:
    def __init__(self, config: Config, store: EncryptedStore, google: GoogleMaps, clock=time.time):
        self.config, self.store, self.google, self.clock = config, store, google, clock
        self.lock = store.lock
        self.cookies = CookieJar()
        self.people: dict[str, Person] = {}
        self.present: set[str] = set()
        self.missing_since: dict[str, float] = {}
        self.last_success = None
        self.status = "credential_required"
        self.failures = 0
        self.session_valid = False
        self.credential_required = True
        data = store.load()  # Corruption fails startup; never overwrite unreadable state.
        if data is not None:
            try:
                if data["schema"] != 1:
                    raise StoreError()
                jar = CookieJar()
                for item in data["cookies"]:
                    jar.set_cookie(Cookie(**item))
                self.cookies = filter_cookies(jar)
                for item in data["people"]:
                    person = Person(**item)
                    # Validate stored model through the same numeric constraints.
                    from .google_maps import _number
                    _number(person.latitude, -90, 90)
                    _number(person.longitude, -180, 180)
                    _number(person.gps_accuracy, 0, 1_000_000)
                    _number(person.source_timestamp, 0, 100_000_000_000)
                    if not isinstance(person.id, str) or not person.id:
                        raise StoreError()
                    self.people[person.id] = person
                self.present = set(data["present"])
                self.missing_since = dict(data.get("missing_since", {}))
                for identity in self.people.keys() - self.present:
                    self.missing_since.setdefault(identity, self.clock())
                for missing_at in self.missing_since.values():
                    _number(missing_at, 0, 100_000_000_000)
                self.last_success = data["last_success"]
                if any(c.name in AUTH_NAMES for c in self.cookies):
                    self.status = "starting"
                    self.credential_required = False
            except (KeyError, TypeError, ValueError, GoogleError):
                raise StoreError() from None
        self._refresh_view()

    def _document(self, cookies, people, present, now, missing_since=None):
        return {"schema": 1,
            "cookies": [{**{name: getattr(c, name) for name in COOKIE_FIELDS},
                         "rest": dict(c._rest)} for c in cookies],
            "people": [asdict(p) for p in people.values()],
            "present": sorted(present), "last_success": now,
            "missing_since": self.missing_since if missing_since is None else missing_since}

    def _validate_and_save(self, candidate):
        incoming, rotated = self.google.poll(candidate)
        now = self.clock()
        updated = dict(self.people)
        present = set()
        for person in incoming:
            if person.source_timestamp > now + 60:
                raise InvalidData()
            present.add(person.id)
            previous = updated.get(person.id)
            newer = previous is None or person.source_timestamp > previous.source_timestamp
            accurate = previous is None or not previous.gps_accuracy or (
                person.gps_accuracy <= self.config.max_gps_accuracy
                if previous.gps_accuracy <= self.config.max_gps_accuracy
                else person.gps_accuracy <= previous.gps_accuracy)
            if newer and accurate:
                updated[person.id] = person
            else:
                # Battery data may change without a newer source observation.
                updated[person.id] = replace(previous, battery=person.battery,
                    display_name=person.display_name, nickname=person.nickname,
                    picture_url=person.picture_url, battery_charging=person.battery_charging,
                    address=person.address if person.source_timestamp == previous.source_timestamp else previous.address,
                    country_code=person.country_code if person.source_timestamp == previous.source_timestamp else previous.country_code)
        missing = {identity: self.missing_since.get(identity, now)
                   for identity in updated.keys() - present}
        self.store.save(self._document(rotated, updated, present, now, missing))
        self.cookies, self.people, self.present = rotated, updated, present
        self.missing_since = missing
        self.last_success = now
        self.status = "ready" if incoming else "no_data"
        self.session_valid = True
        self.credential_required = False
        self.failures = 0
        self._refresh_view()

    def upstream_observations(self):
        """One cookie owner; native HA receives upstream records BEFORE HA policy."""
        from dataclasses import asdict
        from .upstream import REVISION
        with self.lock:
            if not len(self.cookies):
                raise InvalidSession()
            try:
                observations, rotated = self.google.poll_upstream(self.cookies)
                now = self.clock()
                # Persist rotation without running the legacy MQTT location policy.
                self.store.save(self._document(rotated, self.people, self.present, now))
                self.cookies = rotated
                self.last_success = now
                self.status = "ready" if observations.people or observations.account else "no_data"
                self.session_valid = True
                self.credential_required = False
                self.failures = 0
                self._refresh_view()
                self._management = {**self._management,
                    "contact_count": len(observations.people) + int(observations.account is not None)}
                return {"schema": 1, "upstream_revision": REVISION,
                    "people": [asdict(person) for person in observations.people],
                    "account": asdict(observations.account) if observations.account else None,
                    "cookie_expiration": observations.expiration.isoformat() if observations.expiration else None}
            except InvalidSession:
                self.session_valid = False
                self.credential_required = True
                self.status = "credential_required"
                self._refresh_view()
                raise
            except (NetworkFailure, InvalidData, StoreError) as error:
                self.status = ("storage_error" if isinstance(error, StoreError) else
                    "network_failure" if isinstance(error, NetworkFailure) else "parser_failure")
                self._refresh_view()
                raise

    def import_cookies(self, candidate):
        with self.lock:
            # Failed validation or persistence leaves the prior active session intact.
            self._validate_and_save(candidate)

    def poll(self):
        with self.lock:
            if not len(self.cookies):
                self.status = "credential_required"
                self._refresh_view()
                return
            try:
                self._validate_and_save(self.cookies)
            except InvalidSession:
                self.session_valid = False
                self.credential_required = True
                self.status = "credential_required"
                self.failures += 1
            except NetworkFailure:
                self.status = "credential_required" if self.credential_required else "network_failure"
                self.failures += 1
            except GoogleError:
                self.status = "credential_required" if self.credential_required else "parser_failure"
                self.failures += 1
            except StoreError:
                self.status = "storage_error"
                self.failures += 1
            self._refresh_view()

    @property
    def retry_seconds(self):
        return min(3600, self.config.poll_seconds * 2 ** min(self.failures, 6))

    def _refresh_view(self):
        # Publish immutable views after a commit/state transition. Network polling
        # keeps the jar lock, but cannot delay freshness expiry or status reads.
        self._view = (self.status, tuple(self.people.values()), frozenset(self.present), self.session_valid, dict(self.missing_since))
        expirations = [c.expires for c in self.cookies if c.name in AUTH_NAMES and c.expires]
        expiry = None
        if expirations:
            try:
                expiry = datetime.fromtimestamp(min(expirations), UTC).date().isoformat()
            except (ValueError, OverflowError, OSError):
                pass
        self._management = {"session_status": self.status,
            "last_successful_poll": self.last_success, "contact_count": len(self.present),
            "approximate_cookie_expiry": expiry}

    def snapshot(self):
        status, people, present, session_valid, missing = self._view
        now = self.clock()
        # Upstream retains the last known fix through network/auth failures and
        # stationary old observations. A successful response omitting a contact
        # starts its three-minute missing-data grace period.
        return {"status": status, "session_valid": session_valid, "people": people,
            "available": frozenset(p.id for p in people
                if (p.id in present or now - missing.get(p.id, now) < 180)
                and (not self.config.freshness_seconds
                     or 0 <= now - p.source_timestamp < self.config.freshness_seconds))}

    def management_status(self):
        return dict(self._management)
