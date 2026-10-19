# Collector dependencies

Reviewed on 19 October 2026 against PyPI release metadata and maintainer security advisories. Python is restricted to 3.13; development used CPython 3.13.16 and uv 0.13.1. The exact transitive distributions and SHA-256 hashes are in collector/uv.lock. CI uses frozen resolution; builds do not download packages at startup.

| Package | Pin | Selection |
|---|---|---|
| requests | 2.34.2 | Current release; includes 2.33.0 temporary-file and earlier netrc/TLS fixes. |
| cryptography | 50.0.2 | Current patch release; newer than 50.0.0 PKCS7 and 48.0.1 bundled OpenSSL fixes. Only AES-GCM is used. |
| paho-mqtt | 2.1.0 | Current stable release, callback API v2. |
| starlette | 1.9.0 | Current release; newer than 1.3.1 form limits and 1.3.0 authority fixes. |
| uvicorn | 0.54.0 | Current stable release; no published maintainer advisories returned at review. |
| python-multipart | 0.0.32 | Current release; includes 0.0.31 negative-length and 0.0.30 parameter parsing fixes. |
| pytest / httpx | 9.1.1 / 0.28.1 | Current stable test tools; no live credentials needed. |
| hatchling | 1.32.4 | Exact build backend pin. |

This is a bounded release/advisory review, not an audit of every dependency. Paho's maintainer advisory endpoint returned no published advisories. Recheck these sources before a release and run a full lockfile vulnerability scan in release verification.

Primary evidence: [PyPI requests](https://pypi.org/project/requests/), [cryptography](https://pypi.org/project/cryptography/), [Paho](https://github.com/eclipse-paho/paho.mqtt.python/releases/tag/v2.1.0), [Starlette 1.9.0](https://github.com/Kludex/starlette/releases/tag/1.9.0), [Uvicorn](https://pypi.org/project/uvicorn/), [multipart](https://pypi.org/project/python-multipart/).
Maintainer advisories: [Requests](https://github.com/psf/requests/security/advisories), [cryptography](https://github.com/pyca/cryptography/security/advisories), [Starlette](https://github.com/Kludex/starlette/security/advisories), [multipart](https://github.com/Kludex/python-multipart/security/advisories), [Uvicorn](https://github.com/Kludex/uvicorn/security/advisories).

Task 1.1 evidence: frozen installation succeeded on Windows, uv lock --check succeeded, CLI --help and --version succeeded, and 7 configuration checks passed. Linux execution remains a CI check, not an observed result.

Image evidence on 2026-10-19: registry manifest inspection resolved Python 3.13.16-slim-bookworm to sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641, uv 0.13.1 to sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 and Mosquitto's 2 index to sha256:38c0da4f2ef84284d47b3b3eeea1cb3bdeabe81ee10caf0cd5c5ff61ee3ea408 (2.1.2-alpine metadata). All contain ARM64 manifests. No container startup is inferred from metadata.

The complete exported frozen runtime requirements were scanned with pip-audit 2.10.1 on the review date: no known vulnerabilities found. The audit tool ran in an isolated transient development environment and is not a runtime dependency. A future Starlette test-client transition to httpx2 is noted by the pinned version's deprecation warning; current tests with httpx 0.28.1 pass.
