# Tracker: isolated Google Maps collector

Plan: [plan.md](plan.md). Updated: 2026-10-19.
Status: READY_FOR_OWNER_SETUP. The isolated production collector/broker is deployed and verified; real Google import and HA MQTT/People setup remain owner actions. Nine implementation tasks are DONE; Task 4.2 retains only live owner acceptance and the separately unauthorized reboot check.

## Exact next action

Follow docs/NEXT_STEPS.md: open the desktop SSH tunnel, read the owner-only local credentials file, import the Google session in the authenticated loopback UI, then add HA's standard MQTT integration and link trackers to People. Do not upload credentials in chat or configure the original cookie-based HA custom integration for this collector.

After owner setup, verify real polling, discovery and Person behavior. A full Pi reboot remains a separate explicit authorization; no reboot or existing stack restart is necessary to add MQTT. All persistent deployment approval requirements were satisfied by the owner's explicit collector/broker-only approval.

## Tasks

| Task | Phase | Status | Updated |
|---|---|---|---|
| 1.1 Package and reproducible dependencies | 1 | DONE | 2026-10-19 |
| 1.2 Hardened Google transport | 1 | DONE | 2026-10-19 |
| 2.1 Encrypted durable store | 2 | DONE | 2026-10-19 |
| 2.2 Polling and session lifecycle | 2 | DONE | 2026-10-19 |
| 2.3 MQTT discovery and freshness | 2 | DONE | 2026-10-19 |
| 2.4 Authenticated management UI | 2 | DONE | 2026-10-19 |
| 3.1 Container broker and bootstrap | 3 | DONE | 2026-10-19 |
| 3.2 Setup recovery and Person docs | 3 | DONE | 2026-10-19 |
| 4.1 Privacy and restart suite | 4 | DONE | 2026-10-19 |
| 4.2 Authorized Pi acceptance | 4 | IN_PROGRESS | 2026-10-19 |

Status values: PENDING, IN_PROGRESS, DONE, FAILED, BLOCKED. DONE for packaging/docs records preparation checks, not executed container/host acceptance.

## Current verification evidence

2026-10-19 continuation: implementation committed/pushed on feature/isolated-collector, draft PR https://github.com/AgustinBanchio/ha-google-maps/pull/1. Source used for the built release is ce2f19ecf99c2dc90d54a8a54e2a3ce30b27bc01. No pending collector code or tests are inferred from this report.

- Fresh Windows suite: 74 passed, 2 broker tests skipped, one Starlette test-client deprecation warning.
- Fresh disposable Pi ARM64 suite: 76 passed, including both real Mosquitto ACL/reconnect tests; no skips. The Linux ownership/durability paths executed there.
- Production-image host harness: actual broker restart and both-container recreation preserved encrypted session/key, stable contact identity and source timestamp; invalid replacement, independent stale TTL, non-root UID 10001 and container log canary checks passed. Uses only an explicit synthetic transport; never contacted Google with real or synthetic cookies.
- Docker runtime testing caught unquoted tmpfs option lists; those are fixed in the new Compose files. The existing Compose stack was untouched.
- Image sha256:e543a5ea5d8fe2597468d546d8fb01a24bc7f2b548349a8c41fb60d67084abd3 is built locally on ARM64, retained by immutable image ID. Source revision, dependency lock hash, wheel hash and acceptance evidence are retained in the private release record. Full tools/validate_release.py passed (release_metadata_passed). No registry publication is required for this local image; this is distinct from a registry RepoDigest.
- GitHub HACS, hassfest, Linux/Windows unit and broker jobs passed. Fork issues/topics were enabled for HACS metadata validation. A draft mistakenly targeting upstream was immediately closed and replaced with the fork PR.
- Native UI login/status/logout smoke and streaming/concurrency/privacy regression checks passed in the earlier implementation session; fresh automated suite reruns cover their code. uv lock/build/source artifact checks pass. Point-in-time runtime pip-audit reported no known vulnerabilities in the preceding session; not repeated as a new scan claim.
- Selected metadata of all three original containers is identical before/after ARM64 testing: IDs, start times, restart counts, status, privileges and network/Compose service metadata. No existing service was restarted or reconfigured. Disposable test containers were removed.
- Upstream runtime remains identical to b2132123d46c47e5761d5d91cc08ca6b712fe6c1. The upstream remote remains intact. Private files/artifacts/tooling remain ignored.

## Production deployment evidence

Explicit owner approval superseded the earlier automatic-review block. Production started successfully with the reviewed immutable ARM64 image; the new collector and Mosquitto broker are the only added services. One-time new credentials were encrypted for transfer; the admin password is not persisted in plaintext on the Pi. The owner-only workstation handoff is .local/owner-handoff/SETUP-PRIVATE.txt; its contents never entered chat, Git, SSH InputText/arguments or tool output. The ephemeral recipient private key was removed after decryption.

Fresh post-deployment checks passed:

- Collector healthcheck and unauthenticated status rejection (HTTP 401).
- Exact loopback host bindings for ports 8787 and 1883; users 10001:10001 / 1883:1883; read-only roots; dropped capabilities; no privileged/host network/Docker socket/HA config mount.
- Targeted recreation of only the new collector/broker preserved the provisioned key.
- Actual HA-subscriber MQTT authentication, retained session discovery, OFF/credential-required state and denied unrelated writes. A final probe also passed HA's homeassistant/# discovery subscription and homeassistant/status birth publish.
- Original three-container baseline remained identical: container IDs, start times, restart counts, running status, privilege/network/project/service metadata. Existing Compose files, HA/Matter/OTBR permissions and services were untouched.
- No Google session imported, no HA configuration changed, no reboot performed. Live location/session/Person acceptance is still pending owner input.

Task 4.2 remains IN_PROGRESS only for owner-controlled real-session/HA acceptance and any separately authorized reboot. The requested ready-to-add-to-HA milestone is reached. Owner requests direct pushes with no PR workflow; PR #1 was closed, and the verified work and handoff are committed and pushed directly to main.

## Preparation and implementation notes

Preparation reviewed all nine upstream modules, inspected selected Pi metadata read-only, created the public fork/checkout and restored desktop-session SSH transport. The owner instructed continuation on 2026-10-19; tasks were implemented sequentially using spec-build with local source review (no delegated agents). Review fixes covered warning-free cookie parsing, native loopback binding, ordered shutdown, nonblocking freshness views, login throttling races and fail-closed session validity. Exact dependencies and primary-source review are in docs/DEPENDENCIES.md; extraction deltas are in docs/UPSTREAM_PROVENANCE.md.

The Windows sandbox runner timed out on its pipe; auto-reviewed execution outside it worked. Development tooling, synthetic bootstrap files, build products and operational context remain ignored. No real credentials, contact/location data, raw host reports or infrastructure configuration were added to public files.

## Remaining live acceptance

A separate Pi source checkout and the approved collector/broker project now exist. Relevant Cloudflare/Access policies and router forwarding were not independently established; no tunnel service/routes were modified and both new ports are loopback-only. Confirm relevant private-access policies before importing a real Google session. The trusted-host limitation remains accepted. Any full Pi reboot or existing smart-home service changes require separate explicit authorization.

## Verification record

See [verification.md](verification.md) for partial acceptance mapping. Preparation evidence remains in docs/PREPARATION_VERIFICATION.md. The specification acceptance checkboxes remain unchecked pending complete verification.

Follow-up status check, 2026-10-19: HEAD and remote main both remain at preparation commit 28b206b; implementation changes are uncommitted and unpushed. A fresh read-only desktop-helper SSH probe succeeded and returned ARM64 (aarch64) and Docker server 29.9.1. SSH access is working. This does not authorize starting test containers or deploying on the Pi; no remote service was changed. The Task 4.1 blocker is local Linux Docker availability/test completion, not SSH authentication.

Owner continuation 2026-10-19: authorized commit/push and continuation until ready for HA setup, including isolated new collector tests/deployment on the Pi. Existing Docker Compose, HA/Matter/OTBR permissions and services must remain unchanged. No reboot authorized. Exact next action: save/push a feature branch, run disposable ARM64 broker tests, finish restart/recreation evidence, then provision only the separate collector project. Real Google session import remains an owner action through the private UI.

Explicit owner approval received: deploy/start only the separate collector and MQTT broker, including new private credentials and loopback ports 8787/1883. Existing HA/Matter/OTBR Compose, permissions and services remain unchanged; no reboot. Owner also requests direct pushes in this personal repository, with no PR workflow; PR #1 is being closed. Exact next action: execute the reviewed provision/start and selected post-deployment checks.

Owner setup follow-up: the tunnel helper fell back to an SSH password in T3's Session 0 terminal. A fresh desktop-session key-only probe passed. Local fix completed: use a limited interactive desktop worker for the tunnel, disable password/keyboard-interactive fallback, retain host-key checking/no forwarding, and clean up its temporary task/process. No Pi SSH/service/Compose settings change. Evidence: PowerShell syntax passed; a Session 0 launch authenticated through the desktop key agent and the collector page returned HTTP 200. A final bounded 20-second run completed with exit 0 and removed both its listener and temporary task. Password fallback is disabled. The fix and Chrome Netscape export guide are committed/pushed directly to main. Exact next action: owner reruns the tunnel and follows docs/COOKIE_IMPORT.md to upload the Google session privately.

GitHub safety follow-up: verified the mistakenly created upstream draft #61 and fork PR #1 are both CLOSED with mergedAt null. GitHub CLI default and Git remote.pushDefault are now explicitly set to the owner fork/origin; no further PR workflow is used.

## Names and map usability correction (IN_PROGRESS)

Owner clarified that Google display names and locations are intended HA data; only authentication material requires isolation. The original integration used Google Maps <full_name>, GPS attributes and optional picture/nickname. The initial collector discarded display names and hid trackers, which made identification/map use poor. Read-only aggregate broker inspection confirms four fresh GPS payloads with coordinates and four hidden trackers; no real name/location values were returned.

Exact next action: preserve Google display names for private HA discovery, keep hashed unique IDs/topics unchanged, make GPS trackers visible by default, test old encrypted-state migration and name-only updates without GPS republishing, then build/test and update only the collector image. Existing HA/Matter/OTBR containers, permissions and services remain untouched. The owner explicitly requested names/locations in HA; credentials remain excluded from HA/MQTT/logs/public source.


Owner expanded this correction to all original integration data. Implemented full name, nickname, Google profile image, address, country_code, last_seen, battery level/charging and optional account-holder GPS. GPS snapshot attributes preserve observation time; current Maps details metadata updates independently. Frozen upstream parser comparison and old encrypted-store migration pass. Fresh Windows result: 85 passed, 2 broker-dependent tests skipped; one existing Starlette test-client deprecation warning. Existing HA hidden flags persist under HA's registry API, so document the one-time Visible toggle. Exact next action: review diff, push directly to owner main, run disposable ARM64 suite/recovery, then update only collector with old-image/env rollback and verify selected original-service baseline plus aggregate MQTT field completeness.
