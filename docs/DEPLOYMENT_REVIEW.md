# Collector deployment proposal

Deployed 19 October 2026 after the owner explicitly approved only this separate project and its private credentials. The earlier automatic-review block is resolved. No real Google session has been supplied; HA setup remains an owner action.

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
