# Course correction: preserve upstream, isolate Google authentication

19 October 2026. Approved and implemented after the owner explicitly requested the changes. The native adapter/API and tests now exist; the tested session API is deployed and our native component is installed. MQTT remains during migration. The findings below explain the correction; use the active tracker for current evidence.

## Objective and finding

The owner's objective is the original pnbruckner/ha-google-maps integration, with Google credential handling moved outside HA and a small, maintainable upstream patch. Person reporting, location selection, state restoration, pictures, attributes, options and entity lifecycle should remain upstream behaviour.

The current solution diverged from that objective. It preserved upstream source as a reference but deployed a separate parser/model, location selection/lifecycle implementation and MQTT entity publisher. Selected synthetic comparisons and matching fields did not prove equivalence to the original HA integration. Earlier parity claims should be read as limited checks, not complete behavioural equivalence.

Fresh local inspection at f456f7b3ea4e9bae9ee0a0b6e8563d2c932fc18c: all nine Python modules and all other files under custom_components/google_maps are unchanged from audited baseline b2132123d46c47e5761d5d91cc08ca6b712fe6c1. No clean-room rewrite or repository/history reset is needed.

## Options and recommendation

| Approach | Consequence | Recommendation |
|---|---|---|
| Continue reproducing upstream behaviour through MQTT | Retains two implementations of tracking/entity behaviour and requires translating each future upstream change | Stop expanding this path |
| Use the original HA integration with a small external-session data source | Keeps upstream entity behaviour as the implementation and localizes authentication/transport changes | Recommended |
| Create a fresh repository and rebuild everything | Discards reusable security/operations work without reducing the necessary integration patch | Unnecessary |

Use the existing fork and pinned upstream as the foundation. Reuse the original integration rather than building another new set of HA entities. Reuse independently useful credential infrastructure after checking its interfaces against the corrected boundary.

## Required boundary

Google Maps -> external session service -> authenticated local data API -> original HA coordinator/entities

The external service owns cookie import, validation, rotation, encrypted persistence and Google-authenticated HTTP. HA receives person/location records and non-secret session status/expiry metadata. HA may hold a separate, scoped data-access credential that cannot read Google cookies or use management/upload endpoints.

Moving only a cookie file outside HA would not meet the goal: HA would still need the reusable cookie to make authenticated Google requests. The Google request must move with the credentials. Changes to the credential/setup flow and transport connection are therefore expected; changes to person/location reporting are not.

No generic proxy, caller-selected Google URL, cookie export or raw Google-response API is needed. Return an explicit versioned person-data schema matching the audited upstream client contract, without cookie/header/token fields. Keep account identity/name semantics equivalent to upstream, including its account-holder option; account email is ordinary configuration/data, not a Google session secret. Do not keep the current generic Account holder substitution as a permanent change to upstream presentation.

## What to preserve and replace

- Use custom_components/google_maps/device_tracker.py directly: preserve names, pictures, all attributes, GPS accuracy selection, missing-contact grace and state restoration. Keep it unchanged from the selected upstream revision unless a separately justified compatibility fix is required.
- Preserve binary_sensor.py behaviour and the original PersonData/LocationData/MiscData contracts in helpers.py. Retain existing account, accuracy and scan-interval options. Keep the original entity/device identity scheme.
- Change coordinator.py only where it constructs/calls the source or maintains cookies. Keep HA update/coordinator and error semantics; map external credential/network/parser failures explicitly. Credential repairs lead to the external UI instead of uploading cookies through HA.
- Change config_flow.py, __init__.py credential lifecycle, strings/translations and manifest only as needed to configure the external source and remove HA cookie upload/storage/delete paths. Do not leave a fallback that silently loads Google cookies into HA.
- Add one narrow local client adapter, provisionally custom_components/google_maps/collector_client.py, supplying the original coordinator's person-data contract.
- Use the audited upstream embedded Maps client/parser as the external service's implementation, packaged from the same pinned source at build time. Isolate fixed-origin/TLS/redirect/response-bound/error-redaction hardening in a small documented transport/persistence wrapper. Do not maintain a second hand-written person parser or location policy. Any unavoidable parser/client modification must be itemized against the pinned source.
- The native API returns the upstream client's observations before HA-specific accuracy filtering, age expiry or missing-contact policy. Do not serve the current service.people cache as its source: those records have already undergone reimplemented filtering.
- Preserve source timestamps and units exactly; test the millisecond/second boundary. Account-holder identity must map to the original configured account identity, not a replacement opaque label.
- Keep HA's configured polling schedule in control of native updates. Design the source fetch/single-writer path so the API does not introduce a second independent location policy or concurrent cookie writers. MQTT compatibility during transition must share the serialized session service.
- Reuse encrypted storage, private import UI, assigned secret files, container hardening, SSH helper and recovery tests where applicable. They are supporting infrastructure, not the source of HA tracking semantics.
- Retire the MQTT tracking publisher and duplicated HA policy after the native path is verified and cut over. Remove only this project's broker if separately authorized and no longer needed. Do not remove an unrelated HA MQTT configuration.

## Proof required before migration

1. Freeze the exact upstream revision and produce an explicit patch inventory with a rationale per changed upstream file. Add a source-diff guard that flags changes to protected entity/business-logic modules. Keep upstream attribution and the upstream remote.
2. Run actual HA-level tests against the selected supported HA version. Exercise the original entity classes with the same synthetic observations through the original and external transports, comparing states/attributes, pictures, names, unique IDs, accepted fixes, missing-contact timing, restoration and options. Parser-only or MQTT-only tests are insufficient.
3. Cover bad/absent contact records, account-holder data, changed profiles/batteries with unchanged GPS time, less accurate fixes, backward timestamps, missing people, auth expiry, network failure, cookie replacement and source restart. Document any deliberate deviation; do not silently call it equivalent.
4. Verify Google cookies do not enter HA process data, config, diagnostics, HTTP responses, exceptions, logs or release artifacts. Verify the data-only credential cannot access import, management, secrets or arbitrary outbound requests. Keep trusted-host limitations explicit.
5. Test encrypted-session continuity, ARM64 service startup/recovery and a simulated upstream update applied to the original source plus the small maintained patch. The original update must flow into the implementation, not require manually reimplementing its tracker rules again.
6. Review real frontend results after an authorized test installation; API field presence alone does not establish HA presentation.

## Migration and rollback

Keep the running MQTT release until the native adapter/API and tests are ready. Do implementation/testing in development fixtures or disposable environments; do not restart or modify the owner's HA stack during preparation.

Before live migration, prepare a concrete collector diff, HA installation/restart requirements, a private old-to-new entity mapping, Person/automation linkage checks and rollback. Current MQTT entities use a different platform/identity scheme; preserving upstream unique IDs does not automatically migrate MQTT entity IDs or Person links. Do not edit HA .storage files or assume automatic registry transfer. Use supported HA flows and explicitly verify links.

Stage the service change so the existing encrypted cookie/key pair is preserved. Keep one cookie writer. Coordinate old MQTT tracker disable/cleanup and native tracker enablement so duplicate active location sources do not silently change Person selection. Retain the old image/config and matching state backup until the owner confirms maps/People work.

Installing/restarting HA, changing its mounts/permissions, stopping the production broker or rebooting the Pi remain separate operational changes requiring the applicable authorization. The existing HA/Matter/OTBR Compose and Thread permissions are outside the refactor.

## Current next step

Complete native setup through HA's supported flow and verify real tracker presentation and People/automation links before retiring MQTT. See the active upstream-session-adapter tracker. Source guards, seven actual HA runtime scenarios and ARM64 API/recovery tests pass. Preserve direct pushes to the owner's fork without PRs and audit upstream updates explicitly.
