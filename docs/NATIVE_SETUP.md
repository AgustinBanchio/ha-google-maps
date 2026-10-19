# Native Google Maps integration with an external session

This fork uses the original Google Maps HA entities and options. Google cookies are imported only into the separate external session service, never HA. The source-preserving adapter is under implementation; use the active tracker for verification/deployment status.

After the tested session-service release and native integration are installed, add Google Maps in HA. Enter your existing Google account email, local collector address http://127.0.0.1:8787 and its dedicated data access key. The data key is separate from Google cookies and collector management credentials. Configure the original account-holder, maximum GPS accuracy and update-period options. Profile names/pictures and reporting use upstream entity code.

## Missing Data for Account Tracker

Google may omit the account holder's own location and does not supply its profile picture/battery in that record. As upstream, its tracker uses the configured account email for identity/name. Contacts retain their original Google IDs and fields.

## Session replacement

Open the private management tunnel and import a renewed Google cookie export at the external collector. Reload Google Maps or retry its reauthentication flow after the service reports ready. Google cookies must never be pasted into HA's data access key field.

## Existing MQTT installation

Do not remove or replace the existing MQTT integration blindly. A supported migration needs a reviewed mapping of old tracker entity IDs and HA Person/automation links; MQTT platform identities do not automatically become Google Maps identities. Keep the old service release and encrypted state backup until native tracking is verified. Read the active implementation tracker and deployment review before changing production.

No HA/Matter/OTBR Compose or Thread permission changes are required. Installing a custom integration can require a targeted HA restart; this is a separate operational action from preparing code/tests. Do not reboot the Pi or restart other services.
