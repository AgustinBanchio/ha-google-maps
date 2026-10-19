# Tracker: original integration, external session

Status: IN_PROGRESS. Owner authorized implementation. Native source release: `86f69835e00fba2f9e619a5267cb62d4ee352d83`.

| Task | Status |
|---|---|
| 1 Upstream client and transport wrapper | DONE |
| 2 Scoped session data API | DONE |
| 3 Original HA source/auth adapter | DONE |
| 4 Actual HA equivalence/security tests and patch guard | DONE |
| 5 ARM64 release, authorized rollout and migration handoff | IN_PROGRESS |

Fresh evidence, 2026-10-19:

- Windows: 110 passed, 2 broker-specific skips, one existing Starlette warning.
- Five protected upstream modules and the vendored client match the audited baseline. Synthetic three-way upstream update exercise passes.
- Actual HA 2026.10.1: seven runtime scenarios pass, covering original configuration/options, account identity, names/pictures/attributes, accuracy/backwards time, restore, missing contacts, errors/recovery and legacy migration. Disposable HA image had no production config or network.
- GitHub Collector and Validate workflows pass at `86f6983`.
- ARM64 release and all five acceptance groups pass, including encrypted state compatibility, scoped API and operation without a broker. Release validation passes for exact clean source.
- Tested service image: `sha256:7ec36e9e72da239f6f5071d81076e957b37bd9b0a158bef67c27f2916c354baa`.
- Native ZIP SHA256: `274d9d9ece4b545a2983cbc0a753c35fd2492f16a399c47c309b3c190a29f3b4`.
- Account identity supplied privately by owner; stored only in ignored owner-only handoff storage.

Deployment evidence, 2026-10-19:

- The tested ARM64 image is running with the scoped API enabled. The real native client verified 4 shared people, 4 names/profile images and 5 valid coordinate records including the optional account observation. Its key was rejected by management; anonymous API access was rejected.
- Five existing MQTT tracker IDs were preserved. All three original containers and the broker matched baseline before HA installation.
- A deployment verification script used the wrong profile attribute name; the application was healthy, but the checker triggered rollback. The old untagged image ID was unavailable. The tested collector was resumed, the probe corrected, and all aggregate verification passed. A verified rollback image was rebuilt from exact previous source `f5a05b9` and retained under a separate tag; the new image is tagged too. No unresolved outage remains. Matching encrypted pre-update data is retained privately.
- New scoped key provisioned without reading existing credentials; encrypted owner handoff delivered to ignored owner-only local storage and its temporary decryption key removed.
- Owner explicitly approved installing our fork and restarting only HA. Hash-checked native ZIP installed in the existing persistent `/config` bind mount; no previous component existed. One targeted HA restart completed. HA identity/network/privileges unchanged; Matter Server, OTBR and broker untouched. Frontend HTTP 200.
- Real frontend opens the new external-session Google Maps flow. Owner signed into HA; account/address are populated, scoped key entry is pending privately. Never read or expose that password field.
- Normal HA Compose pull/recreation retains the component in `/config`; the separate service and private state are independent. Future HA API compatibility is limited to the tested version and must be checked on upgrades.

Exact next action: finish the supported native HA flow once the owner enters the key, verify real names/pictures/map and original options, privately review old-to-new Person/automation references, then switch only the collector to broker-free native mode if migration is accepted. Do not remove the broker or unrelated MQTT configuration. Push documentation/CI pin updates directly to owner main. See `docs/NATIVE_DEPLOYMENT_REVIEW.md`.

No existing Compose file, mount, privilege, Thread permission, firewall, SSH or host-service changes and no reboot. Operational reports, account identity and credentials remain private. Task 5 remains IN_PROGRESS until live native setup and migration verification are complete.
