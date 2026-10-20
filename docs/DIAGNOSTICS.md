# Collector diagnostics

The authenticated collector page shows Diagnostics below session status. Use Refresh status to see the latest attempt. It retains the last source failure after recovery, with its timestamp, operation and observed HTTP status when known. This addition records future observations; it cannot reconstruct an earlier failure from before installation.

| Reason | What the collector observed |
|---|---|
| `google_invalid_session_marker` | A successful HTTP response contained the original client's invalid-session marker. This does not prove the cookie's expiry date passed. |
| `google_http_auth_rejected` | Google returned HTTP 401 or 403. |
| `google_redirect_rejected` | Google returned a redirect, which the fixed-origin transport refused to follow. Its destination is never recorded. |
| `google_timeout`, `google_connection_error`, `google_tls_error` | The corresponding transport failed. |
| `google_retries_exhausted`, `google_http_error`, `google_network_error` | Requests exhausted retry attempts, received another rejected HTTP status, or encountered an unclassified transport failure. |
| `google_data_invalid`, `google_observation_invalid` | The original parser or observation validation rejected Google's reply. The body is never recorded. |
| `google_response_too_large`, `google_response_encoding_invalid` | The bounded response or UTF-8 checks failed. |
| `google_session_required` | A source-authentication failure without a more specific reason, including no loaded session. |
| `credential_store_unavailable` | Saving the encrypted credential state failed. |
| `data_access_denied` | The local data endpoint rejected an absent/incorrect access key. This is separate from Google's session. |

Operations distinguish `native_poll`, `legacy_poll`, `session_import` and `data_auth`. Cookie additions/changes/removals are counts of **successfully saved** changes, not cookie names, values or fingerprints. A zero count on a failed request does not mean Google sent no cookies. The separate last-source-failure field prevents an anonymous data request from overwriting the useful Google failure diagnosis.

Up to 32 recent significant events are retained. Consecutive identical events are logged at most once per 15 minutes unless saved cookies change; current last-attempt/success/failure timestamps still update. Imports, source recovery and changed reasons are visible. Metadata is saved atomically as `diagnostics.json` in the existing private data directory and survives collector recreation. Its format contains no account/contact/location data or credentials. It is independent of the encrypted session format.

Only fixed allowlisted codes, generated timestamps, numeric HTTP statuses and cookie-change counts enter this history or the dedicated JSON log sink. Cookie names/values/hashes, headers, Google bodies, redirect targets, account identifiers, locations, exception strings and tracebacks are excluded. Original upstream and HTTP debug logging remain disabled; do not enable them to investigate this issue.

Operators can read just this validated metadata without loading Google cookies, store keys or management credentials:

```sh
docker compose --env-file .local/collector.env -p google-maps-collector -f deploy/compose.session.yaml exec -T collector python -m google_maps_collector --diagnostics
```

The command must run from the separate collector checkout with its existing private environment file. It reads only the diagnostics file, validates its schema and size, and prints selected metadata. Do not dump container environments, credential files or raw logs. The existing Compose file already rotates container logs; no Compose change is needed.

Unreadable/corrupt optional diagnostic history is discarded with a visible history-reset indicator. A diagnostics-write failure leaves tracking and encrypted persistence operational, retains in-memory evidence and emits only a fixed warning. A broken log stream cannot print surrounding exceptions or interrupt a poll.

These codes identify the observed failure category. Google may supply no explanation for rejecting an otherwise unexpired session; this feature does not add a browser login/refresh flow or change authentication policy.
