# Active implementation

The owner approved implementing the source-preserving correction without another planning gate. Read docs/specs/current/2026-10-19-upstream-session-adapter/spec.md, plan.md and tracker.md first. Continue from its exact next action. docs/COURSE_CORRECTION.md defines the approved direction. Do not claim pending native API/tests exist; record fresh evidence.

# Current direction: course correction

Read [the course-correction proposal](docs/COURSE_CORRECTION.md) first. The owner clarified that the intended solution is the original HA integration with external Google credential/session handling and a small maintainable upstream patch. The running MQTT collector is a reimplementation and is not the intended final architecture. The proposal is ready for review; replacement API/client code and HA migration have not been implemented. Keep the working deployment and existing stack intact during preparation.

## Running deployment and historical implementation

This is AgustinBanchio's fork of pnbruckner/ha-google-maps. The upstream integration remains unchanged. A separate collector is now implemented locally with encrypted session storage, polling, MQTT discovery and authenticated management. ARM64 broker/recovery tests and release validation now pass. The separate production collector/broker is deployed and verified after explicit approval. Selected Maps data and tracking defaults have been matched through MQTT; complete upstream equivalence is not established; the remaining owner step is to make previously hidden HA trackers Visible and check map/People linkage. The existing smart-home stack remains unchanged.

Read these in order:

1. [Project context and decisions](docs/PROJECT_CONTEXT.md).
2. [Specification](docs/specs/current/2026-10-19-isolated-collector/spec.md).
3. [Implementation plan](docs/specs/current/2026-10-19-isolated-collector/plan.md).
4. [Resumable tracker](docs/specs/current/2026-10-19-isolated-collector/tracker.md).
5. [Static upstream review](docs/audits/2026-10-19-upstream-2.0.3/REVIEW.md).
6. [Environment assessment](docs/ENVIRONMENT_ASSESSMENT.md).
7. [Operations access](docs/OPERATIONS.md).
8. [Collector setup](docs/SETUP.md) and [recovery](docs/RECOVERY.md).

Use tracker.md for exact current evidence and next action. The owner has privately imported the Google session and configured HA MQTT. The local Windows Docker engine was unavailable, so disposable ARM64 container tests ran on the Pi. See tracker.md for fresh results and docs/NEXT_STEPS.md for owner cookie import and HA MQTT setup.

The existing upstream README describes the original integration. Collector source and tests live in collector/, packaging in deploy/. The owner's local checkout is D:/repos/ha-google-maps. Ignored .local/ contains private operational context and isolated development tooling; a fresh clone does not include it.

Continue from the first unfinished tracker task. Do not change existing smart-home services or deploy the collector without the separate required authorization. All accepted requirements and security boundaries are recorded here; the originating conversation is not needed.
