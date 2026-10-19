# Native Google Maps integration with an external session

This fork uses the original Google Maps HA tracker and connectivity sensor, options, names, pictures, attributes and location-selection policy. Google cookies are imported only into the separate session service. HA receives a separate scoped location-data key; it cannot use that key to upload/export cookies or access management.

The owner deployment has the tested service and our custom component installed. HA was restarted once with explicit approval. The component is in the persistent `/config/custom_components/google_maps` mount, not in the container image.

## Add Google Maps

1. Open Settings > Devices & services > Add integration > Google Maps.
2. Enter your Google account email, collector address `http://127.0.0.1:8787` and its dedicated data access key. On the owner's workstation the new private handoff is `.local/native-handoff/NATIVE-SETUP-PRIVATE.txt`. Open it privately, save the key in a password manager, and never paste it into chat or Git.
3. Choose whether to create the account-holder tracker, maximum GPS accuracy and update period. These are the original integration's options. The default accuracy is 1000 metres; use the polling period appropriate for your existing setup.
4. Confirm names, profile pictures and GPS in the native tracker entities. Shared contacts keep their original Google IDs. Link trackers through Settings > People; verify relevant automations/dashboard references before retiring the previous MQTT trackers.

The loopback address assumes HA uses the host network as in the audited owner deployment. Do not expose the service publicly or change the existing Thread/Matter permissions to make it reachable.

## Missing Data for Account Tracker

Google may omit the account holder's own location and does not supply its profile picture/battery in that record. As upstream, its tracker uses the configured account email for identity/name. Contacts retain their original Google IDs and fields.

## Normal HA Compose updates and Pi restarts

Run your usual `docker compose pull` and `docker compose up -d` in the existing HA Compose project. Its persistent `/config` mount retains our component and HA integration configuration when the container is recreated. No custom HA image, extra Python install inside the container or Compose patch is required. Keep the same `/config` storage and host network; do not delete its data volume.

The session service runs in its own Compose project with `restart: unless-stopped`; its encrypted session, encryption key and scoped data key persist outside the container. Updating the HA project does not update or recreate the collector. A normal Pi restart brings back HA and the separate service through their Docker restart policies; an explicitly stopped container remains stopped.

Tested HA version: 2026.10.1. A future HA release can change custom-integration APIs; CI covers the supported version and upstream updates are reviewed using [UPSTREAM_UPDATES](UPSTREAM_UPDATES.md). Back up HA configuration before major HA updates. Do not install the original upstream component over this fork or let HACS replace it with the original cookie-based release.

## Session replacement

Open the private management tunnel using `tools/Open-CollectorTunnel.ps1` and import a renewed Google cookie export at the external service. Reload Google Maps or retry its reauthentication flow after the service reports ready. Google cookies must never be pasted into HA's data access key field. See [Chrome export instructions](COOKIE_IMPORT.md).

A legacy cookie-based native installation is migrated without reading or deleting its old cookie file. Reconfigure the source and remove/revoke obsolete HA cookie copies privately after verifying the external session. The owner's former MQTT-only installation did not put Google cookies in HA.

## Existing MQTT installation

MQTT and native platform identities differ. Keep the old path until names, pictures, map positions and People/automation links are verified in the native integration. Use supported HA configuration/registry flows; never edit `.storage` directly or remove an unrelated MQTT integration.

After migration, switch only the collector to `deploy/compose.session.yaml` with the existing private environment file and image. This disables legacy polling/publishing and leaves the existing broker intact. It needs only store-key, admin-verifier and data-token. Remove this project's old discovery/entities and broker only under the applicable migration authorization. Never use `--remove-orphans` during this transition.

For an existing collector, provision the new key with `tools/provision_data_token.py` and the encrypted owner handoff; do not rerun bootstrap against existing secrets. Fresh installations generate that key during bootstrap. See [deployment and rollback](NATIVE_DEPLOYMENT_REVIEW.md).
