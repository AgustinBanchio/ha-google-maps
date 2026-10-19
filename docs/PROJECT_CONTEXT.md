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

## Corrected direction and current implementation

The owner clarified that the original HA integration must remain the implementation of person/location reporting and tracking behaviour, with Google credential/session handling externalized through a small source/transport adapter. Future upstream updates should apply to that original code with a limited, documented authentication patch. See [course correction](COURSE_CORRECTION.md) for the proposed boundary, reuse, verification and migration.

The currently running collector/MQTT implementation is a different architecture. It duplicates the parser/tracking policy and replaces HA's original entities; selected parity tests do not establish complete equivalence. Keep it running while the source-preserving correction is prepared. All original custom_components/google_maps files remain identical to the pinned upstream baseline, so they can be used directly as the foundation.

The external encrypted store/import UI and operations tooling may be reused after review. A native data API/client does not exist yet. Do not infer approval to install/restart HA or remove the production broker from the discussion of a proposed architecture.

## Security judgement

The user accepted proceeding with the Pi as a trusted host after discussing likelihood versus impact. There is no measured probability of compromise. The review found no deliberate cookie exfiltration in the pinned upstream source, not an unconditional security guarantee.

The collector's purpose is to reduce accidental exposure and code/update surface. HA is currently root and privileged, and the host administrators have broad access. This design cannot promise protection from malicious code controlling that host. Do not silently claim otherwise.

A stronger host boundary or reducing HA privileges may be assessed later. Do not modify existing smart-home services as part of initial collector work.

## Status and scope

The isolated collector and broker are implemented, tested on ARM64 and deployed after explicit owner approval. The upstream runtime and existing smart-home Compose/permissions/services remain unchanged. The owner has imported a real Google session and added HA MQTT. Current work is the source-preserving course correction described above; the new transport/API remains proposed. See tracker.md for exact evidence and residual acceptance checks.

The owner requests direct pushes in the personal repository without PRs. Deployment authorization covers only this new project; existing stack/service changes and full Pi reboot still require separate explicit approval.
