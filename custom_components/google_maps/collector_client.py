"""Data-only local transport for the original Google Maps coordinator.

Google authentication never crosses this boundary. Person parsing and HA entity
policy remain upstream; wire timestamps are seconds, constructor input is ms.
"""
from dataclasses import fields
from datetime import datetime
import json
import math
from urllib.parse import urlsplit

import requests
from .gm_loc_sharing import GMPerson, InvalidCookies, InvalidData, RequestFailed

UPSTREAM_REVISION = "b2132123d46c47e5761d5d91cc08ca6b712fe6c1"
DEFAULT_ENDPOINT = "http://127.0.0.1:8787"
MAX_BYTES = 4 * 1024 * 1024


class CollectorClient:
    def __init__(self, endpoint, token, account_email, session=None):
        try:
            url = urlsplit(endpoint)
            if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost"}
                    or url.port != 8787 or url.username or url.password
                    or url.path not in {"", "/"} or url.query or url.fragment):
                raise ValueError()
            if (not isinstance(token, str) or not 32 <= len(token) <= 256
                    or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in token)):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("invalid local collector configuration") from None
        self.endpoint = endpoint.rstrip("/")
        self._token = token
        self._account_email = account_email
        self._people = []
        self._expiration = None
        self.session = session if session is not None else requests.Session()
        self.session.trust_env = False

    def close(self):
        self.session.close()

    @property
    def cookies_expiration(self):
        """Non-secret expiry metadata used by upstream repair handling."""
        return self._expiration

    def get_new_data(self):
        response = None
        try:
            response = self.session.get(self.endpoint + "/v1/locations",
                headers={"Authorization": "Bearer " + self._token},
                timeout=(5, 360), allow_redirects=False, stream=True)
            if response.status_code == 401:
                raise InvalidCookies("Collector access key rejected")
            if response.status_code == 409:
                raise InvalidCookies("Import the Google session in the external collector")
            if response.status_code == 502:
                raise InvalidData("Collector returned invalid Google data")
            if response.status_code != 200:
                raise RequestFailed("Collector unavailable")
            body = bytearray()
            for chunk in response.iter_content(65536):
                if len(body) + len(chunk) > MAX_BYTES:
                    raise InvalidData("Collector response too large")
                body.extend(chunk)
            data = json.loads(body)
            if (set(data) != {"schema", "upstream_revision", "people", "account", "cookie_expiration"}
                    or data["schema"] != 1 or data["upstream_revision"] != UPSTREAM_REVISION
                    or not isinstance(data["people"], list)):
                raise ValueError()
            people = [(self._person(item), False) for item in data["people"]]
            if data["account"] is not None:
                account = self._person(data["account"])
                # Upstream identifies/names the optional account tracker using the
                # account supplied in HA configuration, not Google credentials.
                account.id = account.full_name = account.nickname = self._account_email
                people.append((account, True))
            expiration = datetime.fromisoformat(data["cookie_expiration"]) if data["cookie_expiration"] else None
            if expiration is not None and expiration.tzinfo is None:
                raise ValueError()
            if len({person.id for person, _ in people}) != len(people):
                raise ValueError()
            self._people, self._expiration = people, expiration
        except requests.RequestException:
            raise RequestFailed("Collector unavailable") from None
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            raise InvalidData("Invalid collector response") from None
        finally:
            if response is not None:
                response.close()

    @staticmethod
    def _person(item):
        if not isinstance(item, dict) or set(item) != {field.name for field in fields(GMPerson)}:
            raise ValueError()
        for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180),
                ("gps_accuracy", 0, 1_000_000), ("last_seen", 0, 100_000_000_000)):
            value = item[key]
            if type(value) not in {int, float} or not math.isfinite(value) or not low <= value <= high:
                raise ValueError()
        if not isinstance(item["id"], str) or not item["id"]:
            raise ValueError()
        # GMPerson.__post_init__ divides its input by 1000. Preserve upstream's
        # integer-millisecond observation exactly rather than dividing twice.
        values = {**item, "last_seen": round(item["last_seen"] * 1000)}
        person = GMPerson(**values)
        if person.last_seen != item["last_seen"]:
            raise ValueError()
        return person

    def get_people(self, include_acct_person):
        return [person for person, account in self._people if include_acct_person or not account]
