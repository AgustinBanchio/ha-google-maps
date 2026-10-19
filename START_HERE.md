# Continue this project

This is AgustinBanchio's fork of pnbruckner/ha-google-maps. The upstream integration remains unchanged. A separate collector is now implemented locally with encrypted session storage, polling, MQTT discovery and authenticated management. ARM64 broker/recovery tests and release validation now pass. The separate production collector/broker is deployed and verified after explicit approval. The existing smart-home stack remains unchanged.

Read these in order:

1. [Project context and decisions](docs/PROJECT_CONTEXT.md).
2. [Specification](docs/specs/current/2026-10-19-isolated-collector/spec.md).
3. [Implementation plan](docs/specs/current/2026-10-19-isolated-collector/plan.md).
4. [Resumable tracker](docs/specs/current/2026-10-19-isolated-collector/tracker.md).
5. [Static upstream review](docs/audits/2026-10-19-upstream-2.0.3/REVIEW.md).
6. [Environment assessment](docs/ENVIRONMENT_ASSESSMENT.md).
7. [Operations access](docs/OPERATIONS.md).
8. [Collector setup](docs/SETUP.md) and [recovery](docs/RECOVERY.md).

Use tracker.md for exact current evidence and next action. No real Google credentials have been supplied. The local Windows Docker engine was unavailable, so disposable ARM64 container tests ran on the Pi. See tracker.md for fresh results and docs/NEXT_STEPS.md for owner cookie import and HA MQTT setup.

The existing upstream README describes the original integration. Collector source and tests live in collector/, packaging in deploy/. The owner's local checkout is D:/repos/ha-google-maps. Ignored .local/ contains private operational context and isolated development tooling; a fresh clone does not include it.

Continue from the first unfinished tracker task. Do not change existing smart-home services or deploy the collector without the separate required authorization. All accepted requirements and security boundaries are recorded here; the originating conversation is not needed.
