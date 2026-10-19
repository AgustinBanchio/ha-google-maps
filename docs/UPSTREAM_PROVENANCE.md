# Collector client provenance

Source: custom_components/google_maps/gm_loc_sharing.py at audited upstream b2132123d46c47e5761d5d91cc08ca6b712fe6c1 (Unlicense, retained in repository LICENSE and Git history).

The collector copy derives the fixed URL, pb query and shared-person array indices from that file. Shared-person IDs, coordinates, accuracy, millisecond timestamps and optional battery retain their upstream interpretation. Account-holder fallback by email is omitted. No display names, addresses or picture URLs enter the collector model.

Attributable hardening: fixed-origin guard; redirects disabled; TLS mandatory; proxy/netrc environment disabled; response size bound; finite/range/type validation; exact cookie domains with secure cookies; explicit Netscape parsing in memory (without warning-emitting standard-library file parsing); transport injection; fixed exception codes without raw payloads or chained transport messages. Requests performs no internal retries; the service owns bounded retry timing. The response body/logging and cookie-file persistence functions were not copied. Store and lifecycle are independent modules.

This extraction does not modify custom_components/. Future upstream changes must follow UPSTREAM_UPDATES.md, with a fresh comparison against the pinned source. Synthetic fixtures are fabricated, not captured Google responses; live compatibility remains an acceptance check.
