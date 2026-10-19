"""Original Google Maps options with external-session source configuration."""
from __future__ import annotations
from abc import abstractmethod
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryBaseFlow, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (BooleanSelector, DurationSelector, NumberSelector,
    NumberSelectorConfig, NumberSelectorMode, TextSelector, TextSelectorConfig, TextSelectorType)
from homeassistant.loader import async_get_integration
from .const import CONF_CREATE_ACCT_ENTITY, CONF_MAX_GPS_ACCURACY, DEF_SCAN_INTERVAL_SEC, DOMAIN
from .collector_client import CollectorClient, DEFAULT_ENDPOINT
from .gm_loc_sharing import InvalidCookies, InvalidData, RequestFailed

class GoogleMapsFlow(ConfigEntryBaseFlow):
    """Google Maps flow mixin."""

    _username: str
    _options: dict[str, Any]

    def _init_gmflow(self, username: str, options: Mapping[str, Any]) -> None:
        """Initialize GoogleMapsFlow."""
        self._username = username
        self._options = deepcopy(dict(options))

    async def async_step_account_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Determine if entity should be created for account."""
        if user_input is not None:
            self._options[CONF_CREATE_ACCT_ENTITY] = user_input[CONF_CREATE_ACCT_ENTITY]
            return await self.async_step_max_gps_accuracy()

        data_schema = vol.Schema(
            {vol.Required(CONF_CREATE_ACCT_ENTITY): BooleanSelector()}
        )
        data_schema = self.add_suggested_values_to_schema(
            data_schema,
            {CONF_CREATE_ACCT_ENTITY: self._options.get(CONF_CREATE_ACCT_ENTITY, True)},
        )
        if doc := (await async_get_integration(self.hass, DOMAIN)).documentation:
            doc = (
                "[Missing Data for Account Tracker]"
                f"({doc}#missing-data-for-account-tracker)"
            )
        else:
            doc = "the integration's documentation"
        return self.async_show_form(
            step_id="account_entity",
            data_schema=data_schema,
            description_placeholders={"doc": doc, "username": self._username},
            last_step=False,
        )

    async def async_step_max_gps_accuracy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Get maximum GPS accuracy."""
        if user_input is not None:
            self._options[CONF_MAX_GPS_ACCURACY] = int(
                user_input[CONF_MAX_GPS_ACCURACY]
            )
            return await self.async_step_update_period()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MAX_GPS_ACCURACY): NumberSelector(
                    NumberSelectorConfig(min=0, mode=NumberSelectorMode.BOX)
                ),
            }
        )
        data_schema = self.add_suggested_values_to_schema(
            data_schema,
            {CONF_MAX_GPS_ACCURACY: self._options.get(CONF_MAX_GPS_ACCURACY, 1000)},
        )
        return self.async_show_form(
            step_id="max_gps_accuracy", data_schema=data_schema, last_step=False
        )

    async def async_step_update_period(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Get update period."""
        if user_input is not None:
            self._options[CONF_SCAN_INTERVAL] = int(
                cv.time_period_dict(user_input[CONF_SCAN_INTERVAL]).total_seconds()
            )
            return await self.async_step_done()

        data_schema = vol.Schema({vol.Required(CONF_SCAN_INTERVAL): DurationSelector()})
        default = self._options.get(CONF_SCAN_INTERVAL, DEF_SCAN_INTERVAL_SEC)
        def_m, def_s = divmod(default, 60)
        def_h, def_m = divmod(def_m, 60)
        data_schema = self.add_suggested_values_to_schema(
            data_schema,
            {CONF_SCAN_INTERVAL: {"hours": def_h, "minutes": def_m, "seconds": def_s}},
        )
        return self.async_show_form(step_id="update_period", data_schema=data_schema)

    @abstractmethod
    async def async_step_done(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish the user config or options flow."""


class GoogleMapsConfigFlow(ConfigFlow, GoogleMapsFlow, domain=DOMAIN):
    """Configure a data-only collector connection; never upload Google cookies."""
    VERSION = 4
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GoogleMapsOptionsFlow()

    async def async_step_user(self, user_input=None):
        return await self.async_step_source(user_input)

    async def async_step_reauth(self, data):
        return await self.async_step_source()

    async def async_step_reconfigure(self, data):
        return await self.async_step_source()

    async def async_step_source(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(self.context.get("entry_id", ""))
        errors = {}
        if user_input is not None:
            account = user_input[CONF_USERNAME].strip().lower()
            client = None
            try:
                if not account or entry and account != entry.unique_id:
                    raise ValueError()
                client = CollectorClient(user_input["endpoint"], user_input["data_token"], account)
                await self.hass.async_add_executor_job(client.get_new_data)
            except InvalidCookies:
                errors["base"] = "session_required"
            except (InvalidData, RequestFailed):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_source"
            finally:
                if client is not None:
                    client.close()
            if not errors:
                await self.async_set_unique_id(account)
                if entry is None:
                    self._abort_if_unique_id_configured()
                self._data = {"endpoint": user_input["endpoint"].rstrip("/"), "data_token": user_input["data_token"]}
                self._source_entry = entry
                self._init_gmflow(account, entry.options if entry else {})
                if entry:
                    return await self.async_step_done()
                return await self.async_step_account_entity()
        schema = vol.Schema({
            vol.Required(CONF_USERNAME, default=entry.unique_id if entry else vol.UNDEFINED): str,
            vol.Required("endpoint", default=entry.data.get("endpoint", DEFAULT_ENDPOINT) if entry else DEFAULT_ENDPOINT): str,
            vol.Required("data_token"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        })
        return self.async_show_form(step_id="source", data_schema=schema, errors=errors)

    async def async_step_done(self, _=None):
        if self._source_entry is not None:
            self.hass.config_entries.async_update_entry(self._source_entry, data=self._data, version=self.VERSION)
            await self.hass.config_entries.async_reload(self._source_entry.entry_id)
            return self.async_abort(reason="reauth_successful" if self.context.get("source") == "reauth" else "reconfigure_successful")
        return self.async_create_entry(title=self._username, data=self._data, options=self._options)


class GoogleMapsOptionsFlow(OptionsFlow, GoogleMapsFlow):
    """Google Maps options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start options flow."""
        username = self.config_entry.unique_id
        assert username
        self._init_gmflow(username, self.config_entry.options)
        return await self.async_step_account_entity()

    async def async_step_done(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish the flow."""
        return self.async_create_entry(title="", data=self._options)
