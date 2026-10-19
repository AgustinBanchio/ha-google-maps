# Set up the isolated collector

Local implementation, ARM64 container recovery and release checks pass. Real Google compatibility remains an owner session-import check. Check the current tracker for observed results. These instructions do not authorize Pi changes.

## Develop with synthetic data

From the repository root, install Python 3.13 and uv 0.13.1. Then run:

```sh
cd collector
uv sync --frozen
uv lock --check
uv run --frozen python -m google_maps_collector --help
uv run --frozen pytest -q
```

Tests use temporary directories, synthetic cookies and fabricated coordinates. No Google credentials are needed. On this Windows checkout uv and Python are isolated under ignored .local/; the existing runner can use .local/tooling/bin/uv.exe.

The bootstrap tests demonstrate first provisioning, a repeated call preserving every file, rejection of partial directories, and interrupted setup cleanup. Store/lifecycle tests demonstrate reconstruction with the same key and source timestamps. Container tests are a separate release requirement.

## Prepare a release

Keep custom_components/ at the audited baseline. Review docs/DEPENDENCIES.md and UPSTREAM_PROVENANCE.md. Build from the repository root with deploy/Dockerfile, passing SOURCE_REVISION as the full clean Git commit. Use a Linux Docker engine and test linux/arm64 startup before the Pi. The build context allowlist excludes .local/, cookies, tests and operational files.

Resolve the resulting registry image digest and retain the source revision, collector/uv.lock SHA-256, image digest, wheel hash and verification results in the private release record. A local image tag such as google-maps-collector:unreleased is for disposable checks only. Deployment uses a reviewed image@sha256 reference. No startup package installation occurs.

## Provision private files once

Only after the owner authorizes the collector deployment, choose a dedicated private host directory outside HA configuration, backups and agent workspaces. Review actual ports 1883 and 8787, tunnel routes and host permissions first. Use a Linux root shell solely to provision the assigned UID/GID ownership; run the installed Python 3.13 environment's interpreter explicitly:

```sh
/path/to/collector/.venv/bin/python tools/bootstrap_collector.py --directory /private/collector
```

The command prompts privately for a collector admin password of at least 12 characters. It creates a 32-byte store key, salted scrypt admin verifier, independent broker passwords, Mosquitto PBKDF2 verifiers and dedicated data directories. It prints only a completion code. On Linux the assigned collector files/data belong to 10001:10001; broker files/data belong to 1883:1883. The parent private directory remains administrator-controlled. Windows bootstrap is for synthetic development only; Unix ownership is not established there.

A repeated bootstrap preserves all existing files without prompting for a new password. Partial setup fails closed. Restore the complete original directory instead of generating a new key.

Create an ignored private Compose env file using deploy/collector.env.example. Set COLLECTOR_PRIVATE_DIR to the absolute provisioned directory and COLLECTOR_IMAGE to the reviewed image digest. The env file contains paths/settings, not passwords. Validate without starting services:

```sh
docker compose --env-file .local/collector.env -f deploy/compose.yaml config --quiet
```

The separate project is google-maps-collector. Both published ports bind 127.0.0.1. No HA mounts, privileged mode, host network or Docker socket is assigned. The collector can reach Google over its Docker network. Only an explicitly authorized deployment runs compose up; existing HA, Matter and OTBR services are outside this project.

## Import or replace a Google session

Open a normal interactive SSH session with a verified host key and forwarding disabled, adding a local tunnel:

```sh
ssh -a -o StrictHostKeyChecking=yes -N -L 8787:127.0.0.1:8787 <private-target>
```

For Windows background T3 access, follow OPERATIONS.md and its desktop-session helper; it is not a general SSH configuration fix.

Visit http://127.0.0.1:8787 and sign in with the collector admin password. Export a Netscape cookie file from the existing personal Google session using a tool you trust, and upload it through this page. The collector never requests your Google password. Export tools/extensions are outside the source audit. Keep temporary exports outside the repository and remove them when no longer needed.

Uploads, including multipart overhead, are limited to 1 MiB. Only approved secure Google-domain cookies are retained. The candidate is validated against the fixed Google HTTPS endpoint before the encrypted store and active session are replaced. A failed replacement preserves the saved session. Do not run the original integration as another session writer during acceptance.

The page shows only session status, last successful poll, contact count and approximate cookie expiry. Expiry does not guarantee session validity. Network/parser failures keep the saved credentials and retry; credential_required prompts replacement. Management login sessions expire after an hour and are lost on restart; Google session storage persists.

## Connect Home Assistant and People

After the owner authorizes HA configuration changes, add its MQTT integration using 127.0.0.1:1883, username homeassistant and the independently generated ha-password file. Enter the password privately in HA; never paste it into chat or commit it. The collector has a different publisher password and cannot subscribe to arbitrary state topics. HA receives only this collector's discovery/state topics and may publish homeassistant/status.

Each contact gets a stable opaque ID derived from its Google person ID. Devices use Google Maps <full name>, retaining existing opaque unique IDs/topics. Trackers are enabled and visible by default. Previously created hidden entities retain their registry setting: open the Maps location entity, select its settings gear, enable Visible and save. Keep the tracker enabled so People can use it. Each device also has Maps battery and Maps details. As upstream, profile/battery changes update tracker attributes while latitude, longitude and last_seen retain the accepted observation.

In Settings > People, attach the Maps and Companion App trackers to the same Person. Hide raw trackers on maps/dashboards as needed. Person matching is manual; names come from Google. HA selects among GPS trackers using its standard update rules; there is no guaranteed Companion App preference. Discovery/retained replay after reconnect can affect HA's own entity update time even though the source_timestamp is preserved. Assess this in actual HA acceptance. See the [MQTT tracker documentation](https://www.home-assistant.io/integrations/device_tracker.mqtt/) and [Person rules](https://www.home-assistant.io/integrations/person/).

As upstream, stationary/old fixes remain available and the last known location survives Google network/authentication errors. A successful response missing a contact starts a three-minute grace period before that contact becomes unavailable. The Maps session connectivity sensor reports polling failures separately. Optional FRESHNESS_SECONDS=300..3600 enables stricter age expiry; the default 0 preserves upstream behaviour. MAX_GPS_ACCURACY defaults to the upstream 1000-metre limit; newer inaccurate fixes cannot replace an accurate fix, and an inaccurate fix is replaced only by one at least as accurate. INCLUDE_ACCOUNT=false disables the optional account-holder tracker. MQTT location fields are deliberately shared with HA and its subscribers. Google names, nickname, profile image URL, address, country code, last_seen, battery level and charging state are intended private HA data. The tracker includes all these attributes and refreshes profile/battery fields as upstream does, preserving the accepted GPS observation and last_seen. Maps details also provides them as a timestamp sensor. HA may change its own last_updated when attributes change; this is distinct from Google last_seen. last_seen is an ISO 8601 UTC timestamp (HA displays timestamp sensors in local time); source_timestamp is the same Google observation in epoch seconds. Home/Away is the zone-derived state: latitude, longitude and gps_accuracy are entity attributes, available under Developer tools > States. An Account holder device appears if Google returns that optional location; Google does not supply its profile name/picture/battery in that record. Google cookies, authentication material and raw responses are never published.

## Release metadata validation

Run tools/validate_release.py --source-only --wheel collector/dist/google_maps_collector-0.1.0-py3-none-any.whl from the root through the collector environment to inspect locked distribution hashes, base-image pins and wheel contents. This does not validate a release image. The default command requires an ignored .local/release.json containing source_revision, lock_sha256, image, wheel, wheel_sha256, arm64_startup and container_recovery. The final two fields are recorded as passed only after their actual checks; attach the sanitized evidence to verification.md. The validator also requires a clean matching Git revision and locally inspected immutable image metadata.

## Prepared owner handoff

The current release was built on ARM64 and can be pinned by its exact local Docker image ID as well as a registry digest. It is retained on the Pi; no registry login or image publication is needed. The private release record identifies the matching clean code revision and wheel/lock hashes.

After persistent deployment is explicitly approved, tools/provision_collector.py can provision once and encrypt the generated owner passwords to an ephemeral workstation public key. The Pi keeps only the admin verifier; the workstation receives an owner-only ignored .local/owner-handoff/SETUP-PRIVATE.txt. Copy these owner credentials into your password manager, then delete the handoff. No plaintext password goes into SSH arguments/InputText, chat, Git or tool output.

From a normal desktop PowerShell session, tools/Open-CollectorTunnel.ps1 opens the verified SSH loopback tunnel using the existing private connection metadata and normal 1Password approval. Keep the terminal open while visiting http://127.0.0.1:8787.


Google profile photos belong to Maps location tracker entities and map markers, as in the original integration. HA's device registry does not have a per-device profile photo. The collector sets the tracker's entity_picture in MQTT discovery, because HA ignores that reserved field in JSON extra attributes. Refresh the tracker dialog/map after a collector update; an Account holder record has no Google-supplied picture. Attaching a tracker to an HA Person does not automatically set that Person's profile photo.
