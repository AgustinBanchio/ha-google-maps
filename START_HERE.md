# Original Google Maps integration with external credentials

This is AgustinBanchio's public fork of pnbruckner/ha-google-maps. The source includes the upstream 2.1.0 tracker, connectivity sensor, five new sensors and Maps client at audited `ae85b249b354c25c2994cd1458231039e1dc977f`. Home Assistant uses a scoped connection to the separate session service, which owns Google credentials. The previous 2.0.3 baseline is preserved in the [original audit](docs/audits/2026-10-19-upstream-2.0.3/REVIEW.md).

Read in order:

1. [Current specification](docs/specs/current/2026-10-19-upstream-session-adapter/spec.md).
2. [Implementation plan](docs/specs/current/2026-10-19-upstream-session-adapter/plan.md).
3. [Current tracker and exact next action](docs/specs/current/2026-10-19-upstream-session-adapter/tracker.md).
4. [Native setup](docs/NATIVE_SETUP.md) and [deployment/rollback review](docs/NATIVE_DEPLOYMENT_REVIEW.md).
5. [Upstream patch boundary](docs/UPSTREAM_PATCH.md) and [update procedure](docs/UPSTREAM_UPDATES.md).
6. [Security context](docs/PROJECT_CONTEXT.md) and [operations](docs/OPERATIONS.md).

Native implementation and actual HA/ARM64 tests pass. The session API is deployed, and our native component is installed in HA's persistent configuration mount after one explicitly approved targeted HA restart. Existing HA Compose, privileges, Matter Server and OTBR remain unchanged. The native setup and migration are verified: five native trackers, four profile pictures and five People linked to their native source. Legacy MQTT publishing is off and its 16 entities are disabled; its broker remains running unchanged for rollback.

The original README describes upstream behaviour. [NEXT_STEPS](docs/NEXT_STEPS.md) describes this fork's setup. Earlier isolated-collector specifications and MQTT setup documents are historical transition material; they are not the final architecture.

The collector diagnostics release is deployed and verified as of 2026-10-20, with a successful live native poll and saved cookie rotation. The authenticated collector page retains safe failure metadata under Diagnostics; see [diagnostics](docs/DIAGNOSTICS.md) and [deployment evidence](docs/DIAGNOSTICS_DEPLOYMENT_REVIEW.md). HA and the other services were not restarted for this update.

The 2.1.0 update requires a coordinated collector and custom component upgrade. See the [2.1.0 audit and rollout](docs/audits/2026-11-25-upstream-2.1.0/REVIEW.md) for verification and rollback. The owner deployment evidence above is for the existing 2.0.3-based installation.

Push directly to the owner's main branch without PRs. Preserve the upstream remote and audited baseline. No automatic upstream merge or unattended deployment. Never commit credentials, account/contact/location data, raw host reports or private infrastructure configuration. Ignored `.local/` holds private operational files; fresh clones do not contain them.
