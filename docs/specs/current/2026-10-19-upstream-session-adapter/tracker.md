# Tracker: original integration, external session

Status: IN_PROGRESS. Owner explicitly requested implementation without stopping after proposals. No native code/tests exist at task start.

| Task | Status |
|---|---|
| 1 Upstream client and transport wrapper | DONE |
| 2 Scoped session data API | DONE |
| 3 Original HA source/auth adapter | IN_PROGRESS |
| 4 Actual HA equivalence/security tests and patch guard | PENDING |
| 5 ARM64 release, authorized rollout and migration handoff | PENDING |

Exact next action: implement unchanged upstream client packaging and the session wrapper, then data API and native adapter. Current production remains MQTT release f5a05b9 until a tested replacement is ready. No HA restart or existing-stack changes have occurred.


Fresh implementation checkpoint: collector suite 109 passed/2 broker skips, one existing Starlette warning; protected-source guard passes for five upstream files plus identical vendored client. Native data API and source/auth adapter exist. The API bypasses legacy filtered MQTT state and preserves full upstream names/addresses; API scope/timestamp/account/security tests pass. Actual HA 2026.10.1 runtime harness is written but not yet executed; do not claim HA equivalence. Exact next action: run that harness in a disposable copy of the installed HA image, correct runtime issues, then broaden native/error/migration tests and prepare ARM64 release.
