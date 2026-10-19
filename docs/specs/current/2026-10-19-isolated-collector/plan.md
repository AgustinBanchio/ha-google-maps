# Isolated Google Maps collector: implementation plan

Spec: [spec.md](spec.md). Source of progress: [tracker.md](tracker.md).

This plan extracts the pinned upstream client into a standalone collector, adds credential handling and MQTT, then packages it separately from the existing smart-home stack. All tasks are sequential to avoid dependency and shared-file conflicts. No runtime implementation is included in the preparation commit.

## Phase 1: Foundation [sequential]

### Task 1.1: Scaffold a reproducible collector package
Goal: establish the Python package, exact reviewed dependencies and test tooling.
Files: collector/pyproject.toml, collector/uv.lock, collector/src/google_maps_collector/__init__.py, collector/src/google_maps_collector/__main__.py, collector/src/google_maps_collector/config.py, collector/tests/conftest.py, .github/workflows/collector.yml.
Changes: use Python 3.13, src layout and the runtime/test dependencies named in the spec; check primary release/security sources before choosing exact supported pins; commit uv.lock hashes. Define typed configuration and bounded polling/freshness/upload settings, with secret file paths rather than secret values. Add CLI --help/--version and CI using uv sync --frozen. Never log configuration secret values.
Tests: from collector/, run uv lock --check and uv run python -m google_maps_collector --help; both succeed without network credentials.
Completion: frozen installs and CLI work on supported development platforms; versions and rationale recorded in docs/DEPENDENCIES.md.
Suggested commit: build: scaffold pinned standalone collector.

### Task 1.2: Extract and harden the Google transport
Depends on: 1.1.
Files: collector/src/google_maps_collector/google_maps.py, collector/tests/test_google_maps.py, collector/tests/fixtures/google_response.json, docs/UPSTREAM_PROVENANCE.md.
Changes: derive the client from the audited gm_loc_sharing.py, retain parser provenance, inject transport for tests, validate the exact Google HTTPS origin, reject redirects and unrelated cookie domains, retain TLS verification and sanitize exceptions. Do not copy raw-response logging.
Tests: uv run pytest -q tests/test_google_maps.py; fixtures verify contact IDs/coordinates/timestamps, malformed data, invalid session, unexpected redirects and absence of credential canaries in error text.
Completion: every outbound request and authentication failure path has evidence; no generic URL input exists.
Suggested commit: feat: extract hardened Google Maps client.

## Phase 2: Core implementation [sequential]

### Task 2.1: Add encrypted durable credential storage
Depends on: 1.2.
Files: collector/src/google_maps_collector/store.py, collector/tests/test_store.py.
Changes: implement the versioned AES-GCM store and pre-provisioned key contract; atomic durable replacement, response-cookie rotation, concurrent access serialization and explicit missing-key/tamper handling. Never create a replacement key silently.
Tests: uv run pytest -q tests/test_store.py; cover roundtrip, wrong key, tamper, interrupted replacement, missing store, format version and no plaintext canary bytes on disk.
Completion: invalid writes preserve the previous store and normal reconstruction reuses credentials.
Suggested commit: feat: persist sessions in an authenticated encrypted store.

### Task 2.2: Implement polling and session lifecycle
Depends on: 2.1.
Files: collector/src/google_maps_collector/service.py, collector/tests/test_service.py.
Changes: implement poll/backoff, distinct auth/network/parser states, serialized candidate validation before replacing the active session, persisted source timestamps, bounded freshness and status events. Retain a valid old session when candidate import fails.
Tests: uv run pytest -q tests/test_service.py; use controllable clocks and transports for old fixes, auth expiry, recovery, rotation, simultaneous import/poll and network outages.
Completion: only genuine newer source fixes generate location events; transient failures do not destroy credentials.
Suggested commit: feat: manage polling and session recovery.

### Task 2.3: Add MQTT discovery and state publishing
Depends on: 2.2.
Files: collector/src/google_maps_collector/mqtt.py, collector/tests/test_mqtt.py.
Changes: implement the specified topic contract, stable opaque IDs, hidden-but-enabled GPS trackers, separate battery sensors, last will, freshness availability, retained discovery and reconnect/HA-birth republishing. Bind output to explicit field schemas; never publish Google cookies/raw responses.
Tests: uv run pytest -q tests/test_mqtt.py; assert exact discovery payloads, duplicate prevention, timestamp preservation, battery-only changes and canary redaction.
Completion: deterministic discovery/state works with an intercepted publisher; no write-command subscription exists.
Suggested commit: feat: publish Home Assistant MQTT trackers.

### Task 2.4: Add private management and cookie import
Depends on: 2.3.
Files: collector/src/google_maps_collector/web.py, collector/src/google_maps_collector/static/index.html, collector/tests/test_web.py.
Changes: implement admin password verification, throttled login, random sessions/CSRF tokens, Host/Origin checks, bounded in-memory Netscape upload parsing and candidate validation. Display only the management fields in the spec. Keep cookie data absent from response/error/log bodies and never provide a cookie export endpoint.
Tests: uv run pytest -q tests/test_web.py; cover unauthorized access, wrong passwords, session expiry/restart, CSRF, hostile Origin/Host, oversized/chunked input and failed replacement.
Completion: setup/renewal works with synthetic credentials and every privacy/auth boundary is covered.
Suggested commit: feat: add authenticated local credential management.

## Phase 3: Integration and wiring [sequential]

### Task 3.1: Package the collector and authenticated broker
Depends on: 2.4.
Files: deploy/Dockerfile, deploy/compose.yaml, deploy/mosquitto.conf, deploy/mosquitto.acl, deploy/collector.env.example, tools/bootstrap_collector.py, collector/tests/test_bootstrap.py.
Changes: add ARM64-capable reproducible image construction, non-root/read-only restrictions, persistent volumes, file-based assigned secrets and separate broker ACLs. Bootstrap explicitly once, using private input/generated secret files outside Git; no regeneration on normal startup. Bind management and broker ports to host loopback. Use a separate Compose project and restart policies. Include orderly retry/health behavior, not just depends_on.
Tests: uv run pytest -q tests/test_bootstrap.py; then docker compose --env-file .local/collector.env -f deploy/compose.yaml config --quiet after synthetic bootstrap. Verify configuration contains no privileged mode, host networking, Docker socket or HA config mount.
Completion: test deployment config validates; bootstrap can repeat safely without replacing keys and images have pinned base digests.
Suggested commit: build: package isolated collector and MQTT broker.

### Task 3.2: Document user setup, People linkage and operations
Depends on: 3.1.
Files: docs/SETUP.md, docs/RECOVERY.md, docs/UPSTREAM_UPDATES.md, START_HERE.md.
Changes: document one-time session export/import, SSH UI access, expiry replacement, broker/HA setup, hidden enabled trackers, manual Person linkage, HA GPS-selection limits, backup/key recovery and targeted rollback. Keep the public docs free of actual credentials/contacts/host identifiers.
Tests: follow the synthetic setup/recovery procedure in a disposable environment; run git diff --check.
Completion: another developer can execute setup without the original chat, and destructive/reboot steps explicitly require authorization.
Suggested commit: docs: explain setup recovery and Person tracking.

## Phase 4: Tests and verification [sequential]

### Task 4.1: Exercise privacy and container recovery
Depends on: 3.2.
Files: collector/tests/integration/test_broker.py, collector/tests/integration/test_restart.py, collector/tests/test_privacy.py, deploy/compose.test.yaml, tools/validate_release.py.
Changes: run against a disposable broker and synthetic Google transport. Test ACL denials, reconnects, recreation, interrupted writes, invalid import and freshness. Scan logs, MQTT, HTTP errors and release artifacts for credential/location canaries. Verify dependency hashes, source revision and image digest and ensure no startup package downloads.
Tests: uv run pytest -q from collector/; docker compose -f deploy/compose.test.yaml up --abort-on-container-exit --exit-code-from tests; uv run python ../tools/validate_release.py from collector/.
Completion: current-session evidence covers AC1 through AC12 except physical-host/reboot evidence; CI artifacts contain no secrets.
Suggested commit: test: verify credential privacy and restart recovery.

### Task 4.2: Prepare and execute authorized Pi acceptance
Depends on: 4.1 and explicit owner deployment authorization.
Files: docs/DEPLOYMENT_REVIEW.md, docs/specs/current/2026-10-19-isolated-collector/verification.md, tracker.md.
Changes: inspect relevant tunnel/Access policies and available ports, present collector-only Compose diff and rollback, then deploy only if authorized. Validate mounts/permissions, original smart-home health and new tracker identities before/after targeted recreation. Import real cookies privately. Obtain explicit authorization before full Pi reboot. Record pass/partial/fail evidence per criterion and private sensitive evidence only in .local/.
Tests: run the pinned collector's documented health/status checks, restart/recreate only the new project, then the separately authorized reboot procedure. Existing HA/OTBR/Matter services must remain healthy and no additional credential import is required for normal restart.
Completion: verification.md lists exact evidence and residual risks; no unverified criterion is marked passed and no host changes exceed authorization.
Suggested commit: docs: record Raspberry Pi acceptance evidence.

## Acceptance mapping

AC1 -> 1.1, 1.2, 2.3, 3.1, 4.1.
AC2 -> 1.2, 4.1.
AC3 -> 2.1, 4.1, 4.2.
AC4 -> 2.2, 2.4, 4.1.
AC5 -> 2.4, 4.1.
AC6 -> 2.2, 2.3, 2.4, 4.1.
AC7 -> 2.3, 3.2, 4.1, 4.2.
AC8 -> 2.2, 2.3, 4.1.
AC9 -> 2.1, 3.1, 4.1, 4.2.
AC10 -> 3.1, 4.1, 4.2.
AC11 -> 1.2, 2.4, 4.1.
AC12 -> 1.1, 3.1, 3.2, 4.1.

## Verification

The commands above are task requirements. The collector suite now exists; consult tracker.md for fresh observed results and pending container/host checks. Do not infer a pass from the existence of test code or CI configuration.
