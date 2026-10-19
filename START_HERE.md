# Original Google Maps integration with external credentials

This is AgustinBanchio's public fork of pnbruckner/ha-google-maps. The native integration retains the original tracker, connectivity sensor, helper contracts, constants and Maps client at audited upstream `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`. A narrow source adapter replaces Google cookie handling in HA. The separate session service uses that same original Maps client and owns Google credentials.

Read in order:

1. [Current specification](docs/specs/current/2026-10-19-upstream-session-adapter/spec.md).
2. [Implementation plan](docs/specs/current/2026-10-19-upstream-session-adapter/plan.md).
3. [Current tracker and exact next action](docs/specs/current/2026-10-19-upstream-session-adapter/tracker.md).
4. [Native setup](docs/NATIVE_SETUP.md) and [deployment/rollback review](docs/NATIVE_DEPLOYMENT_REVIEW.md).
5. [Upstream patch boundary](docs/UPSTREAM_PATCH.md) and [update procedure](docs/UPSTREAM_UPDATES.md).
6. [Security context](docs/PROJECT_CONTEXT.md) and [operations](docs/OPERATIONS.md).

Native implementation and actual HA/ARM64 tests pass. The session API is deployed, and our native component is installed in HA's persistent configuration mount after one explicitly approved targeted HA restart. Existing HA Compose, privileges, Matter Server and OTBR remain unchanged. The previous MQTT path remains available during configuration/migration; do not retire it before native People/automation links are verified.

The original README describes upstream behaviour. [NEXT_STEPS](docs/NEXT_STEPS.md) describes this fork's setup. Earlier isolated-collector specifications and MQTT setup documents are historical transition material; they are not the final architecture.

Push directly to the owner's main branch without PRs. Preserve the upstream remote and audited baseline. No automatic upstream merge or unattended deployment. Never commit credentials, account/contact/location data, raw host reports or private infrastructure configuration. Ignored `.local/` holds private operational files; fresh clones do not contain them.
