# Diagnostics release deployment review

Source: `ce0c2bfeb551df90a2bbe15e29847a5d2902a684`. Diagnostic implementation: `b211f7cb3ee8f060eb2ebf78cbcf13a4c3dee20a`. The subsequent commit adds native ARM64 CI/recovery coverage.

Changes are confined to the collector transport metadata, service diagnostics, authenticated management UI and a read-only metadata command. Original HA entity/client modules and the native observation API are unchanged. No new Google endpoint, session-refresh policy, dependency, credential, Compose mount or privilege is introduced. The independent diagnostics file contains only allowlisted operational metadata and does not change the encrypted session format.

Verified evidence:

- Windows suite: 134 passed, two broker-only skips.
- Disposable Linux broker suite: 136 passed. Existing Starlette test-client deprecation warning only.
- All Collector and Validate CI jobs pass at the exact source revision, including native ARM64 production-image startup/session/recreation/broker-free recovery and diagnostics persistence/redaction (six acceptance groups), plus actual HA runtime tests.
- Protected-source guard, synthetic upstream update and release source checks pass.
- Synthetic browser management login, retained failure/recovery display and refresh button work.
- Read-only Pi preflight: current collector healthy; tagged prior image verified; a separate source checkout and four-container protection baseline prepared. No production change yet.

## Authorized change to request

Build from this exact source and the existing pinned Docker base images, then replace only the separate native-only collector. Use the existing private environment and data mount. Keep Google cookies, encryption key, management verifier and HA data key unchanged. This requires one collector replacement, which clears management-browser login sessions but preserves the Google session. HA needs no restart or component update.

1. Confirm clean exact source, image revision/architecture and protected-container baseline.
2. Retain the old image tag/environment and back up encrypted data while only the collector is stopped. Never read credential contents.
3. Set only the collector image reference and recreate that service with the existing native-only Compose file and `--no-deps --pull never`. Do not run the existing HA Compose stack or remove orphans.
4. Check health, UID/read-only/restart/loopback configuration, authenticated UI availability and the new metadata-only command. Read only allowlisted diagnostic metadata, never raw logs or credentials. Confirm all four protected containers are unchanged.
5. Verify successful native polls through metadata when HA is polling. If HA still needs reauthentication after the earlier session renewal, finish its supported flow privately using the existing key; never claim a live source poll that has not occurred.

## Rollback

Stop only the new collector, restore the prior image environment/reference and recreate only the collector. The encrypted format is unchanged: retain the newest Google session by default. Restore the matching encrypted data backup only if storage corruption/incompatibility requires it, preserving the failed directory separately. The old release ignores the new independent diagnostics file. Verify health and the protected-container baseline.

HA, broker, Matter Server, OTBR, existing Compose permissions, SSH, tunnel and host services are outside this change. No reboot.
