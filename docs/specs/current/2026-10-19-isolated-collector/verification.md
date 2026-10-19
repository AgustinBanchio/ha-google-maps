# Verification: isolated collector

19 October 2026. Verdict: PARTIAL for end-to-end feature acceptance; automated implementation/release verification PASS. Persistent deployment is approved, running and verified. Google import and HA setup remain owner actions.

| Criterion | Evidence | Verdict |
|---|---|---|
| AC1 Isolated personal-session collector | deploy/Dockerfile USER 10001; production-image ARM64 startup and privacy tests pass | PARTIAL: real personal-session import remains |
| AC2 Restricted HTTPS origin | google_maps.py fixed URL, TLS, redirect rejection/filtering; test_google_maps.py intercepted Requests paths pass | PASS for automated transport boundary; live compatibility unverified |
| AC3 Encrypted persistent jar | store.py AES-GCM/atomic fsync; store tests plus actual container recreation/key identity pass | PASS with synthetic credentials |
| AC4 Validate-before-replace UI | web.py upload + service.py serialized commit; failed replacement in actual production-image harness passes | PASS with synthetic transport |
| AC5 Management boundaries | test_web.py auth, CSRF/Host/Origin, concurrency throttle and ASGI streaming bound; native UI smoke | PASS |
| AC6 Revocation/recovery | test_service.py auth/network/rotation/restart validity; invalid replacement in container harness | PASS for synthetic lifecycle; real revocation unverified |
| AC7 MQTT and People | real Mosquitto discovery/ACL/reconnect tests; production-image broker restart and recreation preserve identity | PARTIAL: actual HA discovery/Person linkage remains |
| AC8 Source freshness | same/older/battery-only unit checks; source timestamp after actual recreation; live broker stale availability check | PASS for collector; HA selection during retained replay remains an operational limit |
| AC9 Restart and reboot | interrupted writes, new interpreter, actual broker restart and both-container recreation pass | PARTIAL: full Pi reboot deliberately not authorized/executed |
| AC10 Compose/ACL isolation | actual ARM64 UID/mount startup, real ACL denial tests, separate test project; existing three-container metadata unchanged | PASS for tested image/config; persistent deployment passed |
| AC11 Canary privacy | native privacy/store/UI/MQTT/wheel checks; production-image container log canary scan | PASS for synthetic automated scope |
| AC12 Reproducibility | hash-locked distributions, pinned bases, clean source ce2f19e, immutable locally built image and wheel hash; full release validator passed | PASS; no registry image publication or automatic upstream update |

Fresh commands/results: Windows pytest 74 passed / 2 broker skips; Pi ARM64 Compose pytest 76 passed / no skips; tools/acceptance_test.py completed all production-image recovery/privacy assertions; tools/validate_release.py returned release_metadata_passed. GitHub Linux/Windows unit, broker, HACS and hassfest jobs passed. Detailed private evidence is retained outside Git.

Release source: ce2f19ecf99c2dc90d54a8a54e2a3ce30b27bc01. Built ARM64 image identity: sha256:e543a5ea5d8fe2597468d546d8fb01a24bc7f2b548349a8c41fb60d67084abd3. This local Docker content identity is not a registry RepoDigest. The release record retains lock/wheel hashes and the selected image metadata.

Fresh scope audit: no existing Compose/privilege/network/service changes; all three original container IDs/start times/restart counts/status and selected configuration fields unchanged. After explicit approval, private provisioning and production start/recreation passed. Both new ports are loopback-only; actual broker subscriber authentication, retained discovery, HA wildcard discovery/birth publishing and denied unrelated writes passed. The original three-container baseline remained identical. No real credential or owner location appears in public files. No reboot or HA auth/log/config inspection occurred.

Remaining work: owner imports the Google session and configures HA MQTT/People; then record actual live polling/discovery/Person evidence. Full Pi reboot remains a separate optional authorization. Trusted-host and undocumented Google API limits remain; HA's own GPS-source update rules are not overridden.
