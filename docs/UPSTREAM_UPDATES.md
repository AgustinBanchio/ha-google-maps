# Auditing upstream updates

The current source pin is pnbruckner/ha-google-maps 2.1.0 at `ae85b249b354c25c2994cd1458231039e1dc977f`. The original 2.0.3 audit remains available at `b2132123d46c47e5761d5d91cc08ca6b712fe6c1`. Use the exact `baseline` recorded in [upstream-patch-boundary.json](upstream-patch-boundary.json) for the next comparison.

Do not enable automatic fork synchronization, auto-merge or floating collector images. A version tag is a label; record the full commit and image digest.

## Review procedure

1. Confirm the current tracker, last audit and installed collector version. Work on a review branch; keep the release branch unchanged during review.
2. Fetch metadata without merging:

```sh
git fetch upstream --tags
git log --oneline ae85b249b354c25c2994cd1458231039e1dc977f..upstream/main
git diff --stat ae85b249b354c25c2994cd1458231039e1dc977f..upstream/main
git diff ae85b249b354c25c2994cd1458231039e1dc977f..upstream/main -- custom_components/google_maps .github
```

3. Inspect the actual code, new files, manifest/dependency changes, build steps and destinations; do not rely on release notes alone. Trace cookie handling through HTTP, persistence, errors, diagnostics and management endpoints.
4. The deployed native integration uses the original HA entities and Maps client, with the external-session patch documented in UPSTREAM_PATCH.md. Review/reapply that source/authentication patch onto the reviewed upstream revision. Update the protected-file digests and identical vendored Maps client only after inspecting the changes; do not independently rewrite upstream tracker rules. Run both the protected-source guard and synthetic three-way update exercise, then the actual HA entity/options tests. Preserve fixed-origin transport hardening. The API and native adapter check the same upstream revision: changing it requires a coordinated collector/native rollout or an explicitly tested compatible protocol. A mismatched revision fails closed.
5. Independently review dependency/base-image security updates even when upstream integration files have not changed. Keep exact dependency hashes and base-image digests.
6. Run the security, parsing, corruption, timestamp, reconnect and restart tests in the current plan. Use dummy cookies and synthetic locations in CI.
7. Record the old/new full revisions, findings, unresolved limits and exact test evidence in a new audit document. Future reviews must include prior findings and responses.
8. Merge only reviewed changes under the owner's requested update scope. Build a pinned release, verify its contents, and seek any needed deployment approval only after the diff/tests/rollback are concrete.

No absolute safety guarantee is implied by review. If an update changes security boundaries or introduces a new service/permission, update the spec before deployment.
