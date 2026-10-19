# Deployment review: not yet ready for authorization

The proposed addition is exactly the separate project in deploy/compose.yaml: a collector running as 10001:10001 and an authenticated Mosquitto broker as 1883:1883. Published ports are 127.0.0.1:8787 and 127.0.0.1:1883. Dedicated private directories contain the key/encrypted store, assigned secrets and broker data. Both services have read-only roots, dropped capabilities and no privileged mode, host network, host PID, Docker socket or HA mounts.

No deployment is requested yet. Task 4.1 is blocked on the missing local Linux Docker engine. Container/ARM64 startup, broker ACL/restart and actual recreation evidence must pass before this becomes an approval-ready proposal. There is no collector release image digest yet; the pinned Mosquitto/Python/uv base digests do not substitute for it.

Before requesting approval, add the exact clean source revision, built collector image digest, complete current-session test evidence, selected private host paths/ownership, available ports, relevant tunnel/Access findings, original stack health checks and the intended collector-only start/recreation commands. Keep raw host identifiers/configuration in .local/.

Rollback is to stop only this new project, preserve its complete data/key and broker identities, and restore the previous reviewed image/compatible backup as described in RECOVERY.md. Existing HA/Matter/OTBR, SSH, tunnels, firewall and host services are outside the proposed diff. HA MQTT/Person setup and a full Pi reboot require their applicable explicit authorization. No real credential belongs in this review or chat.
