# Tracker: original integration, external session

Status: COMPLETE. Owner authorized implementation. Native source release: `86f69835e00fba2f9e619a5267cb62d4ee352d83`.

## 2026-11-25 upstream 2.1.0 port

The owner requested the full upstream release with the fork's existing cookie handling. Implemented pinned `ae85b249b354c25c2994cd1458231039e1dc977f` with all new sensors, tracker battery compatibility, recorder exclusions, polling preference, options reload and metadata. The collector still owns cookies. Retained HA entry version 4, existing IDs, scoped data key, encrypted state format and diagnostics. Fixed sensor registry IDs containing hyphens and cleanup for disabled sensors.

Local verification: 11 actual HA scenarios passed, 134 Windows collector tests passed with two broker skips, and all 136 Linux broker tests passed. The deployed collector source wrote a synthetic session, 2.1.0 read it and persisted rotation, and the previous source reopened the updated state using the same keys. Local Docker could not execute ARM64. See the [audit and paired rollout/rollback procedure](../../../audits/2026-11-25-upstream-2.1.0/REVIEW.md).

Exact next action: verify the pinned source and packaging, push directly to owner main and check native ARM64 CI. Live deployment requires separate approval for a paired collector/component upgrade and a targeted HA restart. No Pi service changes were made.

## 2026-11-25 upstream status check

Upstream published [2.1.0](https://github.com/pnbruckner/ha-google-maps/releases/tag/2.1.0) on 9 November at `ae85b249b354c25c2994cd1458231039e1dc977f`. GitHub reports that upstream `main` matches the tag. It is two commits and 13 changed files ahead of our audited `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`. Reviewed the complete [merged #62 patch](https://github.com/pnbruckner/ha-google-maps/commit/338f975a282bda1cf5a7aca765f69418c619ae25) and tag's version bump. Dynamic polling [PR #52](https://github.com/pnbruckner/ha-google-maps/pull/52) remains open at the previously reviewed head.

- Prioritize moving tracker `battery_level` to `extra_state_attributes` under the same key. Our tracker still overrides the deprecated property, which [Home Assistant Core](https://github.com/home-assistant/core/blob/2026.10.1/homeassistant/components/device_tracker/entity.py) says will be unsupported in 2027.7. Preserve existing recorder behavior and tracker identities in the compatibility patch.
- Upstream now ships battery, address, GPS accuracy, last-seen and location-age sensors. Battery is enabled by default. The location sensors use raw observations and can differ from the filtered tracker. The new registry handling splits sensor IDs on every hyphen, which can truncate a hyphenated account ID after reload. Review sensor lifecycle and recorder effects before adopting these features.
- Upstream also raises its HA minimum to 2026.7, changes config flow reload handling and adds an explicit polling preference branch. Our tested HA 2026.10.1 coordinator already skips scheduled refreshes when polling is disabled. The embedded Maps client only changes its cached-property import and drops postponed annotations. Google requests, cookie handling and parsing are unchanged in that client diff. A full baseline advance would require pinning `propcache` for the standalone collector and coordinating the revision check on both sides of the API.

The protected-source guard passed for the five pinned modules and identical vendored client. This was a static assessment. No candidate runtime tests or live host checks were performed.

The owner subsequently requested the full release. The port and its rollout status are tracked above.

## 2026-11-03 upstream status check: COMPLETE

GitHub comparison reports upstream `main` identical to audited `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`; latest published release remains 2.0.3 (4 June 2026). New open maintainer PR #62 (30 October), reviewed at `7b77fd27cab1aa779269893320c738a0d3a85104`, contains a battery-level deprecation fix, recorder exclusions and HA 2026.7 minimum/metadata/typing changes. Its proposed separate sensors are not implemented. Older open PR #52 adds dynamic polling but needs finite/bounded interval validation and correct unavailable-state fallback before adoption. Full changed-file patches were inspected; neither PR was applied. Local protected-source guard passed for five modules and the identical vendored client. No runtime tests of either candidate or live host inspection occurred. See [assessment](../../../audits/2026-11-03-upstream-status/REVIEW.md).

Exact next action: retain the current release and recheck #62 when it changes or merges; perform a pinned, scoped compatibility port only if the owner requests implementation, following `docs/UPSTREAM_UPDATES.md`. No code port or deployment is pending from this check.


## 2026-10-20 diagnostics maintenance: COMPLETE

Owner renewed the session and requested logging. Supplied status reported credential_required with an approximate future cookie expiry; this establishes a source-authentication failure, not its underlying cause. No credential files or raw logs were read. A requested management tunnel opened successfully after an earlier read-only SSH attempt failed at the desktop agent.

Implemented maintenance checkpoint: transport reasons, independent last-source-failure metadata, 32-event persistent allowlisted history, isolated JSON logging, management UI with refresh, and a read-only metadata CLI exist. The original source/wire/authentication contracts remain unchanged. Local suite: 134 passed, 2 broker skips. Disposable Linux Docker broker suite: 136 passed. Source guard, synthetic upstream update and source metadata checks pass. Synthetic browser UI login/diagnostics/recovery display verified. Actual Requests Set-Cookie extraction and encrypted rotation continuity are tested. Broken logging streams cannot emit surrounding exception context; optional metadata write failures do not interrupt tracking. One existing Starlette warning remains.

Release acceptance tooling records the observed image architecture instead of a hardcoded arm64 label, and accepts an explicit test platform.

Release checkpoint: implementation and native ARM64 CI/recovery coverage are pushed directly to owner main (`b211f7c`, `ce0c2bf`). Local Docker cannot execute ARM64 (exec-format error); native ARM64 GitHub CI passes all six acceptance groups. Collector and Validate both pass at `ce0c2bf`, including Windows/Linux unit, both broker architectures and actual HA runtime. Synthetic browser refresh verified. Demo services/containers were removed.

Deployment evidence, 2026-10-20: owner explicitly approved the collector-only diagnostics rollout. Exact clean `ce0c2bf` was built on the Pi; all six acceptance groups passed against the actual ARM64 image and release packaging validation passed. The first isolated acceptance attempt found a missing synthetic fixture image before production changed; building that fixture resolved the test prerequisite without changing release source. Only the collector was replaced, reusing the existing encrypted session and keys. Its image is `sha256:fdbef26546ac1d39d6449d30653daeb28323fb0f456451826d7f0b9e41565151`. Prior image/environment and encrypted-state backup are retained for rollback. UID, read-only root, restart policy and sole loopback port match the review. Four protected containers (HA, broker, Matter Server and OTBR) match their baseline, including identity/start/restart metadata; no HA restart, Compose permission change or reboot occurred.

Fresh verification: 24 diagnostics tests passed with one existing Starlette warning; protected upstream guard and source metadata checks passed. Management diagnostics UI and metadata-only CLI are available. A real native poll succeeded after replacement, with two successfully saved cookie changes and no recorded source failure. A separate CLI process read that persisted event; no credential file or raw production log was inspected. Requested local tunnel returns HTTP 200. See [verification](verification.md) and [deployment review](../../../DIAGNOSTICS_DEPLOYMENT_REVIEW.md).

Exact next maintenance action: routine use. Refresh the collector page and sign in again after replacement to view Diagnostics; use Refresh status if the issue recurs. Preserve rollback artifacts. Historical pre-installation rejection cannot be reconstructed; future diagnostics report the observed failure category, not Google's undisclosed internal reason. No required diagnostics implementation or deployment action remains.

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
