"""DataUpdateCoordinator for the Google Maps integration."""
from __future__ import annotations

from asyncio import Lock
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

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
from .helpers import PersonData, UniqueID, expiring_soon
from .collector_client import CollectorClient

_LOGGER = logging.getLogger(__name__)


GMData = dict[UniqueID, PersonData]
"""Google Maps data.

Dictionary of unique ID -> PersonData.
For "account entity", unique ID is the account's email address.
"""


class GMDataUpdateCoordinator(DataUpdateCoordinator[GMData]):
    """Google Maps data update coordinator."""

    config_entry: ConfigEntry
    _api: CollectorClient
    _unsub_exp: Callable[[], None] | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self._create_acct_entity = entry.options[CONF_CREATE_ACCT_ENTITY]

        # The account's username is used as the config entry's unique ID.
        self._account_email = cast(str, entry.unique_id)
        self.cookie_lock = Lock()

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=entry.options[CONF_SCAN_INTERVAL]),
            always_update=False,
        )

    async def async_shutdown(self) -> None:
        """Cancel listeners, save cookies & close API."""
        await super().async_shutdown()
        self._unsub_all()
        if hasattr(self, "_api"):
            async with self.cookie_lock:
                await self.hass.async_add_executor_job(self._api.close)

    def _unsub_all(self) -> None:
        """Run removers."""
        self._unsub_expiration()

    def _unsub_expiration(self) -> None:
        """Remove expiration listener."""
        if self._unsub_exp:
            self._unsub_exp()
            self._unsub_exp = None

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self._api = CollectorClient(self.config_entry.data["endpoint"],
                self.config_entry.data["data_token"], self._account_email)
        except ValueError:
            raise ConfigEntryAuthFailed("Configure the external collector connection") from None

    async def _async_update_data(self) -> GMData:
        """Fetch the latest data from the source.

        If creating "account entity", its unique ID will be the account's email address.
        """
        async with self.cookie_lock:
            try:
                await self.hass.async_add_executor_job(self._api.get_new_data)
                people = self._api.get_people(self._create_acct_entity)
            except InvalidCookies as err:
                raise ConfigEntryAuthFailed(f"{err.__class__.__name__}: {err}") from err
            except (RequestFailed, InvalidData) as err:
                raise UpdateFailed(f"{err.__class__.__name__}: {err}") from err

        self._source_expiration_synced()
        return {
            UniqueID(person.id): PersonData.from_person(person) for person in people
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

    def __init__(
        self, coordinator: GMDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize."""
        self.coordinator = coordinator
        self.setup_data = deepcopy(dict(entry.data))
        self.setup_options = deepcopy(dict(entry.options))


GMConfigEntry = ConfigEntry[GMConfigEntryParams]
