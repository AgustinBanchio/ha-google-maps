"""Security wrapper around the unchanged upstream Google Maps client.

The upstream module supplies request parameters, response handling and person
parsing. This wrapper owns bounded fixed-origin IO and sanitized public errors.
"""
from dataclasses import dataclass
from http.cookiejar import CookieJar
import logging
import math
from types import SimpleNamespace

import requests
from ._upstream import gm_loc_sharing as upstream
from .diagnostics import Reason

REVISION = "b2132123d46c47e5761d5d91cc08ca6b712fe6c1"
ACCOUNT_ID = "__collector_account__"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

# Upstream logs raw responses on malformed/auth errors. Never install those
# handlers in this service; fixed errors below are the only outward contract.
logging.getLogger(upstream.__name__).disabled = True


@dataclass(frozen=True, repr=False)
class Observations:
    people: tuple
    account: object | None
    expiration: object | None


class RestrictedSession:
    def __init__(self, session):
        self.session = session
        self.session.trust_env = False

    @property
    def cookies(self):
        return self.session.cookies

    def close(self):
        self.session.close()

    def get(self, url, *, params, timeout, verify):
        from .google_maps import URL, InvalidData, InvalidSession, NetworkFailure, UnexpectedRedirect
        if url != URL or verify is not True:
            raise NetworkFailure(Reason.POLICY)
        response = None
        try:
            response = self.session.get(url, params=params, timeout=(10, 60),
                verify=True, allow_redirects=False, stream=True)
            if 300 <= response.status_code < 400:
                raise UnexpectedRedirect(Reason.REDIRECT, response.status_code)
            if response.status_code in {401, 403}:
                raise InvalidSession(Reason.HTTP_AUTH, response.status_code)
            if response.status_code != 200:
                raise NetworkFailure(Reason.HTTP_ERROR, response.status_code)
            body = bytearray()
            for chunk in response.iter_content(65536):
                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise InvalidData(Reason.TOO_LARGE, response.status_code)
                body.extend(chunk)
            return SimpleNamespace(text=body.decode("utf-8"), raise_for_status=lambda: None)
        except requests.exceptions.SSLError:
            raise NetworkFailure(Reason.TLS) from None
        except requests.Timeout:
            raise NetworkFailure(Reason.TIMEOUT) from None
        except requests.ConnectionError:
            raise NetworkFailure(Reason.CONNECTION) from None
        except requests.exceptions.RetryError:
            raise NetworkFailure(Reason.RETRIES) from None
        except requests.RequestException:
            raise NetworkFailure(Reason.NETWORK) from None
        except UnicodeError:
            raise InvalidData(Reason.ENCODING, 200) from None
        finally:
            if response is not None:
                response.close()


def validate_person(person):
    from .google_maps import InvalidData
    for value, low, high in ((person.latitude, -90, 90), (person.longitude, -180, 180),
            (person.gps_accuracy, 0, 1_000_000), (person.last_seen, 0, 100_000_000_000)):
        if type(value) not in {int, float} or not math.isfinite(value) or not low <= value <= high:
            raise InvalidData(Reason.OBSERVATION, 200)
    if not isinstance(person.id, str) or not person.id or len(person.id) > 512:
        raise InvalidData(Reason.OBSERVATION, 200)


class UpstreamSource:
    def __init__(self, session=None):
        self.client = upstream.GMLocSharing(ACCOUNT_ID)
        if session is None:
            self.session = self.client._session
        else:
            self.client.close()
            self.session = session
        self.client._session = RestrictedSession(self.session)

    def poll(self, cookies: CookieJar):
        from .google_maps import filter_cookies, InvalidData, InvalidSession, NetworkFailure
        self.session.cookies = filter_cookies(cookies)
        self.client.__dict__.pop("_cookies", None)
        try:
            self.client.get_new_data()
            people = tuple(self.client.get_people(False))
            account = None
            if len(self.client._data) >= 10:
                account = upstream.GMPerson.acct_from_data(self.client._data[9], ACCOUNT_ID)
            identities = set()
            for person in (*people, *((account,) if account else ())):
                validate_person(person)
                if person.id in identities:
                    raise InvalidData(Reason.OBSERVATION, 200)
                identities.add(person.id)
            return Observations(people, account, self.client.cookies_expiration), filter_cookies(self.session.cookies)
        except upstream.InvalidCookies:
            raise InvalidSession(Reason.INVALID_SESSION, 200) from None
        except upstream.RequestFailed:
            raise NetworkFailure(Reason.NETWORK) from None
        except (upstream.InvalidData, IndexError, TypeError, ValueError, KeyError, RecursionError):
            raise InvalidData(Reason.DATA, 200) from None

    def close(self):
        self.session.close()
