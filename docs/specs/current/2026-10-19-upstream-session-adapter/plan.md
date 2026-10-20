# Implementation plan

All tasks sequential; owner explicitly authorized execution of this course correction.

1. Package the unchanged pinned gm_loc_sharing.py with a source guard. Add an origin-restricted bounded session wrapper and upstream observation serialization. Files: collector/src/google_maps_collector/upstream.py, vendor module, tools/check_upstream.py, collector/tests/test_upstream.py. Verify original records and security transport tests.
2. Add the scoped /v1/locations API and dedicated token, serialize all Google access and reuse encrypted cookies without serving the filtered MQTT cache. Keep legacy MQTT during migration. Files: service.py, web.py, config.py, bootstrap/tooling, deploy files. Verify API auth, rejected management access, no raw/secret output, concurrent import/poll and old encrypted-state upgrade.
3. Adapt original native integration at the source/auth seam. Keep protected entity/helpers/client modules unchanged. Files: collector_client.py, coordinator.py, config_flow.py, __init__.py, manifest/translations. Verify original option/entity contracts and no cookie IO in reachable HA path.
4. Run actual HA 2026.10.1 runtime tests against reference observations and native transport, including entity states/pictures/accuracy/time/missing/restoration/options/errors. Add CI, exact upstream patch inventory and synthetic update guard exercise. Run collector suite, source guard and native HA tests.
5. Build/test ARM64 service, prepare scoped credential delivery, native install and MQTT migration/rollback; execute only authorized deployment actions, verify aggregate live API and original-service baseline, finish setup/migration docs and push main. Record remaining live owner actions precisely.


2026-10-20 diagnostics maintenance: (1) allowlisted error metadata at the external transport seam; (2) bounded persistent JSON diagnostics and dedicated sanitized events for imports/polls/access-key rejection; (3) private status UI for last failure and rotation counts; (4) synthetic Requests cookie extraction, rotation persistence, error/redaction/retention/restart/corruption tests plus current suites; (5) push owner main and prepare targeted collector rollout/rollback with no existing-stack change.
