# Maintained patch against upstream 2.1.0

Baseline `ae85b249b354c25c2994cd1458231039e1dc977f`. The upstream binary sensor, sensor, helper, constant and Maps client files are protected by SHA-256 in [upstream-patch-boundary.json](upstream-patch-boundary.json). The guard also pins the reviewed tracker below. The external service packages the identical Maps client under its `_upstream` module.

Allowed native changes:

| File | Reason |
|---|---|
| collector_client.py (added) | Fixed loopback, scoped data-only transport and schema validation; returns original GMPerson objects with exact timestamp/account semantics |
| coordinator.py | Use the scoped local transport and expiry metadata for repairs. Keep 2.1.0 polling behavior and queue new sensors from the tracker platform. |
| config_flow.py | Replace cookie upload/storage with endpoint/data key setup; preserve original account/accuracy/update-period options code |
| __init__.py | Remove cookie-file deletion and migrate legacy entry metadata to external-source configuration without reading credentials |
| device_tracker.py | Strip only the sensor suffix from registry IDs and remove only sensors that HA attached. This fixes reloads for hyphenated IDs and missing-contact cleanup with disabled sensors. |
| translations/en.json | Describe external session setup/renewal; keep original options/entity translations |
| manifest.json | Fork version/docs/issues, remove file_upload dependency and describe local source polling |

The external upstream.py wrapper enforces exact Google origin, mandatory TLS, rejected redirects/environment proxies, bounded responses and fixed redacted errors. Those are credential/transport hardening, not alternative contact parsing or HA location policy. Invalid non-finite/range values are rejected at the API boundary; valid upstream observations retain all fields, including long names/addresses. The native API bypasses the temporary legacy MQTT filtered cache. cookie_expiration is non-secret metadata for existing expiry repairs.

Run python tools/check_upstream.py before each release. python tools/test_upstream_rebase.py applies the actual maintained HA diff to a temporary synthetic upstream entity update and verifies the changed original entity survives without rewriting tracking rules. Real upstream changes still require the manual audit procedure in UPSTREAM_UPDATES.md; update the baseline/digests and identical vendored client only after review.

Actual HA runtime tests run the original entities and options against a synthetic local source, without production config mounts or Google credentials. Keep those tests and the data contract aligned with every audited upstream revision. The existing MQTT adapter remains a transition path only; native operation uses compose.session.yaml and no broker.
