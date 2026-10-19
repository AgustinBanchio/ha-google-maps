# Project context and accepted decisions

## Objective

Retrieve locations already shared with the owner's personal Google Maps account and feed Home Assistant People/zone automations, while reducing credential exposure and controlling updates.

## Requirements carried forward from the owner

- Use the existing personal Google account. Asking contacts to share with another account is not an option.
- Start from a fork of pnbruckner/ha-google-maps, audited at release 2.0.3 and commit b2132123d46c47e5761d5d91cc08ca6b712fe6c1.
- The owner runs HA Container on a 64-bit Raspberry Pi alongside Matter Server and OTBR.
- The Pi also runs T3, Codex and Claude. Administrative tools can use a host user with Docker access and passwordless sudo.
- A normal Pi reboot, Docker restart or Compose recreation must preserve the session and recover automatically.
- Provide comfortable first-time credential import and later replacement.
- Preserve all original person/location fields in HA; names and locations are intended HA data.
- Keep Google credentials out of HA configuration, entity data, MQTT, logs, repository files and routine HA backups.
- Future upstream updates are audited on request before merging into the fork. No automatic merge/deploy.
- Carry all project knowledge in the repository because the originating conversation will not be reused.
- Local checkout: D:/repos/ha-google-maps. The owner will import it into T3. A Pi source checkout is optional and has not been created.

## Chosen approach

Retain the upstream integration for provenance and extract its small Maps client into a standalone Python service. Use standard HA MQTT device trackers rather than loading the Google cookie into HA's Python process. Add a narrowly scoped authenticated management page and persistent encrypted storage.

Use a separate Compose project for the collector and its small authenticated Mosquitto broker. No broker was observed on the Pi's standard ports or in its running containers; a broker elsewhere was not ruled out. The provided broker is the default so the plan has no dependency on an unspecified service. HA's host-network container connects to the broker's loopback-published port. A future existing-broker override must preserve equivalent ACLs.

## Security judgement

The user accepted proceeding with the Pi as a trusted host after discussing likelihood versus impact. There is no measured probability of compromise. The review found no deliberate cookie exfiltration in the pinned upstream source, not an unconditional security guarantee.

The collector's purpose is to reduce accidental exposure and code/update surface. HA is currently root and privileged, and the host administrators have broad access. This design cannot promise protection from malicious code controlling that host. Do not silently claim otherwise.

A stronger host boundary or reducing HA privileges may be assessed later. Do not modify existing smart-home services as part of initial collector work.

## Status and scope

The isolated collector and broker are implemented, tested on ARM64 and deployed after explicit owner approval. The upstream runtime and existing smart-home Compose/permissions/services remain unchanged. The owner has imported a real Google session and added HA MQTT. Current work corrects names/map visibility and upstream data parity. See tracker.md for exact evidence and residual acceptance checks.

The owner requests direct pushes in the personal repository without PRs. Deployment authorization covers only this new project; existing stack/service changes and full Pi reboot still require separate explicit approval.
