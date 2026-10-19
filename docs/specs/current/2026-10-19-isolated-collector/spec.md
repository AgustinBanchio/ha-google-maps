# Isolated Google Maps collector: specification

Status: agreed direction with explicit implementation defaults. Fork/preparation is authorized; substantial implementation begins on the owner's next instruction. Remote deployment is separately authorized.

## Goal

Use the owner's existing Google session to collect already-shared Maps locations, while keeping that session out of HA's normal files/process and preserving reliable People tracking after routine restarts.

## User stories

- As the owner, I import an existing session through a small private UI and see whether it works.
- As the owner, I restart the Pi, Docker or the collector without re-entering cookies.
- As an HA user, I attach Maps and Companion App trackers to one Person without duplicate map device entries.
- As the owner, I request an upstream audit before any fork update is merged or deployed.

## Non-goals

No official Maps OAuth/API promise, new Google account, automatic contact reshare, automatic Google login, continuous headless browser, public credential UI, arbitrary HTTP proxy, host administration from the collector, existing HA/Thread changes or protection from host administrators. Do not implement automatic Person identity matching or source priority beyond HA's standard Person selection.

## Acceptance criteria

- [ ] AC1: A separate non-root ARM64-capable collector uses the existing personal session; Google credentials never enter HA, MQTT, logs or diagnostics.
- [ ] AC2: Authentication uses only the exact approved Google HTTPS origin, certificate verification, cookie-domain filtering and unexpected-redirect rejection.
- [ ] AC3: The persistent cookie jar is authenticated-encrypted; missing/wrong keys and tampering fail closed without erasing a valid store. Normal restart reuses the same key/store.
- [ ] AC4: An authenticated, loopback-bound upload UI validates cookies in memory and atomically replaces the saved session only after a successful Google validation. Invalid replacement retains the previous session.
- [ ] AC5: The UI never asks for a Google password, exports cookies or exposes an arbitrary request endpoint. Upload limits, CSRF/origin protection, throttled login and redacted errors are tested.
- [ ] AC6: Source session revocation produces credential-required status and a recoverable replacement path; transient network errors retry without deleting credentials.
- [ ] AC7: Stable MQTT GPS trackers and separate battery/status sensors recover after broker/HA restarts and remain attachable to HA Persons. Trackers are visible and enabled by default, and expose all upstream person/location fields.
- [ ] AC8: Older/same-timestamp fixes are not republished as newly observed locations because of battery-only changes. Stale fixes become unavailable after the configured TTL.
- [ ] AC9: Collector/broker recreation, a targeted restart and an interrupted save preserve credentials/identity, and full Pi reboot recovery is demonstrated only with owner authorization.
- [ ] AC10: Compose isolates the new service's data/secrets, omits privileged mode/Docker socket/HA mounts, and provides authenticated least-privilege MQTT access.
- [ ] AC11: Canary credentials/locations do not appear in logs, management errors, MQTT or release artifacts outside the explicitly permitted person/location fields.
- [ ] AC12: Releases retain dependency hashes, source revision and image digest; upstream merge/deploy is manual and follows the audit procedure.

## What

The collector polls Google every 60 seconds by default, using bounded retries/backoff. It retains rotated cookies atomically. No-data, malformed-response, network-failure and invalid-session conditions remain distinct.

Management runs on container port 8787, published only to host 127.0.0.1:8787. The owner accesses it over SSH. It shows session status, last successful poll, contact count and an explicitly approximate cookie expiry date. There is no need to show contact names, coordinates or cookie contents in management responses.

A browser login uses a separate collector-admin password, never the Google password. The bootstrap command provisions that password privately from terminal input or the approved secret-entry mechanism. Persist only a salted scrypt password verifier. Issue random session IDs in HttpOnly, SameSite=Strict cookies, keep management sessions in memory, require a session CSRF token on uploads and validate Origin/Host. After a restart the owner may need to log into management again; Google authentication remains persisted. Do not put passwords/session tokens in URLs. Throttle failed login by a bounded per-client policy.

Limit cookie uploads to 1 MiB including multipart overhead, with a streaming bound even if Content-Length is missing or dishonest. Parse Netscape-format cookies in memory; accept only Google-domain cookies needed by the client, preserve secure/domain/path attributes and never pickle/execute input. Validate through the approved origin before committing. Concurrent polling/import is serialized around the active cookie jar.

Persistent store format is versioned JSON containing an AES-256-GCM nonce/ciphertext and store version as authenticated data. Use cryptography, unique nonces, a pre-provisioned 32-byte key and atomic durable writes. The key is a protected host file mounted read-only into the collector; it is never generated anew at normal startup. Both the key and encrypted store survive Compose recreation. Encryption protects a store copied alone, not an administrator who can read the key and process.

## MQTT contract

Use Mosquitto 2 with authentication and persistence as the default provided broker; pin the actual supported image digest during implementation. Publish the broker only on host loopback port 1883; the collector reaches it over its Compose network. HA uses its existing host network to connect to 127.0.0.1:1883. Recheck port availability before deployment.

Use a collector-specific authenticated publisher and a separate HA subscriber. Collector ACLs permit only its discovery/state/availability topics and subscription to homeassistant/status. HA may subscribe to discovery and google_maps_collector state and publish its standard birth message. No collector command channel, generic proxy or credential-return API exists.

Discovery topic shapes:
- homeassistant/device_tracker/google_maps_collector/<stable-contact-id>/config
- homeassistant/sensor/google_maps_collector/<stable-contact-id>-battery/config
- homeassistant/binary_sensor/google_maps_collector/session/config

State topics live below google_maps_collector/. Derive stable opaque IDs from the upstream Google person ID; do not expose account email in topic names. Do not use display names for identity. Device tracker location attributes include latitude, longitude, gps_accuracy and source timestamp. Keep battery updates on a separate sensor so they do not make an old GPS fix appear newly updated. Include upstream full name, nickname, profile picture URL, address, last_seen, battery level and charging state in each GPS snapshot; publish current metadata independently through a Maps details timestamp sensor. Also preserve country_code from the upstream parser. Include account-holder GPS data if returned, with a local stable ID and generic Account holder label because no account profile is supplied. Names/locations are intended HA data; only authentication material is isolated. Existing IDs/topics remain stable.

Set source_type=gps, visible_by_default=true and enabled_by_default=true. Provide discovery/availability retention and last-will status. Persist broker data and the collector's last source timestamps. Republish discovery on broker reconnect and HA birth; never reset the source observation time. Default freshness TTL is 15 minutes, configurable from 5 to 60 minutes. Global credential-required status and per-contact stale status must not misrepresent a stale retained location as current.

HA Person linkage is manual through Settings > People. Multiple GPS sources use HA's standard most-recently-updated selection; there is no guaranteed Companion App preference. Document the consequences and allow owners to hide raw trackers if they prefer; keep them enabled.

## How

Use Python 3.13 and a src layout at collector/src/google_maps_collector. Package with pyproject.toml and uv.lock. Exact currently supported dependencies and hashes are reviewed in Task 1.1; expected runtime dependencies are requests, cryptography, paho-mqtt, starlette, uvicorn and python-multipart. Test dependencies include pytest and httpx. Do not install dependencies at container startup.

Keep the original custom_components/google_maps runtime unchanged during initial collector implementation. Extract from gm_loc_sharing.py with pinned provenance; add hardening in the collector copy and maintain a reviewable upstream delta.

Deployment files live in deploy/. Use a separate Compose project named google-maps-collector. Collector UID/GID is 10001:10001, read-only root filesystem, temporary tmpfs, dropped capabilities, no-new-privileges and no host PID/network or privileged access. Only its persistent store and assigned secret files are mounted. The broker has a persistent data volume and its own restricted configuration/auth files. Do not mount Docker, HA config or agent workspaces.

## Constraints and accepted risk

The observed HA container is root/privileged and the host's administrative tools can sudo/use Docker. The user accepted this host as trusted. This plan reduces accidental exposure but cannot protect the cookie from hostile code controlling that host.

No existing service privileges, SSH settings, firewalls or tunnels may change under initial implementation. The UI must not be added to Cloudflare Tunnel. Cloudflare Access/router policies are unverified; confirm relevant exposure before deploying credentials.

## Test plan

Synthetic cookie/location fixtures only in source control. Test actual HTTP request construction/redirects with intercepted transports, store tamper/corruption/interrupted persistence, credential replacement races and failures, UI authentication/CSRF/upload bounds, canary redaction, MQTT ACLs/discovery/freshness and service recovery against a test broker. Test image startup on ARM64 before Pi deployment.

Host acceptance must target only the new Compose project. A full Pi reboot requires explicit owner approval and a recovery path; record evidence in verification.md. No automatic reboot is part of CI or normal validation.

## Open questions

No unresolved product choice blocks implementation. Operational facts to verify before deployment are documented in ENVIRONMENT_ASSESSMENT.md: port availability, exact mounts/permissions, relevant tunnel routes/Access policies and owner's deployment authorization. These are deployment preconditions, not assumed findings.
