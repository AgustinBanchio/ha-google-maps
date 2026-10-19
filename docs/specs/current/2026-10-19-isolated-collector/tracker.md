# Tracker: isolated Google Maps collector

Plan: [plan.md](plan.md). Updated: 2026-10-19.
Status: BLOCKED at Task 4.2 awaiting explicit persistent-deployment approval. Nine of ten tasks complete for implementation and automated acceptance; owner session/HA setup remains.

## Exact next action

Obtain explicit permission to start the two persistent services in the separate google-maps-collector Compose project and provision their new credentials. Automatic approval review rejected that action because it interpreted the owner's wording as preparation, not explicit production mutation. See docs/DEPLOYMENT_REVIEW.md for the concrete image, paths, ports, checks and rollback. Do not retry the rejected action indirectly.

After approval, recheck free ports and unchanged original three-container baseline, provision only the new private directory, start/recreate only the new project, and prepare the private owner handoff. The owner imports Google cookies through SSH/local UI and adds HA's MQTT integration. No existing stack/permission/service changes or reboot are authorized.

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
| 4.2 Authorized Pi acceptance | 4 | BLOCKED | 2026-10-19 |

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

## Current blocker

Automatic approval review rejected starting persistent collector/broker services and creating/delivering their credentials. It requires clearer explicit deployment authorization; the rejection was not bypassed. Production was not deployed, owner credentials were not provisioned, no Google session was imported and no Pi reboot occurred. An unused ephemeral owner-recipient key was generated only in an owner-only local directory for the approved encrypted handoff design.

Task 4.1 is DONE [9/10 tasks complete]; Task 4.2 remains BLOCKED on this exact approval and then owner-controlled Google/HA setup. The earlier missing Windows Docker engine is no longer the test blocker: disposable ARM64 testing ran on the Pi under the owner's continuation instruction.

## Preparation and implementation notes

Preparation reviewed all nine upstream modules, inspected selected Pi metadata read-only, created the public fork/checkout and restored desktop-session SSH transport. The owner instructed continuation on 2026-10-19; tasks were implemented sequentially using spec-build with local source review (no delegated agents). Review fixes covered warning-free cookie parsing, native loopback binding, ordered shutdown, nonblocking freshness views, login throttling races and fail-closed session validity. Exact dependencies and primary-source review are in docs/DEPENDENCIES.md; extraction deltas are in docs/UPSTREAM_PROVENANCE.md.

The Windows sandbox runner timed out on its pipe; auto-reviewed execution outside it worked. Development tooling, synthetic bootstrap files, build products and operational context remain ignored. No real credentials, contact/location data, raw host reports or infrastructure configuration were added to public files.

## Deployment preconditions

No Pi checkout, deployment, restart, reboot, real session import or HA configuration change occurred. Cloudflare routes/Access authentication and router forwarding remain unverified. Verify actual ports/mounts, preserve the original smart-home stack and obtain specific deployment authorization before Task 4.2. Full Pi reboot requires separate explicit authorization. The trusted-host limitation remains accepted.

## Verification record

See [verification.md](verification.md) for partial acceptance mapping. Preparation evidence remains in docs/PREPARATION_VERIFICATION.md. The specification acceptance checkboxes remain unchecked pending complete verification.

Follow-up status check, 2026-10-19: HEAD and remote main both remain at preparation commit 28b206b; implementation changes are uncommitted and unpushed. A fresh read-only desktop-helper SSH probe succeeded and returned ARM64 (aarch64) and Docker server 29.9.1. SSH access is working. This does not authorize starting test containers or deploying on the Pi; no remote service was changed. The Task 4.1 blocker is local Linux Docker availability/test completion, not SSH authentication.

Owner continuation 2026-10-19: authorized commit/push and continuation until ready for HA setup, including isolated new collector tests/deployment on the Pi. Existing Docker Compose, HA/Matter/OTBR permissions and services must remain unchanged. No reboot authorized. Exact next action: save/push a feature branch, run disposable ARM64 broker tests, finish restart/recreation evidence, then provision only the separate collector project. Real Google session import remains an owner action through the private UI.
