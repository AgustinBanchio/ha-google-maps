# Native setup and migration

The source-preserving correction is implemented. Our native custom component is installed in HA's persistent configuration, and the tested separate service exposes its scoped loopback API. The original Google session/store were reused. Existing HA Compose, permissions, Matter Server and OTBR remain unchanged. HA completed one explicitly approved restart.

Use [native setup](NATIVE_SETUP.md). On the owner's Windows workstation, the new scoped data key and account identity are in ignored owner-only `.local/native-handoff/NATIVE-SETUP-PRIVATE.txt`. Keep the key private and enter it only in HA's Google Maps source form. Google cookies stay in the external service.

Finish the original option steps, verify native names/pictures/map positions, then review People and automation references before retiring MQTT. The existing broker remains intact during migration. Exact live evidence and unfinished actions are recorded in the [active tracker](specs/current/2026-10-19-upstream-session-adapter/tracker.md).

Normal `docker compose pull` and `docker compose up -d` in the existing HA project preserve the component through its persistent `/config` mount. The separate service restarts automatically with Docker and retains its encrypted session. See the tested-version caveat and rollback in the native guide.
