"""DataUpdateCoordinator for the Google Maps integration."""

from asyncio import Lock, Queue
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, cast, override

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .collector_client import CollectorClient
from .const import (
    CONF_CREATE_ACCT_ENTITY,
    COOKIE_WARNING_PERIOD,
    DOMAIN,
)
from .gm_loc_sharing import (
    InvalidCookies,
    InvalidData,
    RequestFailed,
)
from .helpers import PersonData, PersonID, expiring_soon

_LOGGER = logging.getLogger(__name__)


GMPersonData = dict[PersonID, PersonData]
"""Google Maps person data.

Dictionary of person ID -> PersonData.
For "account entity", person ID is the account's email address.
"""


class GMDataUpdateCoordinator(DataUpdateCoordinator[GMPersonData]):
    """Google Maps data update coordinator."""

    config_entry: ConfigEntry
    _api: CollectorClient
    _unsub_exp: Callable[[], None] | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self._create_acct_entity = entry.options[CONF_CREATE_ACCT_ENTITY]

        # The account's email address (aka username) is used as the config entry's
        # unique ID.
        self._account_email = cast(str, entry.unique_id)
        self._source_lock = Lock()

        if entry.pref_disable_polling:
            update_interval: timedelta | None = None
            always_update = True
        else:
            update_interval = timedelta(seconds=entry.options[CONF_SCAN_INTERVAL])
            always_update = False
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=update_interval,
            always_update=always_update,
        )

    @override
    async def async_shutdown(self) -> None:
        """Cancel listeners and close the local collector connection."""
        await super().async_shutdown()
        self._unsub_all()
        if hasattr(self, "_api"):
            async with self._source_lock:
                await self.hass.async_add_executor_job(self._api.close)

    def _unsub_all(self) -> None:
        """Run removers."""
        self._unsub_expiration()

    def _unsub_expiration(self) -> None:
        """Remove expiration listener."""
        if self._unsub_exp:
            self._unsub_exp()
            self._unsub_exp = None

    @override
    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self._api = CollectorClient(self.config_entry.data["endpoint"],
                self.config_entry.data["data_token"], self._account_email)
        except ValueError:
            raise ConfigEntryAuthFailed("Configure the external collector connection") from None

    @override
    async def _async_update_data(self) -> GMPersonData:
        """Fetch the latest data from the source.

        If creating "account entity", its person ID will be the account's email address.
        """
        async with self._source_lock:
            try:
                await self.hass.async_add_executor_job(self._api.get_new_data)
                people = self._api.get_people(self._create_acct_entity)
            except InvalidCookies as err:
                raise ConfigEntryAuthFailed(f"{err.__class__.__name__}: {err}") from err
            except (RequestFailed, InvalidData) as err:
                raise UpdateFailed(f"{err.__class__.__name__}: {err}") from err

        self._source_expiration_synced()
        return {
            PersonID(person.id): PersonData.from_person(person) for person in people
        }

    def _source_expiration_synced(self, shutting_down: bool = False) -> None:
        """Retain upstream expiry repairs using non-secret source metadata."""
        cookies_expiration = self._api.cookies_expiration
        if expiring_soon(cookies_expiration):
            self._create_issue()
        else:
            ir.async_delete_issue(self.hass, DOMAIN, self.config_entry.entry_id)
            if cookies_expiration and not shutting_down:
                self._unsub_expiration()
                self._unsub_exp = async_track_point_in_utc_time(
                    self.hass,
                    self._create_issue,
                    cookies_expiration - COOKIE_WARNING_PERIOD,
                )

    @callback
    def _create_issue(self, _utcnow: datetime | None = None) -> None:
        """Create repair issue for cookies which are expiring soon."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.config_entry.entry_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="expiring_soon",
            translation_placeholders={
                "entry_id": self.config_entry.entry_id,
                "username": cast(str, self.config_entry.unique_id),
            },
        )


@dataclass
class GMConfigEntryParams:
    """Google Maps Config Entry Parameters."""

    coordinator: GMDataUpdateCoordinator
    setup_data: dict[str, Any]
    setup_options: dict[str, Any]
    new_sensors_queue: Queue[list[SensorEntity]]

    def __init__(
        self, coordinator: GMDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize."""
        self.coordinator = coordinator
        self.setup_data = deepcopy(dict(entry.data))
        self.setup_options = deepcopy(dict(entry.options))
        self.new_sensors_queue = Queue()


GMConfigEntry = ConfigEntry[GMConfigEntryParams]
