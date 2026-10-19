# Recovery and rollback

Use only the separate google-maps-collector Compose project. Deployment, targeted changes and full Pi reboot require the applicable owner authorization. Do not restart HA, OTBR, Matter, SSH, tunnels or host services as a recovery shortcut.

## Normal restart

Collector recreation reuses the assigned key, encrypted session, source timestamps, broker password files and persistent broker data. Management login sessions are intentionally lost. Reopen the SSH tunnel and sign in again; Google cookies should not need another import. Startup fails closed when the key/store cannot be read or authenticated.

Network failures retry with bounded exponential delay, up to one hour. A session revocation or rejected redirect produces credential_required while preserving the encrypted file. Import a replacement through the authenticated page. Failed replacements leave the old session intact. Malformed Google responses have a separate parser_failure status.

## Backup and key recovery

Keep the encrypted session, store key, admin verifier, broker secrets, broker data and release record outside ordinary HA backups. Protect a recovery copy separately and preserve file ownership/modes. A copied jar alone is encrypted; a copy with its key can be decrypted. Host administrators and privileged host code remain trusted.

Restore the complete key/store pair and existing broker identities. Do not run bootstrap to repair a partial backup or replace a missing key. A wrong key, tampering or unsupported store version must be investigated without deleting the original files. Store copies and raw operational reports belong only in private storage, never public issues or Git.

## Targeted rollback

Before changing a release, record the previous immutable image reference and back up the complete private data while the new project is stopped. On an authorized rollback, restore the previous reviewed image reference in the ignored Compose env file and recreate only this project. Preserve the encrypted store/key and broker identities. Avoid compose down --volumes and never remove the private data directory as routine recovery.

If a format change makes the previous release incompatible, restore its matching complete backup while the collector is stopped. Verify ownership, health, the four management status fields, stable tracker IDs and stale availability before enabling automations. Do not publish logs or dumps containing locations or credentials.

A full Pi reboot is a separate acceptance action. Obtain explicit authorization and establish console/recovery access first. Confirm the original smart-home services and collector recover, and record only sanitized evidence in verification.md.

## Local synthetic recovery checks

From collector/, uv run --frozen pytest -q tests/test_bootstrap.py tests/test_store.py tests/test_service.py exercises repeat setup, interrupted persistence, tampering, wrong keys, timestamp restoration and rejected credential replacement in disposable temporary directories. This is local code evidence; it does not prove container recreation, ARM64 startup, HA behavior or Pi reboot recovery.
