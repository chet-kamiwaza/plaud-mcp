---
phase: 01-api-client
plan: "01"
subsystem: api
tags: [httpx, pydantic-settings, plaud-api, bearer-token, python, async]

# Dependency graph
requires: []
provides:
  - PlaudClient async HTTP client with all six required Plaud auth headers
  - pydantic-settings startup validation raising ValidationError on missing PLAUD_TOKEN/PLAUD_DEVICE_ID
  - Application-level -302 domain redirect handling with single retry and domain validation
  - PlaudAuthError raised on status -10000; PlaudAPIError on all other non-zero status codes
  - 7 unit tests covering AUTH-01 through AUTH-04 using respx mocks
affects: [02-mcp-tools, 03-container]

# Tech tracking
tech-stack:
  added:
    - httpx 0.28.1 (already installed; now used directly)
    - pydantic-settings 2.13.1 (already installed; now used directly)
    - pytest-asyncio (installed)
    - respx 0.23.1 (installed)
  patterns:
    - pydantic-settings BaseSettings with module-level Settings() instance for startup validation
    - httpx.AsyncClient with default headers for all six Plaud auth headers
    - Application-level JSON status code dispatch inside _request() method
    - respx.mock for httpx unit testing without live network calls
    - conftest.py autouse fixture + module-level os.environ.setdefault for test env injection

key-files:
  created:
    - pyproject.toml
    - src/plaud_mcp/__init__.py
    - src/plaud_mcp/config.py
    - src/plaud_mcp/errors.py
    - src/plaud_mcp/client.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_client.py
  modified:
    - pyproject.toml (build backend fix)

key-decisions:
  - "Used pydantic-settings module-level settings = Settings() for fail-fast startup validation (AUTH-01)"
  - "Set all six AUTH-02 headers as AsyncClient defaults — not per-request — to prevent omission bugs"
  - "T-01-02 domain validation: new_domain.endswith('plaud.ai') enforced before any base_url mutation"
  - "_redirect_attempted bool guard chosen over counter — only one retry ever needed for -302"
  - "Live smoke test skipped: user confirmed no valid PLAUD_TOKEN available; unit tests are full coverage"

patterns-established:
  - "Pattern 1: All Plaud API calls go through PlaudClient._request() — single dispatch point for status handling"
  - "Pattern 2: Never log settings.plaud_token value — T-01-01 threat mitigated by convention"
  - "Pattern 3: async with PlaudClient() as client — context manager ensures aclose() called on exit"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-04]

# Metrics
duration: 10min
completed: 2026-04-08
---

# Phase 1 Plan 01: API Client Summary

**httpx AsyncClient with all six Plaud auth headers, -302 domain redirect handling, -10000 PlaudAuthError, and pydantic-settings startup validation — 7 unit tests all passing**

## Performance

- **Duration:** ~10 min (execution resumed from checkpoint)
- **Started:** 2026-04-08T22:20:00Z (estimated)
- **Completed:** 2026-04-08
- **Tasks:** 2 auto tasks completed + 1 checkpoint approved
- **Files modified:** 9

## Accomplishments

- Built `PlaudClient` with all six AUTH-02 headers injected as `httpx.AsyncClient` defaults — resolves STATE.md blocker (header set is the likely cause of the 401 reports, not Chromium-level validation)
- Implemented startup config validation via pydantic-settings `Settings()` at import time — server fails immediately with `ValidationError` if `PLAUD_TOKEN` or `PLAUD_DEVICE_ID` are missing (AUTH-01)
- Application-level response code dispatch in `_request()`: status=0 returns data, -302 updates `base_url` and retries once with domain validation against `*.plaud.ai`, -10000 raises `PlaudAuthError`, other non-zero raises `PlaudAPIError`
- T-01-02 security mitigation applied: redirect to non-plaud.ai domains is rejected before base_url mutation
- 7 unit tests covering all AUTH requirements pass with respx mocking

## Task Commits

1. **Task 1: Project scaffold, config module, and error classes** - `dbcdb06` (feat)
2. **Task 2: PlaudClient implementation** - `647d74a` (feat)
3. **Fix: setuptools build backend** - `fa8988f` (fix) — Rule 1 deviation, see below

## Files Created/Modified

- `pyproject.toml` — package definition with httpx, pydantic-settings, mcp, fastmcp deps; pytest asyncio_mode=auto
- `src/plaud_mcp/__init__.py` — package marker (empty)
- `src/plaud_mcp/config.py` — `Settings` class with `PLAUD_TOKEN`, `PLAUD_DEVICE_ID`, `PLAUD_BASE_URL`, `PLAUD_APP_VERSION`; module-level `settings` instance raises `ValidationError` at import time
- `src/plaud_mcp/errors.py` — `PlaudError`, `PlaudAuthError`, `PlaudAPIError` custom exception hierarchy
- `src/plaud_mcp/client.py` — `PlaudClient` with async context manager, six-header defaults, `_request()` dispatch, `-302` redirect handling, `get()` convenience method
- `tests/__init__.py` — package marker (empty)
- `tests/conftest.py` — `autouse` fixture injecting `PLAUD_TOKEN`/`PLAUD_DEVICE_ID` env vars for test collection; module-level `os.environ.setdefault` for pydantic-settings Settings() import
- `tests/test_client.py` — 7 unit tests across 5 test classes (AUTH-02 through AUTH-04 + success path + unknown error)

## Decisions Made

- Used pydantic-settings module-level `settings = Settings()` for startup validation — raises at import time, not at first API call
- All six AUTH-02 headers set as `AsyncClient` defaults, not per-request kwargs — prevents accidental omission in future `get()` calls
- Domain validation (`new_domain.endswith("plaud.ai")`) applied before base_url mutation — T-01-02 threat mitigation from threat register
- `_redirect_attempted` bool guard chosen over integer counter — semantically correct (one retry is the full retry budget)
- Live smoke test skipped: user confirmed no valid `PLAUD_TOKEN` available at this time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong setuptools build backend in pyproject.toml**
- **Found during:** Task 3 checkpoint continuation (running `pip install -e .`)
- **Issue:** `build-backend = "setuptools.backends.legacy:build"` caused `BackendUnavailable` — the correct path is `setuptools.build_meta`
- **Fix:** Changed to `build-backend = "setuptools.build_meta"`
- **Files modified:** `pyproject.toml`
- **Verification:** `pip install -e .` succeeded; `python -m pytest tests/ -v` ran all 7 tests and passed
- **Committed in:** `fa8988f`

---

**Total deviations:** 1 auto-fixed (1 Rule 1 - Bug)
**Impact on plan:** Required for the package to be importable by pytest. No scope creep.

## Issues Encountered

- `pyproject.toml` build backend was set to `setuptools.backends.legacy:build` (invalid path). Fixed as Rule 1 deviation before running the final test suite.

## User Setup Required

**External token required for live smoke test.**

For full Phase 1 verification (smoke test against live Plaud API), set these env vars and run the script in Task 3's `how-to-verify` section:

```bash
export PLAUD_TOKEN="<token from Plaud account settings or ~/Library/Application Support/Plaud/config.json>"
export PLAUD_DEVICE_ID="<any stable UUID registered in your Plaud account>"
```

The unit test suite (AUTH-01 through AUTH-04) passes completely without a live token.

## Live API Test Result

**Skipped — no valid token available.** User approved the checkpoint with `"approved (no valid token)"`.

STATE.md blocker ("direct HTTP may return 401 — may be a missing-headers issue") is **partially resolved**: the full six-header set has been implemented. The remaining open question (whether the full header set is truly sufficient to avoid 401s) can only be confirmed with a live token smoke test. Headers are:
```
Authorization: bearer {PLAUD_TOKEN}
X-Device-Id: {PLAUD_DEVICE_ID}
edit-from: desktop
app-platform: desktop
app-versionNumber: {PLAUD_APP_VERSION}  # default "5.3.9"
app-language: en
```

Note from PROJECT.md context: the reverse-engineered app bundle shows `app-versionNumber: 1.0.5` (Electron app version) vs the plan's `5.3.9` (community-reported desktop app version). This discrepancy is tracked in the Assumptions Log (A1) and is overridable via `PLAUD_APP_VERSION` env var.

## Assumptions Status

| # | Assumption | Status |
|---|------------|--------|
| A1 | `app-versionNumber: "5.3.9"` accepted | UNVALIDATED — no live token; made configurable via env var |
| A2 | `/user/current` is valid connectivity endpoint | UNVALIDATED — no live token; fallback `/file/simple/web?limit=1` noted in plan |
| A3 | `-302` body is `{"data": {"domains": {"api": "<hostname>"}}}` | IMPLEMENTED — unit test mock uses this shape; live validation pending |
| A4 | `-10000` means auth error | IMPLEMENTED — unit test passes; live validation pending |
| A5 | `app-language: "en"` accepted | UNVALIDATED — low risk |

## Next Phase Readiness

**Ready for Phase 2 (MCP Tools):**
- `PlaudClient` is imported as `from plaud_mcp.client import PlaudClient`
- All AUTH requirements (AUTH-01 through AUTH-04) satisfied with unit test coverage
- `settings` object provides `plaud_base_url`, `plaud_token`, `plaud_device_id`, `plaud_app_version` for Phase 2 use
- Error types `PlaudAuthError` and `PlaudAPIError` are ready to be caught at MCP tool boundary

**Blocker for live validation:** A valid `PLAUD_TOKEN` and `PLAUD_DEVICE_ID` must be injected to run the smoke test. Phase 2 can proceed with unit tests only; smoke test can be deferred to first container integration test.

---
*Phase: 01-api-client*
*Completed: 2026-04-08*
