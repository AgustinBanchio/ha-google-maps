# Continue this project

This is AgustinBanchio's fork of pnbruckner/ha-google-maps. The upstream integration is retained unchanged. The next feature is a separate Google Maps location collector feeding Home Assistant through MQTT.

Read these in order:

1. [Project context and decisions](docs/PROJECT_CONTEXT.md).
2. [Specification](docs/specs/current/2026-10-19-isolated-collector/spec.md).
3. [Implementation plan](docs/specs/current/2026-10-19-isolated-collector/plan.md).
4. [Resumable tracker](docs/specs/current/2026-10-19-isolated-collector/tracker.md).
5. [Static upstream review](docs/audits/2026-10-19-upstream-2.0.3/REVIEW.md).
6. [Environment assessment](docs/ENVIRONMENT_ASSESSMENT.md).
7. [Operations access](docs/OPERATIONS.md).

Current state: fork, local checkout and handoff prepared; collector implementation has not started. No Google credentials have been provided. Nothing has been deployed or restarted on the Raspberry Pi.

The existing upstream README describes the original integration, not the planned collector. Import this directory as a T3 project and ask the new thread to read START_HERE.md and continue from tracker.md.

The owner's local checkout is D:/repos/ha-google-maps. An ignored .local directory contains private operational context and raw host reports on that checkout only. A fresh clone will not contain those reports.

There is no need for the originating chat. All accepted requirements, security boundaries and next tasks are in this repository.
