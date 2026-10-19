# Verification: isolated collector

Scope correction: the following results verify the deployed MQTT implementation and selected comparisons only. They do not establish complete equivalence to the original HA integration. The owner requires the source-preserving architecture described in docs/COURSE_CORRECTION.md; its adapter/API and HA-level equivalence tests do not exist yet.

19 October 2026. Upstream-data/behaviour correction: implementation, ARM64 recovery, release validation and live collector deployment PASS. End-to-end acceptance remains PARTIAL only for the owner's HA map/Person UI check and the separately unauthorized full Pi reboot.

| Criterion | Fresh evidence | Verdict |
|---|---|---|
| AC1 Isolated personal-session collector | deploy/Dockerfile runs as 10001; live session reused after collector replacement; five locations published | PASS within trusted-host boundary |
| AC2 Restricted HTTPS origin | google_maps.py:148 and transport tests; real poll succeeds through production collector | PASS |
| AC3 Encrypted durable session | store.py:47 tests, old-store migration test_service.py:186, synthetic container recreation, live credential reuse | PASS |
| AC4 Validate-before-replace | serialized service.py:75, web upload tests and rejected synthetic replacement in ARM64 harness | PASS |
| AC5 Management boundaries | web auth/CSRF/origin/streaming tests; live unauthenticated status returns 401 | PASS |
| AC6 Revocation/recovery | synthetic auth/network/rotation/replacement checks; cached locations remain while connectivity reports failure | PASS for tested lifecycle; real revocation not forced |
| AC7 Full upstream data and discovery | frozen upstream parser comparison test_google_maps.py:125; mqtt.py:37; live five named trackers and complete location schemas, four profile images, original IDs preserved | PASS for collector/MQTT; owner confirms HA map/Person UI |
| AC8 Original tracking behaviour | service.py:75/:159; test_service.py:226 quality cases, :241 persistent three-minute missing grace, :259 stationary/network retention; metadata preserves source last_seen | PASS; HA last_updated may change on attribute updates, as upstream |
| AC9 Restart/reboot | interrupted writes, new interpreter, actual ARM64 broker restart and both-container recreation; live old session migration | PARTIAL: full Pi reboot not authorized/executed |
| AC10 Compose/ACL isolation | ARM64 broker/ACL suite; live non-root/read-only/capability checks and loopback services; broker and original three-container baseline unchanged | PASS |
| AC11 Credential privacy | Google/UI/MQTT/encrypted-store/wheel canaries and synthetic harness log scan; selected live checks return only aggregate metadata | PASS for automated scope |
| AC12 Release provenance | clean c2be4af source, immutable ARM64 image, locked dependencies/wheel hash, full release validator | PASS |

Fresh local command: collector/.venv/Scripts/python.exe -m pytest -q collector/tests — 96 passed, 2 broker-dependent skips, one existing Starlette test-client deprecation warning. The disposable ARM64 Compose suite passed, including broker tests. tools/acceptance_test.py passed its four grouped recovery/privacy checks, including new field/discovery assertions. tools/validate_release.py passed. GitHub Collector (Linux, Windows, broker) and Validate workflows passed at c2be4af.

Deployed source: c2be4af5a342f9d4f357bd34ac18a5995cada1da. ARM64 image: sha256:d9788abc10c012248e1d612494c2aa1091dd3817639933422dabfe77d9036c6c. This is a local immutable image identity, not a registry RepoDigest. The private release record retains dependency/wheel hashes and recovery evidence.

Live aggregate checks: five trackers, five Google Maps names, five visible-by-default discovery configs, five location messages with all upstream attribute keys, five details payloads and four profile images. The fifth tracker is the optional account holder, whose Google record lacks shared-contact profile/battery fields. The real session remains ready; existing four tracker IDs are preserved. No actual names, coordinates, addresses, cookie values or credential file contents were returned or committed.

Deployment replaced only collector, with a private encrypted-state backup and old-image/env rollback. The production broker and all three original containers retained identical selected IDs/start times/restart counts/status/privilege/network/project metadata. Existing HA/Matter/OTBR Compose files and permissions were untouched. No reboot, HA auth/storage/log inspection or new credential provisioning occurred.

HA preserves existing entity registry Hidden settings when discovery defaults change. Owner action: open each existing Maps location entity's settings gear, enable Visible and save, then inspect map/Person linkage. New trackers default visible. Coordinates and last_seen are attributes; Home/Away remains the normal zone state. See docs/SETUP.md. Do not delete/re-add MQTT or change tracker IDs.

The MQTT adapter has different setup from the original HA custom integration. It preserves the reviewed tracking/data semantics; no claim is made that every HA frontend/registry/reconnect timing detail is identical. Trusted host administrators remain able to access credentials, and Google's endpoint remains undocumented. Full Pi reboot and any existing-stack changes require separate authorization.


Picture follow-up, 19 October: HA filters entity_picture out of JSON extra attributes; the preceding report proved transport data presence rather than frontend rendering. Corrected tracker discovery now uses the supported entity_picture field and resends discovery on image change/removal. Regression tests preserve IDs and source timestamps. Fresh Windows 97 passed/2 broker skips, ARM64 suite and four grouped recovery checks, release validation and GitHub checks pass at f5a05b9. Deployed image sha256:feda30345cf8c8f73ec9ac78f30ea5c167382e3d2890fc5eaa4dad4c6f3031ce. Live retained discovery has four picture URLs matching the four shared-contact profiles; the account-holder tracker has none. Credentials/IDs and production broker/original-container baselines are unchanged. Frontend image rendering remains an owner check. Device registry photos and HA Person photo assignment are separate from tracker photos, as in the original integration. See [HA MQTT attribute filtering and discovery setup](https://github.com/home-assistant/core/blob/2026.10.1/homeassistant/components/mqtt/entity.py) and [common discovery schema](https://github.com/home-assistant/core/blob/2026.10.1/homeassistant/components/mqtt/schemas.py).
