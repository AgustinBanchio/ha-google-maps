# Add the deployed collector to Home Assistant

The separate collector and MQTT broker are running on the Pi. Existing HA, Matter Server and OTBR containers and permissions are unchanged. No Home Assistant restart is needed for MQTT setup.

1. Open the private credentials file on the Windows workstation: `.local/owner-handoff/SETUP-PRIVATE.txt`. It contains the collector admin password and the separate HA MQTT password. Save them in your password manager, then delete this temporary handoff file. Never paste them into chat.
2. In a normal desktop PowerShell 7 terminal at this repository, run `./tools/Open-CollectorTunnel.ps1`. Approve normal 1Password SSH authentication if prompted. Keep the terminal open and visit http://127.0.0.1:8787.
3. Sign in with the collector admin password and upload a Netscape-format cookie export from the existing personal Google session. Do this only through the private page. Confirm session status becomes ready and the last-successful-poll/contact-count fields populate. The cookie expiry date is approximate. Relevant external tunnel/Access policies were not independently verified; neither new port has been exposed publicly by this deployment.
4. In HA, open Settings > Devices & services > Add integration > MQTT. Use broker `127.0.0.1`, port `1883`, username `homeassistant` and the MQTT password from the private handoff. If HA already has a different MQTT broker configured, preserve that existing configuration and reconcile the broker setup before replacing anything.
5. The session sensor should appear immediately. Contact GPS trackers and separate battery sensors appear after successful Google polling. Trackers are enabled but hidden by default. Rename them privately and attach the Maps tracker alongside the Companion App tracker in Settings > People. HA's normal GPS-source selection applies; there is no forced Companion App preference.

This collector uses HA's standard MQTT integration. Do not add the original cookie-based Google Maps custom integration for the same session: the collector must remain its only writer. Keep exported cookies outside Git/chat/HA backups.

If upload is rejected, the saved session is retained. Record only the fixed error/status code; do not share the cookie file. See SETUP.md and RECOVERY.md for details. No Pi reboot, Docker daemon restart or existing Compose changes are part of these steps.
