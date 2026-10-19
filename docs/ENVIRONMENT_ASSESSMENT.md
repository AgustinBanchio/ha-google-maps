# Environment assessment

Read-only observations from 19 October 2026. Private identifiers, exact local paths and raw outputs live only in the checkout's ignored .local directory.

## Confirmed

- The target is a 64-bit Raspberry Pi running a rootful Docker daemon enabled at boot.
- The host administrative user belongs to Docker/sudo groups and has passwordless sudo.
- One Compose stack contains HA, OTBR and Matter Server. All use host networking and restart: unless-stopped.
- HA 2026.10.1 runs as root, privileged, with writable configuration/media bind mounts and read-only host D-Bus. No Docker socket mount was present in its inspected mount list.
- OTBR is privileged with the Thread radio and TUN device assigned.
- Matter Server is not privileged and uses a non-root user.
- Five custom integrations were inventoried by manifest only. Their source and dependencies were not audited.
- HA listens on all IPv4/IPv6 interfaces. Other smart-home/monitoring services also have network listeners.
- Cloudflare Tunnel processes are active. The system tunnel service has no configured user or restrictive systemd sandbox settings in the properties inspected.
- T3's user service and coding tools run under the administrative host user. Inspected T3 service properties did not enable NoNewPrivileges, ProtectHome, ProtectSystem or PrivateTmp.
- SSH enables public-key and password authentication. Root login is allowed by keys, not passwords.
- No MQTT container or listener on 1883/8883 was observed.
- UFW is not installed. The nftables snapshot contains Docker/Thread forwarding/NAT rules and no input-hook filter chain was seen in that snapshot.

## Not established

Cloudflare public routes and Access authentication policies could not be verified from the standard local configuration paths. No claim is made that the tunnels are unauthenticated or that the host is directly public. Router forwarding, upstream firewalling, legacy firewall layers, all IPv6 reachability, HA MFA/account settings and vulnerability status of other integrations were not assessed.

A firewall forwarding drop policy does not by itself establish protection of host-network services. Likewise, binding to all interfaces does not establish internet reachability.

## Consequences

A private collector container on this host reduces ordinary file sharing but is not a strong boundary against the privileged HA container or host administrators. Credential encryption at rest with a boot-readable key is additional protection against a jar copied alone; it is not host-compromise protection.

Do not expose the credential UI through the existing tunnels by default. Use a loopback-bound UI over SSH and normal authentication. Verify routes/Access policies and the exact proposed Compose diff before any deployment.

Host hardening, SSH password changes, HA/OTBR privilege changes and network changes are separate, staged work. No services were changed or restarted during inspection.
