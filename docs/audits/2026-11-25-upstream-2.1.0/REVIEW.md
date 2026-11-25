# Google Maps 2.1.0 audit and coordinated rollout

The owner approved porting the full published 2.1.0 release while retaining this fork's collector-owned session. The 2.0.3 source pin was `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`. The new source pin is `ae85b249b354c25c2994cd1458231039e1dc977f`. The release consists of the [#62 implementation](https://github.com/pnbruckner/ha-google-maps/commit/338f975a282bda1cf5a7aca765f69418c619ae25) and the version bump. Review covered the [13 changed files and both commits](https://github.com/pnbruckner/ha-google-maps/compare/b2132123d46c47e5761d5d91cc08ca6b712fe6c1...ae85b249b354c25c2994cd1458231039e1dc977f) plus the reapplied fork patch.

## Release behavior

- The tracker still exposes `battery_level` as a live state attribute. HA's recorder now excludes battery level, charging and tracking type from tracker attribute history. Battery has a dedicated sensor enabled by default. Address, GPS accuracy, last seen and location age sensors are disabled by default. The location sensors show observations before the tracker's accuracy and timestamp filtering.
- Disabling polling leaves manual tracker updates available. A manual location-age refresh only recalculates age. Options use HA's reload helper. Reauthentication with an unchanged data key still reloads the integration so a recovered external session can resume an entry that failed setup.
- The fork adopts the upstream HA 2026.7 minimum and the presence/location category. Config entry version, tracker IDs and the loopback API schema remain compatible with existing configuration. Two local tracker fixes preserve hyphenated person IDs in sensor registry lookups and skip removal of sensors that HA never attached. The missing-contact removal issue was reproduced on actual HA 2026.10.1.

## Session boundary

The fork still configures the collector endpoint and its scoped data key in HA. The config flow has no cookie upload, and native setup, migration and unload do not read or delete Google cookie files. The collector uses the same fixed Google origin, TLS checks, redirect rejection, response bound, sanitized errors, cookie-rotation logic and encrypted storage. The embedded Maps client diff only removes postponed annotations and switches `cached_property` to `propcache`. Both client files are identical and the standalone collector pins `propcache==0.5.4` with distribution hashes. The lock update leaves the other dependency pins and base image digests in place.

The two components enforce the same exact upstream revision through `/v1/locations`. A mismatched pair rejects location updates while an already-loaded tracker retains its last known location. The HA config entry, scoped key, encrypted state, store key and admin verifier carry forward. A valid saved Google session works without uploading cookies again. Guest or hostile code on the privileged Pi remains subject to the original host trust limits. See [the 2.0.3 audit](../2026-10-19-upstream-2.0.3/REVIEW.md) and [project security context](../../PROJECT_CONTEXT.md).

## Verification

- Actual HA 2026.10.1 at image digest `sha256:130241f28d01fa80dfa3b44f7d89781c188d8642ecab9024f079f19f9f82baa0`, with its network disabled and synthetic inputs, passed 11 scenarios. Coverage includes sensor defaults and raw values, filtered tracker preservation, battery attributes, manual polling, missing-contact restoration, account entity cleanup, migration, reloads and mixed-revision rejection/recovery.
- Windows collector tests passed 134 with two broker tests skipped. The Linux suite with a disposable broker passed all 136. Both exercised the guarded request path, scoped credentials, redaction and persisted rotation. The existing Starlette test-client warning remains.
- Cross-version check used collector source from the last verified deployment `ce0c2bfeb551df90a2bbe15e29847a5d2902a684` to create a synthetic encrypted session. The new collector accepted the same data key, polled using the restored cookie jar and saved a synthetic Google cookie rotation. The previous source then reopened that state and polled using the rotated jar and original data key. Key file hashes matched throughout. No production credentials, location data or services were used.
- The pinned-source guard, synthetic three-way update, frozen lock check and collector wheel validation passed. The OSV audit reported no known advisories or adverse project status for the 17 locked runtime packages checked.
- Local Docker could not execute the pinned ARM64 base image. Native ARM64 production-image recovery is checked by the repository's Collector workflow.

## Deployment and rollback

Deployment requires owner approval for replacing the collector container and restarting HA once. Prepare the native ZIP and a production ARM64 collector image from the same clean fork revision. Record their hashes and verify the collector image's architecture, exact source label and existing non-root user. Retain the currently deployed collector image, native component and encrypted state backup. Confirm HA meets the 2026.7 minimum and keep the existing Compose projects, private path and HA config mount.

1. Stage the verified native component and collector image. Keep the existing encrypted session storage, store key, management verifier and scoped HA data key. The normal upgrade does not reprovision credentials.
2. Replace only the collector with the reviewed pinned image in the existing native-only Compose project. Install the verified native component in the persistent HA config mount and restart only HA. The brief mixed-revision window can interrupt live location updates. Keep rollback ready until both sides agree.
3. Check collector health and the HA online sensor, then confirm an authenticated update, existing tracker IDs and People links, plus the default battery sensor and the disabled defaults for the other new sensor types. Report aggregate results only.
4. If acceptance fails, restore the prior collector image and native component together and restart only HA. Keep the current encrypted session and keys if readable. The prior collector can consume state rotated by the new one, as tested above. Keep the encrypted snapshot available for a storage recovery; restoring an older jar may require renewal if Google has revoked it. The restored component can ignore 2.1.0 sensor registry rows. Clean up any leftover sensor rows only through HA's supported registry controls as needed.

No production rollout or credential refresh was performed for this port.
