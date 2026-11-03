# Upstream status check: 3 November 2026

Scope: read-only GitHub metadata and complete changed-file patches for the two open upstream PRs. No upstream code was incorporated, and no host inspection or deployment was performed. This is a candidate assessment, not release acceptance or a full security audit of an unreleased revision.

## Released source

The GitHub comparison of our audited baseline `b2132123d46c47e5761d5d91cc08ca6b712fe6c1` against upstream `main` returned `identical`, zero commits ahead/behind and no changed files. The latest main commit is still the 4 June 2026 version bump. Latest published release remains 2.0.3, published 4 June 2026. There is no new released or merged code to port.

References: [comparison](https://github.com/pnbruckner/ha-google-maps/compare/b2132123d46c47e5761d5d91cc08ca6b712fe6c1...main), [release](https://github.com/pnbruckner/ha-google-maps/releases/tag/2.0.3).

## New maintainer work: PR #62

[PR #62](https://github.com/pnbruckner/ha-google-maps/pull/62), opened 30 October 2026, is open and unmerged. Reviewed head: `7b77fd27cab1aa779269893320c738a0d3a85104`, branch `ha-version`; base is our audited baseline. Twelve files change across four commits.

- The useful compatibility candidate removes the deprecated tracker `battery_level` property and supplies the same value through `extra_state_attributes`.
- Recorder exclusions expand to battery level, charging and tracking type. Porting these would deliberately change recorded attribute history; review that separately from fixing the deprecation.
- README/HACS minimum HA version becomes 2026.7. Manifest gains the presence/location category. Other edits are typing/formatting changes.
- Separate sensors for battery level, address, last seen and GPS accuracy are unchecked in the PR checklist, and there is no sensor platform in the changed files. Do not describe them as implemented.
- The embedded Maps module only drops postponed annotations and replaces the standard-library cached_property import with propcache. Its HTTP, cookie handling and parsing logic are unchanged in this diff. A wholesale port would require declaring and pinning propcache in the standalone collector, which currently does not declare it.

Recommendation: monitor #62; if the owner requests an early port, audit a pinned revision and isolate the compatibility fix from optional history changes. Protected source digests, original-reference HA tests and revision coupling require deliberate review. A full baseline advance must keep both embedded client copies identical and coordinate collector/native revision checks. Existing transport hardening and the residual risks described by the 19 October audit remain relevant; this PR does not replace our external-session boundary.

## Older optional feature: PR #52

[PR #52](https://github.com/pnbruckner/ha-google-maps/pull/52), opened 26 May 2026, remains open and unmerged at head `fb450cc9ed07d463933dbeea7c571d43f8e5d91f`. It adds a number/input_number entity to control polling intervals dynamically, modifying config flow, constants, coordinator and translations.

Static findings: unavailable/unknown/removed entity states return without restoring the static fallback, despite the described behavior. Numeric conversion lacks finite-value and practical minimum/maximum checks; non-finite or oversized values can fail timedelta conversion, and arbitrarily small positive intervals are accepted. The event path also requests an immediate refresh on each accepted state change. This feature needs adaptation and actual HA scheduler/fallback tests before adoption; do not copy it unchanged. It predates our October audit and is not new since that review.

## Local evidence and next action

Local source reviewed at `c944d858a6d09d35e9ec9bfa31a0015ed4734092`. `python tools/check_upstream.py` passed: all five protected files match the audited baseline, and the vendored Maps client matches the integration copy. No runtime tests were run for these unreleased PRs; neither was applied locally. No current live version was re-verified; the tracker retains the last deployment evidence.

Exact next action: keep the existing release; recheck #62 when it changes or merges, or perform a scoped pinned compatibility port if the owner requests implementation. No implementation or deployment is pending from this status request. Follow `docs/UPSTREAM_UPDATES.md` before incorporating any code, including a review branch, exact diff, applicable tests and rollout/rollback review.
