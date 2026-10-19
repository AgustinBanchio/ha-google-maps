# Tracker: original integration, external session

Status: COMPLETE. Owner authorized implementation. Native source release: `86f69835e00fba2f9e619a5267cb62d4ee352d83`.

| Task | Status |
|---|---|
| 1 Upstream client and transport wrapper | DONE |
| 2 Scoped session data API | DONE |
| 3 Original HA source/auth adapter | DONE |
| 4 Actual HA equivalence/security tests and patch guard | DONE |
| 5 ARM64 release, authorized rollout and migration handoff | DONE |

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
- Real frontend opens the new external-session Google Maps flow. Owner signed into HA and entered the scoped key privately. The supported flow completed with the original account-holder option enabled, maximum accuracy 1000 metres and update period 60 seconds. The key was never read from the form or printed.
- Normal HA Compose pull/recreation retains the component in `/config`; the separate service and private state are independent. Future HA API compatibility is limited to the tested version and must be checked on upgrades.

Final live verification:

- Six native entities: five named trackers with coordinates and connectivity sensor on. Four shared-contact pictures successfully load in the browser; account picture/battery omissions follow upstream. HA map renders all five People.
- Exact Google identity/hash mapping matched all five legacy trackers without ambiguity. Updated five People through supported HA API; preserved their other trackers, names and user associations. All five use native trackers as their current source.
- HA indexed reference checks found no remaining references on 16 legacy entities. Seven available dashboard configurations had no legacy references; the default dashboard had no stored configuration. No direct dashboard rewrite was needed.
- Disabled all 16 legacy entities through supported registry API, with private before/after snapshots for rollback. No `.storage` edits.
- Switched only the collector to `deploy/compose.session.yaml`: legacy polling/publishing off, no MQTT credential mounted, existing encrypted session reused. Scoped native API and HA connectivity remain healthy. Broker, Matter Server and OTBR unchanged; HA had no further restart. No legacy entity states remain active.
- Collector and Validate CI both pass at documentation/immutable HA-image-pin commit `d609978`; application source and installed package remain tested release `86f6983`.
- Final selected-metadata check confirms all 12 installed files match the tested ZIP, native service is running with `unless-stopped`, its sole API port is loopback-only, and the HA component uses persistent configuration storage. The original permissions and other services remain preserved; HA frontend is healthy and a verified rollback image is retained. Final source guard, synthetic upstream update and release source metadata checks pass. No private account identity appears in tracked files.

Exact next action: routine owner use. Keep release images, encrypted-state backup, private migration snapshots and disabled legacy entities during rollback retention. Broker/discovery removal is optional and needs applicable authorization; do not remove unrelated MQTT configuration. Audit requested upstream updates using `docs/UPSTREAM_UPDATES.md`. Future HA upgrades retain installation through persistent `/config` but require version compatibility checks. No required implementation or migration action remains.

No existing Compose file, mount, privilege, Thread permission, firewall, SSH or host-service changes and no reboot. Operational reports, account identity and credentials remain private. One explicitly approved targeted HA restart was performed.
