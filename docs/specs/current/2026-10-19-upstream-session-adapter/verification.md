# Verification: collector diagnostics maintenance

## Verdict: PASS

Scope: the 2026-10-20 diagnostics addition and explicitly authorized collector-only rollout. Original native migration evidence remains in the tracker. A successful post-deployment native poll was observed; this report does not infer the cause of the earlier Google rejection.

## Test results

Fresh focused Windows test output, using the existing collector virtual environment:

```text
24 passed, 1 warning in 6.72s
```

The warning is the existing Starlette TestClient/httpx deprecation. The `uv` executable was absent from this shell's PATH; the existing virtual environment's Python ran the tests successfully.

Fresh source checks:

```text
{"upstream_guard": "passed", "baseline": "b2132123d46c47e5761d5d91cc08ca6b712fe6c1", "protected_files": 5}
source_metadata_passed
```

Actual Pi image acceptance output, with synthetic fixtures only:

```json
{
  "passed": [
    "synthetic import, native data API and arm64 non-root startup passed",
    "broker restart and both-container recreation preserve session key and identity",
    "rejected replacement and independent stale-fix availability passed",
    "container logs contain no credential/contact canaries",
    "bounded diagnostics survive recovery/recreation and metadata-only CLI excludes canaries",
    "native-only request-driven data survives recreation with broker stopped"
  ],
  "source_revision": "ce0c2bfeb551df90a2bbe15e29847a5d2902a684",
  "image_id": "sha256:fdbef26546ac1d39d6449d30653daeb28323fb0f456451826d7f0b9e41565151",
  "architecture": "arm64"
}
```

Release packaging validation passed before replacement. Selected deployment checks returned `deployed: true`, `release_validation: true`, `metadata_cli_verified: true`, `diagnostics_persistence: true`, `protected_containers_unchanged: 4`, `credentials_reused: true`, `encrypted_state_backup: true`, `ha_restart: false`, `compose_unchanged: true`, `no_reboot: true`. A second baseline check passed. The live metadata CLI showed `native_poll` success, cookie changes `added: 0, changed: 2, removed: 0`, and no source failure. The local tunnel returned HTTP 200. Private operational reports remain ignored; no raw production logs or credential contents were read.

## Acceptance criteria audit

| Criterion | Status | Evidence |
|---|---|---|
| Distinct transport/auth/data/storage failure metadata | PASS | `collector/src/google_maps_collector/diagnostics.py:76`; `collector/tests/test_diagnostics.py:40`; `collector/tests/test_diagnostics.py:109` |
| No secret, account, contact, location or exception text output | PASS | `collector/tests/test_diagnostics.py:40`; `collector/tests/test_diagnostics.py:149`; actual-image canary acceptance `tools/acceptance_test.py:214` |
| Bounded persisted history, recovery and saved rotation counts | PASS | `collector/src/google_maps_collector/diagnostics.py:104`; `collector/tests/test_diagnostics.py:70`; `collector/tests/test_diagnostics.py:84`; `tools/acceptance_test.py:229`; persisted live event |
| Authenticated management UI and credential-free metadata command | PASS | `collector/tests/test_diagnostics.py:174`; `collector/tests/test_diagnostics.py:186`; deployed HTML and CLI verification |
| Preserve source/wire/authentication contracts | PASS | Fresh five-file upstream guard; native API/recovery acceptance `tools/acceptance_test.py:222`; historical exact-revision CI and actual HA results in tracker |
| Collector-only authorized rollout with rollback, no HA restart | PASS | `docs/DIAGNOSTICS_DEPLOYMENT_REVIEW.md`; actual-image tests and release validation before replacement; four-container baseline checks and retained rollback artifacts |

## Edge case coverage

| Case | Handled | Tested | Evidence |
|---|---|---|---|
| Failed import preserves working session | Yes | Yes | `collector/tests/test_diagnostics.py:99`; Pi acceptance |
| Source failure retained after recovery/access denial/restart | Yes | Yes | `collector/tests/test_diagnostics.py:84`; Pi acceptance |
| Corrupt/oversized/untrusted metadata | Yes | Yes | `collector/tests/test_diagnostics.py:126`; `collector/tests/test_diagnostics.py:141`; `collector/tests/test_diagnostics.py:149` |
| Optional metadata write or stderr failure | Yes | Yes | `collector/tests/test_diagnostics.py:117`; `collector/tests/test_diagnostics.py:160` |
| Actual Requests cookie extraction and encrypted persistence | Yes | Yes | `collector/tests/test_diagnostics.py:70`; live saved cookie changes |

## Test quality

All six acceptance criteria have evidence; all five listed edge cases have tests. Assertions cover observed error codes, actual Requests cookie handling, encrypted continuity, authorization separation and canaries across persisted/container output. The Pi acceptance used the exact deployed image and an isolated synthetic Compose project. Its broker restarts were confined to that project. No issue remains from the initial missing fixture image.

## Scope deviations

None. No additional Google endpoint, session-refresh policy, HA component, production broker or Compose permission change. The metadata command and defensive logging behavior support the requested safe diagnosis.

## Action items

No required deployment work remains. Refresh/sign into the collector page to view Diagnostics. Preserve rollback artifacts and inspect retained failure metadata if Google rejects a future session. Calendar expiry alone cannot explain every rejection.
