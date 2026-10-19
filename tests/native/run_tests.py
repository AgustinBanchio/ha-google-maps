"""Actual HA runtime verification; runs in a disposable installed-version image.

No HA production mounts, host network, Google credentials or external IO.
"""
import asyncio
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
import json
import os
import inspect
from pathlib import Path
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch

ROOT = Path(os.environ["HA_NATIVE_SOURCE"]) if "HA_NATIVE_SOURCE" in os.environ else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntries, ConfigEntryDisabler
from homeassistant.setup import async_setup_component
from homeassistant import loader
from homeassistant.helpers import entity_registry as er, device_registry as dr, issue_registry as ir, area_registry as ar
from custom_components.google_maps import collector_client
from custom_components.google_maps.gm_loc_sharing import GMPerson, GMLocSharing
from custom_components.google_maps.const import CONF_CREATE_ACCT_ENTITY, CONF_MAX_GPS_ACCURACY

DIAGNOSTICS = []

TOKEN = "SYNTHETIC_DATA_ACCESS_KEY_000000000000000000000"
ACCOUNT = "synthetic-owner@example.invalid"
ORIGINAL_CLIENT = collector_client.CollectorClient


class Response:
    status_code = 200
    def __init__(self, document): self.document = document
    def iter_content(self, size): yield json.dumps(self.document).encode()
    def close(self): pass


class Session:
    def __init__(self, owner): self.owner = owner
    def get(self, url, **kwargs):
        assert url == "http://127.0.0.1:8787/v1/locations"
        assert kwargs["headers"] == {"Authorization": "Bearer " + TOKEN}
        assert kwargs["allow_redirects"] is False
        self.owner.calls += 1
        response = Response(self.owner.document)
        response.status_code = self.owner.status
        return response
    def close(self): pass


class NativeRuntime(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        directory = Path(self.temp.name)
        (directory / "custom_components").mkdir()
        (directory / "custom_components/google_maps").symlink_to(ROOT / "custom_components/google_maps", target_is_directory=True)
        self.hass = HomeAssistant(str(directory))
        self.raw = json.loads((ROOT / "collector/tests/fixtures/google_response.json").read_text())
        self.calls, self.status = 0, 200
        self.set_document()
        self.patches = [patch("custom_components.google_maps.coordinator.CollectorClient", self.client),
                        patch("custom_components.google_maps.config_flow.CollectorClient", self.client)]
        for item in self.patches: item.start()
        initialized = loader.async_setup(self.hass)
        if inspect.isawaitable(initialized):
            await initialized
        self.hass.config.skip_pip = True
        self.hass.config_entries = ConfigEntries(self.hass, {})
        await self.hass.config_entries.async_initialize()
        dr.async_setup(self.hass)
        for module in (ar, dr, er, ir):
            if hasattr(module, "async_load"):
                initialized = module.async_load(self.hass)
            else:
                initialized = module.async_get(self.hass).async_load()
            if inspect.isawaitable(initialized):
                await initialized
        assert await async_setup_component(self.hass, "homeassistant", {})

    def set_document(self):
        reference = GMLocSharing(ACCOUNT)
        reference._data = deepcopy(self.raw)
        people = reference.get_people(False)
        account = GMPerson.acct_from_data(self.raw[9], ACCOUNT) if len(self.raw)>9 and self.raw[9] else None
        self.document = {"schema":1,"upstream_revision":collector_client.UPSTREAM_REVISION,
            "people":[asdict(p) for p in people],"account":asdict(account) if account else None,"cookie_expiration":None}
        reference.close()

    def client(self, endpoint, token, account):
        return ORIGINAL_CLIENT(endpoint, token, account, Session(self))

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        for item in self.patches: item.stop()
        self.temp.cleanup()

    async def add_entry(self, account=True):
        self.entry = ConfigEntry(version=4, minor_version=1, domain="google_maps", title=ACCOUNT,
            data={"endpoint":"http://127.0.0.1:8787","data_token":TOKEN},
            options={CONF_CREATE_ACCT_ENTITY:account,CONF_MAX_GPS_ACCURACY:1000,"scan_interval":60},
            source="user",unique_id=ACCOUNT,discovery_keys={},subentries_data=[])
        await self.hass.config_entries.async_add(self.entry)
        self.assertEqual(str(self.entry.state), "ConfigEntryState.LOADED",
            f"entry setup state={self.entry.state} reason={getattr(self.entry, 'reason', None)} diagnostics={DIAGNOSTICS[-2:]}")
        await self.hass.async_block_till_done()
        self.assertTrue(self.entry.runtime_data.coordinator.last_update_success)
        return self.entry.runtime_data.coordinator

    def tracker(self):
        entity_id = er.async_get(self.hass).async_get_entity_id("device_tracker","google_maps","synthetic-person")
        self.assertIsNotNone(entity_id)
        state = self.hass.states.get(entity_id)
        self.assertIsNotNone(state)
        return state

    async def refresh(self, coordinator):
        self.set_document()
        await coordinator.async_refresh()
        await self.hass.async_block_till_done()

    async def test_original_entity_fields_accuracy_metadata_and_restore(self):
        coordinator = await self.add_entry()
        state = self.tracker()
        self.assertEqual(state.attributes["friendly_name"], "Google Maps SYNTHETIC_NAME")
        self.assertEqual(state.attributes["entity_picture"], "https://lh3.googleusercontent.com/synthetic-picture")
        self.assertEqual(state.attributes["nickname"], "Synthetic")
        self.assertEqual(state.attributes["address"], "SYNTHETIC_ADDRESS")
        self.assertEqual(state.attributes["latitude"], 0.5)
        self.assertEqual(state.attributes["battery_level"], 73)
        initial_seen = state.attributes["last_seen"]
        # Native transport gives an older inaccurate fix and fresh misc metadata;
        # unchanged upstream entities retain GPS while adopting misc fields.
        self.raw[0][0][1][2] -= 1000
        self.raw[0][0][1][1][2] = 1.25
        self.raw[0][0][1][3] = 2000
        self.raw[0][0][13] = [True,42]
        self.raw[0][0][6][3] = "Updated nickname"
        await self.refresh(coordinator)
        state = self.tracker()
        self.assertEqual(state.attributes["latitude"],0.5)
        self.assertEqual(state.attributes["last_seen"],initial_seen)
        self.assertEqual(state.attributes["battery_level"],42)
        self.assertTrue(state.attributes["battery_charging"])
        self.assertEqual(state.attributes["nickname"],"Updated nickname")
        # Newer, less accurate fix is still ignored by original entity policy.
        self.raw[0][0][1][2] += 3000
        await self.refresh(coordinator)
        self.assertEqual(self.tracker().attributes["latitude"],0.5)
        await self.hass.config_entries.async_reload(self.entry.entry_id)
        await self.hass.async_block_till_done()
        self.assertEqual(self.tracker().attributes["latitude"],0.5)
        self.assertEqual(self.tracker().attributes["last_seen"],initial_seen)
        self.raw[0][0][1][3] = 30
        await self.refresh(self.entry.runtime_data.coordinator)
        self.assertEqual(self.tracker().attributes["latitude"],1.25)

    async def test_original_missing_contact_grace_and_reappearance(self):
        coordinator = await self.add_entry()
        calls=[]
        def later(hass, delay, callback):
            calls.append((delay, callback))
            return lambda: None
        self.raw[0] = []
        with patch("custom_components.google_maps.device_tracker.async_call_later", later):
            await self.refresh(coordinator)
        self.assertEqual(calls[0][0],180)
        self.assertNotEqual(self.tracker().state,"unavailable")
        await calls[0][1](datetime.now(UTC))
        await self.hass.async_block_till_done()
        self.assertEqual(self.tracker().state,"unavailable")
        self.raw=json.loads((ROOT / "collector/tests/fixtures/google_response.json").read_text())
        await self.refresh(coordinator)
        self.assertNotEqual(self.tracker().state,"unavailable")

    async def test_original_account_option_identity_and_poll_interval(self):
        self.raw.extend([None,None,deepcopy(self.raw[0][0])])
        self.set_document()
        coordinator = await self.add_entry(account=False)
        registry=er.async_get(self.hass)
        self.assertIsNone(registry.async_get_entity_id("device_tracker","google_maps",ACCOUNT))
        self.hass.config_entries.async_update_entry(self.entry,options={**self.entry.options,CONF_CREATE_ACCT_ENTITY:True,"scan_interval":120})
        await self.hass.async_block_till_done()
        await self.hass.config_entries.async_reload(self.entry.entry_id)
        await self.hass.async_block_till_done()
        entity_id=registry.async_get_entity_id("device_tracker","google_maps",ACCOUNT)
        self.assertIsNotNone(entity_id)
        self.assertEqual(self.hass.states.get(entity_id).attributes["friendly_name"],"Google Maps "+ACCOUNT)
        self.assertEqual(self.entry.runtime_data.coordinator.update_interval.total_seconds(),120)

    async def test_original_connectivity_failures_keep_last_known_tracker(self):
        coordinator = await self.add_entry()
        previous = self.tracker()
        for status in (503, 502, 409):
            self.status = status
            await coordinator.async_refresh()
            await self.hass.async_block_till_done()
            self.assertFalse(coordinator.last_update_success)
            current = self.tracker()
            self.assertEqual(current.attributes["latitude"], previous.attributes["latitude"])
            self.assertEqual(current.attributes["last_seen"], previous.attributes["last_seen"])
            self.assertNotEqual(current.state,"unavailable")
            states = self.hass.states.async_all("binary_sensor")
            self.assertTrue(any(state.state == "off" for state in states))
        self.status = 200
        await coordinator.async_refresh()
        await self.hass.async_block_till_done()
        self.assertTrue(coordinator.last_update_success)
        self.assertTrue(any(state.state == "on" for state in self.hass.states.async_all("binary_sensor")))

    async def test_original_inaccurate_first_fix_then_improving_accuracy(self):
        self.raw[0][0][1][3] = 2000
        self.set_document()
        coordinator = await self.add_entry()
        self.assertEqual(self.tracker().attributes["gps_accuracy"],2000)
        expected_latitude = 0.5
        for accuracy,latitude,accepted in ((3000,1.1,False),(1500,1.2,True),(1000,1.3,True),(2000,1.4,False)):
            self.raw[0][0][1][2] += 1000
            self.raw[0][0][1][1][2] = latitude
            self.raw[0][0][1][3] = accuracy
            await self.refresh(coordinator)
            if accepted: expected_latitude = latitude
            self.assertEqual(self.tracker().attributes["latitude"],expected_latitude)
        self.raw[0][0][6][1] = "https://lh3.googleusercontent.com/updated-synthetic-picture"
        await self.refresh(coordinator)
        self.assertEqual(self.tracker().attributes["entity_picture"],self.raw[0][0][6][1])

    async def test_legacy_native_entry_migration_does_not_read_or_delete_cookies(self):
        from custom_components.google_maps import async_migrate_entry
        legacy=Path(self.temp.name)/"legacy-cookie-canary.txt"
        legacy.write_text("SYNTHETIC_LEGACY_COOKIE_CANARY")
        entry=ConfigEntry(version=3,minor_version=1,domain="google_maps",title=ACCOUNT,
            data={"cookies_file":str(legacy)},options={CONF_CREATE_ACCT_ENTITY:True,CONF_MAX_GPS_ACCURACY:1000,"scan_interval":60},
            source="user",unique_id=ACCOUNT,discovery_keys={},subentries_data=[],disabled_by=ConfigEntryDisabler.USER)
        await self.hass.config_entries.async_add(entry)
        self.assertTrue(await async_migrate_entry(self.hass,entry))
        self.assertEqual(entry.version,4)
        self.assertEqual(entry.unique_id,ACCOUNT)
        self.assertNotIn("cookies_file",entry.data)
        self.assertEqual(entry.data["data_token"],"")
        self.assertEqual(legacy.read_text(),"SYNTHETIC_LEGACY_COOKIE_CANARY")

    async def test_native_configuration_and_original_options_flow(self):
        result=await self.hass.config_entries.flow.async_init("google_maps",context={"source":"user"})
        self.assertEqual(result["step_id"],"source")
        result=await self.hass.config_entries.flow.async_configure(result["flow_id"],{"username":ACCOUNT,"endpoint":"http://127.0.0.1:8787","data_token":TOKEN})
        self.assertEqual(result["step_id"],"account_entity")
        result=await self.hass.config_entries.flow.async_configure(result["flow_id"],{CONF_CREATE_ACCT_ENTITY:False})
        self.assertEqual(result["step_id"],"max_gps_accuracy")
        result=await self.hass.config_entries.flow.async_configure(result["flow_id"],{CONF_MAX_GPS_ACCURACY:500})
        self.assertEqual(result["step_id"],"update_period")
        result=await self.hass.config_entries.flow.async_configure(result["flow_id"],{"scan_interval":{"seconds":60}})
        self.assertEqual(result["type"],"create_entry")
        self.assertNotIn("cookies_file",result["data"])
        self.assertEqual(result["options"][CONF_MAX_GPS_ACCURACY],500)


class JSONResult(unittest.TestResult):
    def __init__(self):
        super().__init__();self.details=[]
    def addError(self,test,err):
        super().addError(test,err);self.record(test,err)
    def addFailure(self,test,err):
        super().addFailure(test,err);self.record(test,err)
    def record(self,test,err):
        frames=traceback.extract_tb(err[2])
        self.details.append({"test":str(test),"type":err[0].__name__,"message":str(err[1]),"frames":[{"file":Path(f.filename).name,"line":f.lineno} for f in frames[-4:]]})

if __name__ == "__main__":
    import logging
    class Diagnostics(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                if record.exc_info:
                    error = record.exc_info
                    DIAGNOSTICS.append({"type":error[0].__name__, "message":str(error[1]),
                        "frames":[{"file":Path(f.filename).name,"line":f.lineno} for f in traceback.extract_tb(error[2])[-4:]]})
                else:
                    DIAGNOSTICS.append({"message":record.getMessage()[:500]})
    logging.getLogger().handlers = [Diagnostics()]
    logging.getLogger().setLevel(logging.ERROR)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativeRuntime)
    result=JSONResult();suite.run(result)
    report={"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"details":result.details}
    print(json.dumps(report,default=str))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(report,indent=2,default=str))
    sys.exit(not result.wasSuccessful())
