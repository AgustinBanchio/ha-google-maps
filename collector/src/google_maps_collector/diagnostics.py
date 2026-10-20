"""Bounded, allowlisted operational metadata. Never accept exception text."""
from copy import deepcopy
from enum import StrEnum
import json
import logging
import math
from pathlib import Path
import sys
from threading import RLock
import time

from .store import atomic_write

LIMIT = 32
MAX_BYTES = 65536
LOGGER = logging.getLogger("google_maps_collector.events")


class Reason(StrEnum):
    INVALID_SESSION = "google_invalid_session_marker"
    HTTP_AUTH = "google_http_auth_rejected"
    REDIRECT = "google_redirect_rejected"
    HTTP_ERROR = "google_http_error"
    TIMEOUT = "google_timeout"
    TLS = "google_tls_error"
    CONNECTION = "google_connection_error"
    RETRIES = "google_retries_exhausted"
    NETWORK = "google_network_error"
    POLICY = "transport_policy_rejected"
    TOO_LARGE = "google_response_too_large"
    ENCODING = "google_response_encoding_invalid"
    DATA = "google_data_invalid"
    OBSERVATION = "google_observation_invalid"
    SESSION = "google_session_required"
    STORAGE = "credential_store_unavailable"
    DATA_KEY = "data_access_denied"
    UNKNOWN = "unclassified_failure"


OPERATIONS = {"native_poll", "legacy_poll", "session_import", "data_auth"}
EVENT_KEYS = {"time", "operation", "outcome", "reason", "http_status", "cookie_changes"}
STATE_KEYS = {"schema", "last_attempt", "last_success", "last_failure", "last_source_failure", "events"}


class EventHandler(logging.Handler):
    def emit(self, record):
        try:
            # Resolve stderr at write time. Never invoke logging.handleError:
            # its fallback prints the surrounding exception/stack on IO failure.
            sys.stderr.write(self.format(record) + "\n")
            sys.stderr.flush()
        except Exception:
            pass  # Optional output must not interrupt polling or dump context.


def configure_logging():
    """Only our fixed JSON records; leave upstream/HTTP debug logging disabled."""
    handler = EventHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.handlers = [handler]
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def cookie_changes(before, after):
    # Compare credentials only inside their existing owner. Emit counts only,
    # never names, identifiers, values, expiry fingerprints or hashes.
    def records(jar):
        return {(c.domain, c.path, c.name): (c.value, c.expires, c.secure) for c in jar}
    old, new = records(before), records(after)
    return {"added": len(new.keys() - old.keys()),
        "changed": sum(old[k] != new[k] for k in old.keys() & new.keys()),
        "removed": len(old.keys() - new.keys())}


def failure_metadata(error):
    from .google_maps import InvalidSession, InvalidData, NetworkFailure
    from .store import StoreError
    reason = getattr(error, "reason", None)
    if not isinstance(reason, Reason):
        reason = (Reason.STORAGE if isinstance(error, StoreError) else
            Reason.SESSION if isinstance(error, InvalidSession) else
            Reason.DATA if isinstance(error, InvalidData) else
            Reason.NETWORK if isinstance(error, NetworkFailure) else Reason.UNKNOWN)
    status = getattr(error, "http_status", None)
    if type(status) is not int or not 100 <= status <= 599:
        status = None
    return reason, status


def valid_event(event):
    if type(event) is not dict or set(event) != EVENT_KEYS:
        return False
    now = event["time"]
    status, counts = event["http_status"], event["cookie_changes"]
    return (type(now) in {int, float} and math.isfinite(now) and 0 <= now < 100_000_000_000
        and event["operation"] in OPERATIONS and event["outcome"] in {"success", "failure"}
        and event["reason"] in {None, *Reason}
        and (status is None or type(status) is int and 100 <= status <= 599)
        and type(counts) is dict and set(counts) == {"added", "changed", "removed"}
        and all(type(v) is int and 0 <= v <= 65535 for v in counts.values()))


class Diagnostics:
    def __init__(self, path: Path, clock=time.time):
        self.path, self.clock, self.lock = path, clock, RLock()
        self.available, self.history_reset = True, False
        self.state = {"schema": 1, "last_attempt": None, "last_success": None,
            "last_failure": None, "last_source_failure": None, "events": []}
        try:
            if path.is_symlink():
                raise ValueError()
            with path.open("rb") as source:
                raw = source.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError()
            data = json.loads(raw)
            if (type(data) is not dict or set(data) != STATE_KEYS or type(data["schema"]) is not int
                    or data["schema"] != 1 or type(data["events"]) is not list
                    or len(data["events"]) > LIMIT
                    or any(not valid_event(e) for e in data["events"])
                    or any(e is not None and not valid_event(e) for k, e in data.items()
                        if k not in {"schema", "events"})):
                raise ValueError()
            self.state = data
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            # Corrupt optional metadata cannot prevent location collection or
            # cause unvalidated stored strings to reach logs/the status API.
            self.history_reset = True

    def record(self, operation, *, error=None, changes=None):
        if operation not in OPERATIONS:
            raise ValueError("invalid diagnostic operation")
        reason, status = failure_metadata(error) if error is not None else (None, None)
        changes = changes or {"added": 0, "changed": 0, "removed": 0}
        event = {"time": self.clock(), "operation": operation,
            "outcome": "failure" if error is not None else "success", "reason": reason,
            "http_status": status, "cookie_changes": changes}
        if not valid_event(event):
            raise ValueError("invalid diagnostic metadata")
        with self.lock:
            self.state["last_attempt"] = event
            if error is not None:
                self.state["last_failure"] = event
                if operation != "data_auth":
                    self.state["last_source_failure"] = event
            elif operation != "data_auth":
                self.state["last_success"] = event
            previous = self.state["events"][-1] if self.state["events"] else None
            changed = (previous is None or any(event[k] != previous[k] for k in
                ("operation", "outcome", "reason", "http_status")) or any(changes.values())
                or event["time"] - previous["time"] >= 900)
            if changed:
                self.state["events"] = (self.state["events"] + [event])[-LIMIT:]
                LOGGER.info(json.dumps({"event": "collector_operation", **event}, separators=(",", ":")))
            try:
                atomic_write(self.path, json.dumps(self.state, allow_nan=False, separators=(",", ":")).encode())
                self.available = True
            except (OSError, ValueError):
                if self.available:
                    LOGGER.warning('{"event":"diagnostics_write_failed"}')
                self.available = False

    def snapshot(self):
        with self.lock:
            return {**deepcopy(self.state), "persistence_available": self.available,
                "history_reset": self.history_reset}
