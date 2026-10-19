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
- Local checkout: D:/repos/ha-google-maps. The owner will import it into T3. A separate Pi collector source checkout now exists; private operational paths are not published.

## Corrected direction and current implementation

The original HA integration implements person/location reporting and tracking behaviour. Google credential/session handling is externalized through a narrow source adapter. Five protected upstream files and the external service's vendored Maps client match the audited baseline; the documented patch boundary identifies each changed integration file.

The scoped loopback API returns original upstream observations before HA filtering. HA stores only its separate location-data access key and account identity. The external encrypted store/import UI and operations tooling remain responsible for Google cookies. The native component and tested ARM64 service are deployed; supported HA setup, pictures, map and five Person migrations are verified.

Legacy MQTT publishing is disabled. Its five tracker identities were matched exactly to native Google identities, Person links migrated through HA's supported API, and all 16 legacy entities disabled. The broker remains unchanged for rollback. See [course correction](COURSE_CORRECTION.md), [native setup](NATIVE_SETUP.md) and the active tracker.

## Security judgement

The user accepted proceeding with the Pi as a trusted host after discussing likelihood versus impact. There is no measured probability of compromise. The review found no deliberate cookie exfiltration in the pinned upstream source, not an unconditional security guarantee.

The collector's purpose is to reduce accidental exposure and code/update surface. HA is currently root and privileged, and the host administrators have broad access. This design cannot promise protection from malicious code controlling that host. Do not silently claim otherwise.

A stronger host boundary or reducing HA privileges may be assessed later. Do not modify existing smart-home services as part of initial collector work.

## Status and scope

The scoped collector API and native custom component are implemented, tested and installed. The owner explicitly approved one targeted HA restart for this installation. HA's persistent `/config` mount retains the component across normal HA Compose pull/recreation; no existing Compose file or permissions were changed. The separate collector and broker retain `unless-stopped` recovery and private persistent storage.

The owner requests direct pushes to this personal fork without PRs. The installed HA version tested is 2026.10.1; future upstream or HA updates require compatibility checks. Broker retirement, unrelated service changes and Pi reboot are not authorized by the component installation approval.
