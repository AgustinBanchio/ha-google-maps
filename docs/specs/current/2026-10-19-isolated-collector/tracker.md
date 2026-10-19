# Tracker: isolated Google Maps collector

Plan: [plan.md](plan.md).
Prepared: 2026-10-19.
Status: NOT_STARTED.

## Tasks

| Task | Phase | Status | Updated |
|---|---|---|---|
| 1.1 Package and reproducible dependencies | 1 | PENDING | 2026-10-19 |
| 1.2 Hardened Google transport | 1 | PENDING | 2026-10-19 |
| 2.1 Encrypted durable store | 2 | PENDING | 2026-10-19 |
| 2.2 Polling and session lifecycle | 2 | PENDING | 2026-10-19 |
| 2.3 MQTT discovery and freshness | 2 | PENDING | 2026-10-19 |
| 2.4 Authenticated management UI | 2 | PENDING | 2026-10-19 |
| 3.1 Container broker and bootstrap | 3 | PENDING | 2026-10-19 |
| 3.2 Setup recovery and Person docs | 3 | PENDING | 2026-10-19 |
| 4.1 Privacy and restart suite | 4 | PENDING | 2026-10-19 |
| 4.2 Authorized Pi acceptance | 4 | PENDING | 2026-10-19 |

Status values: PENDING, IN_PROGRESS, DONE, FAILED, BLOCKED. A blocker must name the missing fact/authorization, not simply say work remains.

## Preparation completed

- Static review of all nine upstream integration modules, matched to the full 2.0.3 commit/tree.
- Read-only Pi architecture, privilege, listener, firewall, SSH, custom-manifest and tunnel-process checks.
- Restored authenticated SSH through a local desktop-session helper without exporting SSH keys or changing T3/1Password configuration.
- Fork created in AgustinBanchio and cloned under D:/repos/ha-google-maps, with origin/upstream remotes.
- Public handoff documents contain sanitized findings; raw reports and connection context remain only in ignored .local/.
- No Google credentials supplied, new Google account, remote clone, implementation or deployment.

## Resume instruction

Read START_HERE.md and AGENTS.md. On the owner's implementation instruction, begin Task 1.1, keep upstream runtime unchanged and update this tracker after each completed task. Use synthetic data. Do not deploy or reboot existing services as part of development.

## Remaining deployment preconditions

Cloudflare routes/Access authentication and router forwarding remain unverified. Existing HA/OTBR privileges remain unchanged and are accepted host-trust limitations. Verify actual ports/mounts and obtain specific deployment authorization before Task 4.2. A full Pi reboot requires explicit authorization.

## Verification record

The preparation verification is in docs/PREPARATION_VERIFICATION.md. Feature acceptance has not run and the spec checkboxes remain unchecked.
