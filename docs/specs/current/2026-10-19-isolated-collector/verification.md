# Verification: isolated collector

Date: 19 October 2026. Overall: PARTIAL, not ready for deployment. See tracker.md for commands, counts, blocker and exact next action. No real Google session or Pi changes were used.

| Criterion | Local evidence | Remaining acceptance |
|---|---|---|
| AC1 Isolation and credential privacy | Separate package, Docker UID/config, intercepted transport and privacy tests | Built ARM64 image, effective container/host isolation and live compatibility |
| AC2 Restricted HTTPS origin | Actual Requests preparation, TLS, domain filtering and redirect tests pass | Real Google protocol compatibility |
| AC3 Encrypted persistent jar | Tamper/key/interruption/reconstruction tests pass | POSIX durability and mounted key/store behavior in containers |
| AC4 Validate-before-replace UI | Failed-import/concurrency/store tests pass | Real candidate import privately after authorization |
| AC5 Management boundaries | Authentication/session/CSRF/Origin/Host/throttling/stream bounds pass; native browser login/status/logout passed | Container-exposed listener/exposure checks |
| AC6 Revocation and recovery | Synthetic auth/network/parser/rotation cases pass; revocation stays fail-closed through later network failures | Real session revocation behavior |
| AC7 MQTT/People recovery | Discovery/schema/freshness unit tests pass; setup documents manual linkage | Broker harness execution, actual HA discovery, restart and Person behavior |
| AC8 Source freshness | Same/older/battery-only/TTL tests pass; source timestamp survives reconstruction | HA retained-message/update-time behavior |
| AC9 Restart/reboot recovery | Atomic interruption and new-interpreter recovery pass | Actual collector/broker recreation, targeted restart and separately authorized Pi reboot |
| AC10 Compose/ACL isolation | Both configs validate; pinned manifests and restrictive mounts/ACL definitions reviewed | Effective Linux permissions and live ACL denials |
| AC11 Canary privacy | Native logs/errors/MQTT schemas/encrypted store/wheel checks pass | Container logs, broker traffic and full release artifacts |
| AC12 Reproducible releases | Exact hashed lock, dependency advisory review, pinned base manifests, source metadata validator and build artifacts | Clean release revision, collector image digest, ARM64 startup and complete release record |

Final native suite: 73 passed, 2 broker tests skipped, one upstream test-client deprecation warning. pip-audit found no known runtime dependency vulnerabilities at the review date. Linux/Windows CI jobs and disposable broker CI are configured but not observed here.

Docker Compose execution failed because the local Linux engine pipe does not exist. Full release validation correctly fails incomplete. A manifest's ARM64 entry is not startup evidence; a subprocess reconstruction is not container recreation. No acceptance checkbox is marked complete based on unexecuted code.

Residual limits: synthetic Google fixtures are fabricated; no live compatibility test has occurred. MQTT source_timestamp is preserved, but HA's own last-update selection can change during retained replay; validate this with real HA before relying on source preference. The Pi and its administrators remain trusted, and privileged HA host code is outside a strong isolation guarantee.
