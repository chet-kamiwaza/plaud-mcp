# Phase 10 Validation Record

**Validated:** 2026-04-14
**Status:** passed

## Commands run

| Command | Result | Notes |
|--------|--------|-------|
| `python -m pip install '.[dev]'` | passed | Installed declared dev tooling including `build` and the Python 3.10 `tomli` fallback. |
| `pytest -q tests/test_release_assets.py` | passed | `4 passed in 0.01s` |
| `pytest -q` | passed | `78 passed in 0.83s` |
| `python -m build` | passed | Built `sdist` and wheel successfully with clean SPDX-style license metadata. |
| `bash scripts/container-runtime.sh docker config` | passed | Rendered loopback `127.0.0.1:8080` binding and `/app/data` volume mapping. |
| `bash scripts/container-runtime.sh podman config` | passed | Rendered the same compose contract through the validated Podman compose-provider path. |
| `bash scripts/verify-local-mac.sh docker` | passed | Built, started, cleaned up, and ended with `78 passed in 0.62s`. |
| `bash scripts/verify-local-mac.sh podman` | passed | Built, started, cleaned up, and ended with `78 passed in 0.61s`. |

## Observed caveats

- Docker and Podman emit blank-value warnings for `PLAUD_EMAIL` and `PLAUD_PASSWORD` when auto-refresh is not configured. This is expected from the current compose contract.
- Podman on this Mac uses an external compose provider. The repo documents that behavior explicitly.
- Local verification should remain sequential on one Mac because both runtime checks use port `8080`.

## Cleanup checks

- `lsof -nP -iTCP:8080 -sTCP:LISTEN` returned no active listener after verification.
- `podman ps -a` was empty after the Podman verification run.
- Unrelated Docker containers on the host remained untouched.
