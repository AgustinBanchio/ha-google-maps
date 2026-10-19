# Auditing upstream updates

Baseline: pnbruckner/ha-google-maps release 2.0.3, commit b2132123d46c47e5761d5d91cc08ca6b712fe6c1.

Do not enable automatic fork synchronization, auto-merge or floating collector images. A version tag is a label; record the full commit and image digest.

## Review procedure

1. Confirm the current tracker, last audit and installed collector version. Work on a review branch; keep the release branch unchanged during review.
2. Fetch metadata without merging:

```sh
git fetch upstream --tags
git log --oneline b2132123d46c47e5761d5d91cc08ca6b712fe6c1..upstream/main
git diff --stat b2132123d46c47e5761d5d91cc08ca6b712fe6c1..upstream/main
git diff b2132123d46c47e5761d5d91cc08ca6b712fe6c1..upstream/main -- custom_components/google_maps .github
```

3. Inspect the actual code, new files, manifest/dependency changes, build steps and destinations; do not rely on release notes alone. Trace cookie handling through HTTP, persistence, errors, diagnostics and management endpoints.
4. The deployed MQTT collector diverges from upstream. The owner now requires the source-preserving correction in COURSE_CORRECTION.md: use upstream HA entities and Maps client directly, with a small documented external-session transport/authentication patch. Until that correction is implemented, explicitly distinguish a manual collector port from an upstream update; do not claim automatic behavioural parity. After correction, review/reapply the small patch and run the actual upstream-entity equivalence tests. Do not overwrite transport hardening blindly.
5. Independently review dependency/base-image security updates even when upstream integration files have not changed. Keep exact dependency hashes and base-image digests.
6. Run the security, parsing, corruption, timestamp, reconnect and restart tests in the current plan. Use dummy cookies and synthetic locations in CI.
7. Record the old/new full revisions, findings, unresolved limits and exact test evidence in a new audit document. Future reviews must include prior findings and responses.
8. Merge only reviewed changes under the owner's requested update scope. Build a pinned release, verify its contents, and seek any needed deployment approval only after the diff/tests/rollback are concrete.

No absolute safety guarantee is implied by review. If an update changes security boundaries or introduces a new service/permission, update the spec before deployment.
