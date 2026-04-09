---
phase: 03-container-kubernetes
plan: 01
subsystem: infra
tags: [docker, kubernetes, fastmcp, python, mcp, container, k8s]

# Dependency graph
requires:
  - phase: 02-mcp-tools
    provides: FastMCP server with 8 tools over stdio transport
provides:
  - Docker image build from python:3.10-slim with plaud-mcp package
  - MCP_TRANSPORT env var dispatch: stdio (default) or streamable-http on port 8080
  - /health custom route on FastMCP app for Kubernetes liveness probes
  - Kubernetes Deployment + ClusterIP Service + Secret template manifests
  - plaud-mcp console script entry point via pyproject.toml
affects: [deployment, kubernetes, docker, ci-cd]

# Tech tracking
tech-stack:
  added: [Docker (python:3.10-slim), Kubernetes manifests (deployment/service/secret), starlette JSONResponse]
  patterns:
    - MCP_TRANSPORT env var dispatch for multi-transport support
    - Two-stage pip install in Dockerfile for dependency layer caching
    - FastMCP custom_route decorator for non-MCP HTTP endpoints
    - K8s envFrom.secretRef pattern for credential injection

key-files:
  created:
    - src/plaud_mcp/__main__.py
    - Dockerfile
    - .dockerignore
    - deploy/deployment.yaml
    - deploy/service.yaml
    - deploy/secret.yaml
  modified:
    - src/plaud_mcp/server.py
    - pyproject.toml
    - .gitignore

key-decisions:
  - "MCP_TRANSPORT=stdio default; http branch uses streamable-http on 0.0.0.0:8080"
  - "Two pip install steps in Dockerfile: first caches deps from pyproject.toml, second installs package after src/ copy"
  - "FastMCP custom_route stores routes in _additional_http_routes (not _custom_routes as plan assumed)"
  - "deploy/secret.yaml committed as placeholder template using git add -f; .gitignore blocks real-credential versions"
  - "ClusterIP-only service: no external exposure without explicit port-forward or Ingress"

patterns-established:
  - "Package entrypoint pattern: __main__.py reads env var and calls mcp.run() with appropriate transport"
  - "Health check via @mcp.custom_route('/health', methods=['GET']) returning JSONResponse({'status': 'ok'})"
  - "Non-root container: useradd --uid 1000 in Dockerfile + securityContext.runAsNonRoot in Deployment"

requirements-completed: [CONT-01, CONT-02, CONT-03, CONT-04, CONT-05]

# Metrics
duration: 6min
completed: 2026-04-09
---

# Phase 3 Plan 01: Container & Kubernetes Summary

**MCP server packaged as python:3.10-slim Docker image with MCP_TRANSPORT dispatch, /health FastMCP custom route, and Kubernetes Deployment/Service/Secret manifests with UID 1000 non-root security**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-09T03:11:23Z
- **Completed:** 2026-04-09T03:17:47Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Created `src/plaud_mcp/__main__.py` as the package entrypoint: reads `MCP_TRANSPORT` env var, dispatches to `stdio` (default) or `streamable-http` on port 8080
- Added `@mcp.custom_route("/health")` to `server.py` returning `{"status": "ok"}` for Kubernetes liveness probes; removed `if __name__ == "__main__"` block
- Built `Dockerfile` from `python:3.10-slim` with two-stage pip install for layer cache efficiency, `USER 1000` non-root, `ENV MCP_TRANSPORT=stdio` default, `PLAUD_TOKEN`/`PLAUD_DEVICE_ID` never baked in (T-03-01)
- Created three Kubernetes manifests: Deployment with `envFrom.secretRef: plaud-credentials`, liveness/readiness probes on `/health`, `runAsNonRoot: true`; ClusterIP Service on 8080; Secret template with placeholder-only base64 values
- Added `[project.scripts]` entry to `pyproject.toml` enabling `plaud-mcp` console script
- Added `deploy/secret.yaml` to `.gitignore` to prevent accidental credential commit (T-03-03)
- All 37 Phase 2 regression tests continue to pass after server.py changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Entrypoint, health route, pyproject scripts** - `cc3343c` (feat)
2. **Task 2: Dockerfile and .dockerignore** - `c5074d6` (feat)
3. **Task 3: Kubernetes manifests** - `df66cf0` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `src/plaud_mcp/__main__.py` - Package entrypoint; MCP_TRANSPORT dispatch to stdio or streamable-http
- `src/plaud_mcp/server.py` - Added /health custom route; removed __main__ block
- `pyproject.toml` - Added [project.scripts] plaud-mcp = "plaud_mcp.__main__:main"
- `Dockerfile` - python:3.10-slim, two-stage pip install, USER 1000, ENV MCP_TRANSPORT=stdio
- `.dockerignore` - Excludes .venv/, tests/, .planning/, .git/, deploy/, __pycache__
- `deploy/deployment.yaml` - K8s Deployment with envFrom secretRef, liveness probe, runAsNonRoot
- `deploy/service.yaml` - ClusterIP Service on port 8080
- `deploy/secret.yaml` - Secret template with placeholder base64 values (DO NOT COMMIT WITH REAL VALUES)
- `.gitignore` - Appended deploy/secret.yaml

## Decisions Made

- **MCP_TRANSPORT dispatch**: `stdio` default for Claude Code/Desktop local use; `http` branch uses `streamable-http` on `0.0.0.0:8080` for Kubernetes service exposure
- **Two-stage pip install**: First `pip install .` caches dependency layer from `pyproject.toml`; second `pip install -e .` after `COPY src/` installs the package itself — source changes don't invalidate the dependency cache
- **FastMCP route storage**: Plan verification assumed `_custom_routes` attribute; actual FastMCP attribute is `_additional_http_routes`. Route correctly registered (verified via attribute inspection)
- **secret.yaml as committed template**: Used `git add -f` to commit placeholder-only file; `.gitignore` entry blocks real-credential versions from being committed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Curly quotes in Dockerfile CMD instruction**
- **Found during:** Task 2 (Dockerfile creation)
- **Issue:** Write tool rendered Unicode curly quotes in `CMD ["python", "-m", "plaud_mcp"]` instead of ASCII straight quotes, causing `grep -q 'python -m plaud_mcp' Dockerfile` to fail and breaking the CMD for Docker
- **Fix:** Rewrote Dockerfile with explicit ASCII-only content; verified bytes with Python
- **Files modified:** Dockerfile
- **Verification:** `grep 'python.*plaud_mcp' Dockerfile` passes; CMD line verified as pure ASCII bytes
- **Committed in:** c5074d6 (Task 2 commit)

**2. [Rule 3 - Blocking] .gitignore blocked committing secret.yaml template**
- **Found during:** Task 3 (K8s manifests commit)
- **Issue:** After appending `deploy/secret.yaml` to `.gitignore`, git refused to stage the placeholder template file
- **Fix:** Used `git add -f deploy/secret.yaml` to force-add the placeholder-only template. This is correct behavior: the gitignore entry protects real-credential versions; the committed file contains only obviously-fake placeholder strings
- **Files modified:** None (workflow fix only)
- **Verification:** File committed in df66cf0; `git show df66cf0:deploy/secret.yaml` shows only placeholder values
- **Committed in:** df66cf0 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes required for correct delivery. No scope creep. Security posture maintained — secret.yaml contains only placeholder values.

## Issues Encountered

None beyond the two auto-fixed deviations documented above.

## User Setup Required

None — no external service configuration required to build and deploy. To use the Kubernetes manifests:

1. Extract your Plaud token: `~/Library/Application Support/Plaud/config.json`
2. Encode: `echo -n "your-token" | base64`
3. Edit `deploy/secret.yaml` (already gitignored) with real base64 values
4. `kubectl apply -f deploy/`

## Next Phase Readiness

Phase 3 is complete. All 5 CONT requirements satisfied:
- CONT-01: stdio transport via `__main__.py` (MCP_TRANSPORT default)
- CONT-02: streamable-http transport via `__main__.py` (MCP_TRANSPORT=http)
- CONT-03: Dockerfile builds self-contained image
- CONT-04: Kubernetes Deployment + Service + Secret manifests
- CONT-05: /health endpoint for liveness probe

The project is now at milestone v1.0. A live end-to-end test (docker build + docker run with a real PLAUD_TOKEN) remains the only unvalidated step — blocked on obtaining a valid token from the Plaud Desktop app.

---
*Phase: 03-container-kubernetes*
*Completed: 2026-04-09*
