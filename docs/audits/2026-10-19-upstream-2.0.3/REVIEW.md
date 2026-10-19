# ha-google-maps 2.0.3: focused static security review

Reviewed on 19 October 2026. Repository: pnbruckner/ha-google-maps.
Release 2.0.3 resolves to commit b2132123d46c47e5761d5d91cc08ca6b712fe6c1.
GitHub's latest-release endpoint reported 2.0.3 at review time.

Conclusion: no code path was found in the reviewed integration that deliberately uploads Google session cookies to an unrelated server. This is a bounded static source review, not an unconditional security guarantee, formal certification, or a live network test.

## Scope and evidence

Read all nine Python modules in custom_components/google_maps, the parent namespace initializer, manifest.json, hacs.json and the English translation JSON. The Python modules total approximately 2,045 non-final-empty lines. Checked returned Git blob IDs against the recursive tree for the full commit; all nine module IDs matched. The reviewed source is retained in Git history at the pinned commit; its tree inventory is included alongside this report.

Traced cookie upload, validation, local persistence, the HTTP session, error handling, logging, entity attributes and shutdown/removal. Checked relevant Requests documentation and HACS update documentation/installation entry point.

The installed HA version, Python, requests, urllib3, TLS trust store, exporter extension, other custom integrations, actual filesystem permissions, backups and user automations were not supplied and were not audited. This review does not audit those dependencies in full or establish what is installed on the user's server. No Google credential was accessed and no authenticated live request was made. At the time of this static source review the terminal runner was unavailable, so no local Python execution, packet capture or dynamic integration tests were performed. Later SSH/host checks are recorded separately in ENVIRONMENT_ASSESSMENT.md. The source was retrieved using GitHub tools and reviewed without executing it.

## Cookie and network flow

1. config_flow.py uses HA's process_uploaded_file context manager to access a user-uploaded cookie file. It validates via GMLocSharing, then saves under a generated UUID filename.
2. helpers.py constructs the path as <HA config>/.storage/google_maps/<UUID>.
3. gm_loc_sharing.py loads cookies with Python's MozillaCookieJar. It does not use pickle, evaluate cookie data as code or send the whole file as an HTTP upload.
4. GMLocSharing constructs a dedicated requests.Session and assigns its cookie jar to that session. It does not install these cookies into HA's shared HTTP session.
5. Its single explicit HTTP call is a GET to https://www.google.com/maps/rpc/locationsharing/read with fixed query parameters, timeout=60 and verify=True. Cookies travel as HTTP authentication cookies selected by the HTTP library, not as telemetry payloads.
6. coordinator.py saves changed response cookies locally at intervals of at least 15 minutes or on shutdown. This is cookie maintenance, not a software updater.
7. __init__.py schedules deletion of the previous cookie file when replaced, and of the configured cookie file when the entry is removed. This does not revoke the Google session or remove historical copies from backups.

Other URL strings are documentation/export-extension links; entity_picture returns a URL supplied in Google's response. No path was found that passes the private cookie jar to those URLs.

## Findings and residual risks

No third-party credential upload or self-update mechanism found. The runtime code contains no explicit subprocess launch, dynamic remote code loading, encoded executable payload, or separate analytics destination. The manifest declares requirements: [] and the HA integration dependency file_upload. This version embeds its location-sharing implementation; it does not fetch locationsharinglib as an integration-specific dependency. It still relies on libraries supplied by HA.

Readable credential storage is inherent to this implementation. MozillaCookieJar persistence writes reusable cookie values in a Netscape-format file, with no integration-level encryption. Code with access to the HA process/configuration can potentially read them. Pinning the integration does not isolate cookies from other custom components, a compromised HA host, or copies in backups. No claim about actual filesystem ACLs is made.

Response logging exposes private data in some failure/debug cases. gm_loc_sharing.py includes raw response text or parsed response data in InvalidData exceptions and debug logging. coordinator.py forwards InvalidData into UpdateFailed, and config_flow.py debug-logs validation errors. These paths can expose names, locations, addresses or other returned account data to logs/support bundles. The cookie logging helpers themselves log names, expiry times and changed-cookie names, not cookie values. No explicit cookie-value logging was found. A hardening change should redact raw response bodies while preserving a useful error code.

Destination restriction is not enforced independently. The first URL is fixed and HTTPS certificate verification is enabled, but requests follows redirects by default; there is no application-level host allowlist or redirect rejection. Cookie domain/path rules still apply: this is not evidence that Google cookies are automatically sent to arbitrary redirect hosts. Environment-derived proxy/trust behavior is also inherited from Requests. A stricter collector could reject redirects and enforce the exact expected origin, subject to compatibility testing.

Cookie extraction is a separate trust boundary. cookies.py instructs users to install a browser extension to export cookies. That extension was not audited here. The integration also offers a path straight to file upload, so it is not technically dependent on installing that extension.

## Updates and maintaining the reviewed state

No software downloader or self-updater was found in these integration modules. HACS checks for newer versions and provides installation through its Update button or the update.install action. A user automation or another updater can invoke that action; the user's configuration was not inspected. Updating HACS itself does not imply updating this downloaded integration.

New releases are not mandatory on a fixed schedule. Reasons to review and install one include changes to Google's undocumented API/session handling, HA compatibility changes, security fixes, correctness fixes and desired features. Recent 2.0.2 and 2.0.3 release notes specifically address HA 2026.6 compatibility/deprecation. Cookie expiry usually calls for fresh cookies, not new integration code.

For reproducibility, retain the full commit and per-file inventory, rather than relying on the mutable release tag or main branch. Compare installed file blobs/contents with the reviewed source. Keep installation manual and exclude this update entity from broad auto-update automations. Review the diff of every future version before installation, including manifest changes and new dependencies. Updating HA can change shared libraries even if these integration files stay unchanged. Do not freeze HA security updates merely to preserve this review.

Practical options using the user's existing account are a manually maintained copy of this reviewed integration, or a separate collector using the same personal account with only sanitized location output delivered to HA. The latter can keep Google credentials outside HA, but only if its process/filesystem boundary actually prevents HA from reading them.

## Primary sources

- Pinned tree: https://github.com/pnbruckner/ha-google-maps/tree/b2132123d46c47e5761d5d91cc08ca6b712fe6c1
- HTTP/cookie implementation: https://github.com/pnbruckner/ha-google-maps/blob/b2132123d46c47e5761d5d91cc08ca6b712fe6c1/custom_components/google_maps/gm_loc_sharing.py
- Upload/storage flow: https://github.com/pnbruckner/ha-google-maps/blob/b2132123d46c47e5761d5d91cc08ca6b712fe6c1/custom_components/google_maps/config_flow.py
- Coordinator: https://github.com/pnbruckner/ha-google-maps/blob/b2132123d46c47e5761d5d91cc08ca6b712fe6c1/custom_components/google_maps/coordinator.py
- Manifest: https://github.com/pnbruckner/ha-google-maps/blob/b2132123d46c47e5761d5d91cc08ca6b712fe6c1/custom_components/google_maps/manifest.json
- HACS installation entry point: https://github.com/hacs/integration/blob/main/custom_components/hacs/update.py
- HACS update documentation: https://hacs.netlify.app/docs/use/update/
- HACS update actions: https://hacs.dev/docs/use/entities/update/
- Requests redirects: https://requests.readthedocs.io/en/latest/user/quickstart/#redirection-and-history
