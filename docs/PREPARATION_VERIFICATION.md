# Preparation verification

Verified on 19 October 2026. Scope: fork and resumable project handoff, not collector implementation or deployment.

## Passed with fresh evidence

- The authenticated GitHub CLI account is AgustinBanchio; GitHub reports AgustinBanchio/ha-google-maps is a public fork of pnbruckner/ha-google-maps.
- The local directory D:/repos/ha-google-maps is a Git checkout with origin pointing at the owner fork and upstream pointing at the source project.
- git diff --exit-code b2132123d46c47e5761d5d91cc08ca6b712fe6c1 -- custom_components hacs.json succeeds. The upstream integration runtime is unchanged.
- PowerShell parsed both operational helpers without syntax errors. The copied generic helper successfully executed hostname and uname -m over SSH on the Pi using the existing 1Password agent. Temporary helper tasks were removed, and the existing T3 Connect task remained running.
- git check-ignore confirms private connection metadata and raw reports are excluded. No actual Google credential was obtained or used.
- The public Markdown link check found no missing relative targets, the spec contains 12 numbered acceptance criteria, every criterion maps to plan tasks, and every plan task appears in tracker.md.
- Audit tree JSON parses, and the original nine source-module blob IDs had matched the audited commit tree during source review.
- git diff --check succeeds. The final commit and origin/main equality are checked separately at delivery.

## Limits

The collector package, image, UI and MQTT bridge have not been implemented. Their tests and acceptance checkboxes are deliberately not marked passed. The runtime integration has received a static source review, not an authenticated network test or an audit of HA's full dependency graph.

Cloudflare routes/Access policies, router forwarding and HA account/MFA configuration are not verified. The environment assessment records these deployment preconditions and the accepted privileged-host trust boundary.

No Pi service, firewall, SSH/tunnel setting, container or deployment was changed or restarted. No Pi source checkout was necessary for this handoff.

## Evidence locations

- START_HERE.md: project entry point and implementation status.
- docs/PROJECT_CONTEXT.md: accepted requirements and decisions.
- docs/specs/current/2026-10-19-isolated-collector/spec.md: concrete criteria and defaults.
- docs/specs/current/2026-10-19-isolated-collector/plan.md: exact tasks and future validation commands.
- docs/specs/current/2026-10-19-isolated-collector/tracker.md: resumable pending task list.
- docs/audits/2026-10-19-upstream-2.0.3/REVIEW.md and pinned-tree.json: static review and pinned provenance.
- docs/ENVIRONMENT_ASSESSMENT.md: sanitized host observations and limitations.
- .local/inspection/: private raw metadata reports available only on the owner's checkout, not GitHub.
