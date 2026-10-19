# Tracker: isolated Google Maps collector

Plan: [plan.md](plan.md). Updated: 2026-10-19.
Status: IN_PROGRESS at Task 4.1. Eight of ten tasks complete for local implementation/preparation. Feature acceptance is not complete.

## Exact next action

Provide a working local Linux Docker engine or an explicitly authorized disposable development environment. Do not use the Pi as an implicit deployment/test target. Then run:

```sh
docker compose -f deploy/compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
```

Review/fix the two presently unexecuted broker tests. Extend verification to actual broker restart, collector/broker container recreation, mounted-secret ownership and linux/arm64 startup. The current broker tests cover ACL denial, delivery and subscriber reconnect/retained timestamp; they do not yet exercise actual broker/container recreation. Produce a clean source revision, built collector image digest and release record, then run tools/validate_release.py without --source-only. Only after Task 4.1 passes prepare the concrete host-specific deployment review and request any needed authorization for Task 4.2.

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
| 4.1 Privacy and restart suite | 4 | IN_PROGRESS | 2026-10-19 |
| 4.2 Authorized Pi acceptance | 4 | PENDING | 2026-10-19 |

Status values: PENDING, IN_PROGRESS, DONE, FAILED, BLOCKED. DONE for packaging/docs records preparation checks, not executed container/host acceptance.

## Current verification evidence

Final local execution on Windows with CPython 3.13.16 and uv 0.13.1:

- uv sync --frozen and uv lock --check passed; CLI --help/--version passed without credentials.
- uv run --frozen pytest -q: **73 passed, 2 skipped**, one Starlette test-client deprecation warning. The skipped tests require BROKER_TEST_HOST for the disposable broker.
- Google transport: intercepted actual Requests construction, TLS, proxy/netrc isolation, redirect rejection, exact cookie domains, parser bounds/types, synthetic locations and fixed errors.
- Store: unique-nonce AES-GCM, wrong/missing keys, corruption/version/tampering, interrupted replacement preserving the old file, no plaintext credential canary and restart reconstruction. POSIX directory fsync/ownership branches are implemented but unexecuted here.
- Lifecycle: genuine newer fixes, separate battery changes, stale TTL, serialized poll/import, rejected replacement, rotation, network/auth/parser/store recovery, cold restart and a fresh interpreter recovering the same source timestamp. Slow polling cannot delay freshness checks. Revocation remains credential-required after a later network error; startup network failure cannot validate a stored session.
- Management: scrypt verifier, private sessions, expiry/restart/logout, CSRF/Host/Origin, throttling including concurrent slow-body attempts, malformed/oversized input and an ASGI streaming test stopping at the first over-limit chunk.
- MQTT: intercepted discovery/state schema, hidden enabled GPS trackers, opaque IDs, battery isolation, LWT, availability and exact birth subscription. No actual HA acceptance is claimed.
- Bootstrap: synthetic first/repeat/partial/interrupted provisioning and fixed CLI startup errors. Native execution defaults to loopback; Compose publishes only loopback.
- Production and test docker compose config --quiet passed with synthetic bootstrap files. Python, uv and Mosquitto registry manifests were resolved to pinned digests; an ARM64 manifest exists, but startup was not tested.
- uv build produced wheel and source archive. tools/validate_release.py --source-only --wheel ... passed. Build context/artifact allowlists exclude private operational files and synthetic test credentials from production artifacts.
- pip-audit 2.10.1 against the complete exported frozen runtime requirements reported **No known vulnerabilities found** on 2026-10-19. This is a point-in-time advisory scan, not proof of absence of vulnerabilities.
- Native browser smoke: login page rendered, synthetic admin login/status/logout succeeded via T3 preview. No Google cookies were imported and no live Google request was made. The temporary local process/tab were stopped/closed.
- git diff --check passed. custom_components/ remains identical to upstream b2132123d46c47e5761d5d91cc08ca6b712fe6c1; the upstream remote is retained.

Full release validation intentionally returns release_validation_incomplete: there is no clean release revision/image record, built collector image digest or ARM64/container recovery evidence. CI definitions exist but have not been run on GitHub in this session. Changes remain uncommitted.

## Blocker evidence and remaining work

The attempted disposable Compose suite failed before starting containers:

> failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine ... The system cannot find the file specified.

Docker Desktop's Linux engine is unavailable. No engine/service was started or modified. Task 4.1 is partial: native privacy/process reconstruction checks exist and pass; the broker harness exists but has not executed; actual broker restart/container recreation and ARM64 acceptance still require implementation/execution in the working environment. Do not equate the process-reconstruction test with container or Pi reboot recovery.

## Preparation and implementation notes

Preparation reviewed all nine upstream modules, inspected selected Pi metadata read-only, created the public fork/checkout and restored desktop-session SSH transport. The owner instructed continuation on 2026-10-19; tasks were implemented sequentially using spec-build with local source review (no delegated agents). Review fixes covered warning-free cookie parsing, native loopback binding, ordered shutdown, nonblocking freshness views, login throttling races and fail-closed session validity. Exact dependencies and primary-source review are in docs/DEPENDENCIES.md; extraction deltas are in docs/UPSTREAM_PROVENANCE.md.

The Windows sandbox runner timed out on its pipe; auto-reviewed execution outside it worked. Development tooling, synthetic bootstrap files, build products and operational context remain ignored. No real credentials, contact/location data, raw host reports or infrastructure configuration were added to public files.

## Deployment preconditions

No Pi checkout, deployment, restart, reboot, real session import or HA configuration change occurred. Cloudflare routes/Access authentication and router forwarding remain unverified. Verify actual ports/mounts, preserve the original smart-home stack and obtain specific deployment authorization before Task 4.2. Full Pi reboot requires separate explicit authorization. The trusted-host limitation remains accepted.

## Verification record

See [verification.md](verification.md) for partial acceptance mapping. Preparation evidence remains in docs/PREPARATION_VERIFICATION.md. The specification acceptance checkboxes remain unchecked pending complete verification.

Follow-up status check, 2026-10-19: HEAD and remote main both remain at preparation commit 28b206b; implementation changes are uncommitted and unpushed. A fresh read-only desktop-helper SSH probe succeeded and returned ARM64 (aarch64) and Docker server 29.9.1. SSH access is working. This does not authorize starting test containers or deploying on the Pi; no remote service was changed. The Task 4.1 blocker is local Linux Docker availability/test completion, not SSH authentication.

Owner continuation 2026-10-19: authorized commit/push and continuation until ready for HA setup, including isolated new collector tests/deployment on the Pi. Existing Docker Compose, HA/Matter/OTBR permissions and services must remain unchanged. No reboot authorized. Exact next action: save/push a feature branch, run disposable ARM64 broker tests, finish restart/recreation evidence, then provision only the separate collector project. Real Google session import remains an owner action through the private UI.
