# Collector deployment proposal

Deployed 19 October 2026 after the owner explicitly approved only this separate project and its private credentials. The earlier automatic-review block is resolved. The owner has since imported the Google session and configured HA MQTT. The upstream-parity collector update described below is now deployed and verified.

## Exact proposed addition

- Separate Compose project: `google-maps-collector`, using `deploy/compose.yaml` only.
- Collector: immutable locally built ARM64 image `sha256:e543a5ea5d8fe2597468d546d8fb01a24bc7f2b548349a8c41fb60d67084abd3`, source `ce2f19ecf99c2dc90d54a8a54e2a3ce30b27bc01`, UID/GID 10001:10001, read-only root, dropped capabilities, no-new-privileges, dedicated data and assigned read-only secrets.
- Broker: pinned Mosquitto image already in compose.yaml, UID/GID 1883:1883, authenticated separate collector/HA accounts, restricted ACLs and its own persistent data.
- New host listeners: `127.0.0.1:8787` management and `127.0.0.1:1883` MQTT. Both ports were free during selected inspection; recheck immediately before start.
- New private directory: a dedicated directory under the administrator's home `.local/share/google-maps-collector`, outside HA configuration and its Compose stack. The exact absolute path stays private.
- One-time provisioning generates only this project's store key and passwords. Only a salted scrypt admin verifier persists on the Pi. Owner passwords are encrypted to an ephemeral workstation recipient public key for transfer and saved in an owner-only ignored handoff file; no plaintext secret travels through SSH commands/InputText or tool output. No real Google cookie is created or read.

The proposed start is `docker compose --env-file <private-env> -p google-maps-collector -f deploy/compose.yaml up -d`, from the separate source checkout, after config validation and one-time provisioning. It does not run against the existing Compose files.

## Fresh evidence

The Pi's disposable ARM64 broker suite passed 76 tests. The production image recovery harness passed startup as UID 10001, synthetic import, actual broker restart, recreation of both new containers, same store key/source timestamp/stable contact identity, rejected replacement, stale availability and log canary checks. The ephemeral test project was removed.

Release validation passed with the source revision, image identity, lock hash and wheel hash retained in the private release record. GitHub HACS, hassfest, Linux/Windows unit and broker checks passed. All three pre-existing containers retained identical IDs, start times, restart counts, status, privilege and network/project metadata before/after testing. No HA/Matter/OTBR permission or Compose change occurred.

## Completed deployment checks

The original three-container baseline and free ports were checked before provisioning. Only this project was started and recreated. Collector health, unauthenticated HTTP 401, effective user/read-only mounts/capabilities, loopback listeners, MQTT subscriber authentication/retained discovery and unrelated-write denial all passed. The new key survived recreation; the original three-container baseline still matches exactly. No reboot occurred. Owner credentials were delivered encrypted into an owner-only ignored workstation file, and the ephemeral private key was removed.

Owner action then remains: use the SSH management tunnel, upload the Google session privately, add HA's standard MQTT integration with the separate subscriber credentials, and manually attach discovered trackers to People. Live Google compatibility, actual HA Person behavior and tunnel/Access exposure policy confirmation remain owner-dependent. No custom Google integration containing cookies is required in HA.

## Rollback and exclusions

Rollback stops/removes only `google-maps-collector` with its own env/file/project options. Preserve the complete new private directory and image identity; do not use volume deletion. The existing smart-home stack is never included in that command.

No change or restart to HA, Matter Server, OTBR, Docker daemon, firewall, SSH, tunnel services or existing privileges is proposed. No Pi reboot is proposed or authorized. Trusted-host limitations remain accepted.

## Authorized upstream-parity collector update

Owner requested original HA data and behaviour with safer credential handling. Candidate source c2be4af5a342f9d4f357bd34ac18a5995cada1da; immutable ARM64 image sha256:d9788abc10c012248e1d612494c2aa1091dd3817639933422dabfe77d9036c6c. Fresh disposable ARM64 suite, extended synthetic recovery harness and release metadata validation all passed; GitHub Collector and Validate workflows passed.

Only the collector is stopped briefly for an encrypted-data backup, then recreated with `up -d --no-deps collector`. The production broker and original three smart-home containers are not restarted. Credentials, private mounts, privileges, listeners and existing Compose stack remain unchanged. No bootstrap or new credentials are needed. Defaults restore original GPS accuracy selection, last-known availability and missing-contact grace; all upstream person fields reach HA with stable existing IDs.

Rollback retains the old immutable image, ignored env and encrypted data backup. Stop only collector, restore its matching encrypted data with original ownership, restore the old image/env with FRESHNESS_SECONDS=900 (required by the old image), then recreate only collector. Existing keys and broker credentials stay in place. The added Maps details entities may remain registered after image rollback; original tracker identities are unchanged. No key/store values or real names/locations are returned in verification; inspect only aggregate MQTT completeness and selected baseline metadata.


Update completed: only collector was replaced. Its existing encrypted session and credentials loaded successfully; all five named location payloads have complete upstream attribute schemas and four shared-contact profile images. Original tracker IDs are preserved, the broker is unchanged, and all three original service baselines still match. Private rollback evidence is retained outside Git. Remaining owner action is the HA Visible toggle/map/Person check; no credential re-import is required.
