# Native setup and migration

The source-preserving correction is implemented. Our native custom component is installed in HA's persistent configuration, and the tested separate service exposes its scoped loopback API. The original Google session/store were reused. Existing HA Compose, permissions, Matter Server and OTBR remain unchanged. HA completed one explicitly approved restart.

Use [native setup](NATIVE_SETUP.md). On the owner's Windows workstation, the new scoped data key and account identity are in ignored owner-only `.local/native-handoff/NATIVE-SETUP-PRIVATE.txt`. Keep the key private and enter it only in HA's Google Maps source form. Google cookies stay in the external service.

Native configuration and migration are complete. Five native trackers have names and coordinates; four shared-contact profile pictures load. Five People use their corresponding native tracker while their other trackers/settings remain intact. All 16 legacy MQTT entities are disabled, publishing is off, and the separate service runs `deploy/compose.session.yaml` without a mounted MQTT password. The broker remains running unchanged for rollback.

No indexed automation/script/scene references remained on legacy entities; seven available dashboard configurations had no legacy references. The default dashboard had no stored configuration. The live HA map contains all five People. The [active tracker](specs/current/2026-10-19-upstream-session-adapter/tracker.md) records evidence and maintenance actions. Optional broker/discovery removal requires separate applicable authorization.

Normal `docker compose pull` and `docker compose up -d` in the existing HA project preserve the component through its persistent `/config` mount. The separate service restarts automatically with Docker and retains its encrypted session. See the tested-version caveat and rollback in the native guide.
