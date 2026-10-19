# Project instructions

Read START_HERE.md, then the current specification, plan and tracker before changing code. Keep tracker.md current with evidence and the exact next action. Do not claim pending collector code or tests exist.

This repository is a public fork. Never commit Google cookies, private keys, passwords, tokens, account/contact/location data, raw host reports or unredacted infrastructure configuration. Use .local/ for private operational files; it is ignored. No real credentials are required for implementation or CI fixtures.

The owner accepted the Raspberry Pi host and its administrators as trusted. The current privileged HA container prevents a strong guarantee against hostile HA integration code on that host. Separate storage reduces accidental exposure; encryption with an automatically available key does not remove administrator access.

Current remote authorization is read-only inspection, plus creating a separate source checkout if needed. No Pi checkout was needed during preparation. Do not change or restart HA, Matter Server, OTBR, firewall, SSH, tunnels or host services, and do not reboot the Pi, without explicit deployment/change authorization. Do not read credential files or dump container environments, process arguments, HA auth storage or logs. Return only selected metadata.

On Windows, a background T3 Connect process may not use the desktop 1Password agent directly. tools/Invoke-DesktopSsh.ps1 supports normal 1Password approval via a one-shot, non-admin interactive-session task. Get the target from .local/private-context.md, or ask the owner if absent. Keep host-key verification and agent forwarding disabled. Never export SSH private keys or relax 1Password protection. The user must be logged into the desktop. This is a transport workaround, not a global fix to Session 0 SSH.

Preserve the audited upstream baseline b2132123d46c47e5761d5d91cc08ca6b712fe6c1 and the upstream remote. Keep changes to the embedded Maps client small and attributable. Follow docs/UPSTREAM_UPDATES.md before incorporating upstream changes. No automatic upstream merges or unattended collector deployment.

The owner's authorization covers preparing this fork and its plan. Begin substantial collector implementation when the owner asks to implement/continue the plan. Remote deployment is a separate action; prepare a concrete diff, tests and rollback before requesting any needed deployment approval.

For this personal fork, commit and push directly to the owner repository; do not open pull requests unless explicitly requested. Preserve the audited upstream remote and baseline.
