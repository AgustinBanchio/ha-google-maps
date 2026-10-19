# Native integration deployment review

The replacement preserves the original HA entity modules and policy at upstream `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`. Only its account/source seam changes. The separate service owns Google cookies and returns original upstream observations over a scoped local API.

Tested source: `86f69835e00fba2f9e619a5267cb62d4ee352d83`. ARM64 image: `sha256:7ec36e9e72da239f6f5071d81076e957b37bd9b0a158bef67c27f2916c354baa`. Native ZIP SHA256: `274d9d9ece4b545a2983cbc0a753c35fd2492f16a399c47c309b3c190a29f3b4`.

Verification: 110 local tests passed; seven actual HA 2026.10.1 runtime scenarios passed; five ARM64 acceptance groups passed, including broker-free service operation. Upstream protected-source and synthetic update guards pass. CI passed for the tested commit.

## Collector deployment, already authorized

1. Check the original three-container baseline, working collector/broker metadata and clean source/release validation.
2. Generate only a new scoped data key. Do not read existing credential files. Deliver the new key encrypted to a temporary owner public key and decrypt only in ignored owner-only local handoff storage.
3. Stop only the collector, back up its encrypted data directory and image-only environment file, then update its source/image. Retain the production broker and MQTT publishing during migration.
4. Start only the collector with `up -d --no-deps collector`. Verify readiness, existing MQTT identities, scoped API authorization and aggregate live upstream record counts. Confirm HA/Matter/OTBR and the broker remain unchanged.

## Native HA installation and migration

This is a separate operational change from collector deployment. It writes only `custom_components/google_maps` in HA's configuration directory and requires one targeted HA restart to load the custom component. Back up any existing component directory before replacement. Do not change the existing Compose file, mounts, privileges, permissions, Matter Server, OTBR, firewall, SSH or host services. No reboot.

1. Verify the tested ZIP hash and install its public source files. Restart only HA after applicable authorization.
2. In HA's supported Google Maps configuration flow, enter the privately supplied account email, `http://127.0.0.1:8787` and the new scoped data key. Google cookies and the collector management password are never entered in HA.
3. Configure the original account-holder, accuracy and polling options. Verify named native trackers, pictures, GPS and connectivity. Google may omit the account holder's own GPS/picture/battery, as in the original integration.
4. Review old MQTT-to-native tracker correspondence privately. Select the native trackers in HA People and update relevant automations/dashboard references. Do not assume platform entity IDs transfer automatically.
5. Keep the working MQTT path until native tracking and links are confirmed. The separate native-only Compose file is ready for the subsequent collector switch. Broker removal and retained discovery cleanup are deferred until migration is accepted; unrelated MQTT integrations remain intact.

## Rollback

Collector: stop only the new collector, preserve its failed-state directory separately, restore the encrypted data backup and previous environment, select the retained verified rollback image from the private release record, restore the previous source revision, and start only the collector. Do not assume an old untagged image ID still exists; both current and rollback images are retained with release tags. Keep the old image and new scoped key; never overwrite existing Google/store/admin/broker secrets. Verify health/MQTT and the original baseline.

HA: remove the new component directory (or restore its previous backup), then restart only HA if necessary and restore previous Person/automation tracker selections through HA's supported UI. Keep MQTT running throughout initial migration. No host reboot or existing-stack Compose operation is required.

Private operation scripts record stage/result metadata, never cookies, tokens, names, coordinates or raw host reports in this public repository.

## Executed installation evidence

The owner explicitly approved installing our fork and restarting only HA. The scoped API release is running; the real native client verified four shared people with names/pictures and five valid GPS records including the optional account observation. The old five MQTT tracker IDs were preserved. Before the approved HA restart, all three original containers and the broker matched baseline. Afterwards HA's identity, network and privilege settings remained unchanged, while Matter Server/OTBR and the broker remained untouched. HA's frontend returned HTTP 200.

The native ZIP was hash-checked and installed into the existing persistent `/config` bind mount. No existing component was overwritten. Ordinary HA Compose recreation retains this directory. The new key was delivered privately and its temporary handoff decryption key was deleted. The real setup flow completed with the original account-holder option enabled, 1000-metre accuracy and 60-second update period. Five named native trackers have coordinates, four profile pictures load, connectivity is on, and the live map includes all five People. All five Person links were migrated using exact Google-identity correspondence; their other trackers, names and user associations were preserved. No indexed automation/script/scene references remained on the 16 legacy entities; seven available dashboard configurations had no references. The default dashboard had no stored configuration. All legacy entities were disabled through the supported registry API. The collector then switched to native-only Compose without a mounted MQTT credential; its API and HA connectivity remained healthy. The broker, Matter Server and OTBR remained unchanged and HA had no further restart. Private supported-API rollback snapshots are retained locally.
