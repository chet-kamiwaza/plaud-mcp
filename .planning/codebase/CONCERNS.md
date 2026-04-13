# Codebase Concerns

**Analysis Date:** 2026-04-13

## Tech Debt

**Dead code: unreachable return statement in `search_transcripts`:**
- Issue: `src/plaud_mcp/server.py` line 607 contains a second `return` statement after the tool function's primary return on line 605. This line is unreachable dead code.
- Files: `src/plaud_mcp/server.py:607`
- Impact: No runtime impact, but signals leftover refactoring debris. Linters and coverage tools may flag it.
- Fix approach: Delete line 607.

**Dockerfile base image comment disagrees with FROM instruction:**
- Issue: Comment on line 3 says "python:3.10-slim base" but the actual `FROM` on line 10 pulls `python:3.14-slim`. The comment is stale.
- Files: `Dockerfile:3,10`
- Impact: Misleading documentation. A developer relying on the comment might assume Python 3.10 is used.
- Fix approach: Update line 3 comment to match the actual FROM image.

**Discovery script is a one-time artifact, not maintained:**
- Issue: `scripts/discover_phase1_contracts.py` (810 lines) is a Phase 1 reverse-engineering script that runs against the Plaud web app and desktop bundle. It is not referenced by any workflow, test suite, or deployment pipeline, and its hardcoded file glob patterns (`index-Bbfz*.js`) are fragile against upstream app updates.
- Files: `scripts/discover_phase1_contracts.py`
- Impact: Bit rot. If run in the future it may silently fail or produce incorrect artifacts.
- Fix approach: Either archive the script into a `scripts/archive/` directory with a note, or delete it if the Phase 1 artifacts are already committed.

**Module-level Settings instantiation blocks import-time flexibility:**
- Issue: `src/plaud_mcp/config.py:47` executes `settings = Settings()` at module import time. Any import of `plaud_mcp.config` (directly or transitively) requires `PLAUD_TOKEN`/`PLAUD_TOKEN_FILE` and `PLAUD_DEVICE_ID` to be set, or a `ValidationError` is raised. This makes testing fragile (the test conftest must set env vars before any import) and prevents conditional loading patterns.
- Files: `src/plaud_mcp/config.py:47`, `tests/conftest.py:11-13`
- Impact: The conftest workaround (module-level `os.environ.setdefault`) is brittle; if a new test file is collected before conftest runs, collection fails. Also prevents CLI subcommands that don't need credentials.
- Fix approach: Use a lazy singleton pattern (`_settings: Settings | None = None` with a `get_settings()` accessor function) so Settings is only instantiated on first use.

## Known Bugs

**No known runtime bugs detected.**

All 17 threats from the threat register are marked closed. No TODO/FIXME/XXX/HACK comments exist in `src/` or `scripts/`.

## Security Considerations

**Settings `__repr__` leaks token if ever printed/logged:**
- Risk: The `Settings` pydantic model has no `__repr__` override and no `hide_input_in_errors: True` in `model_config`. If any future code path logs or prints the settings object (e.g., debug logging, exception traceback with local variables), `plaud_token` will appear in cleartext. This is documented as informational note 1 in `SECURITY.md`.
- Files: `src/plaud_mcp/config.py:9-17`
- Current mitigation: No logging framework is used in the codebase, so there is currently no code path that triggers this.
- Recommendations: Add `hide_input_in_errors=True` to `model_config` and implement a `__repr__` that redacts `plaud_token`. Do this before introducing any logging infrastructure.

**No explicit S3 URL domain allowlist:**
- Risk: `_fetch_s3_content` in `src/plaud_mcp/server.py:146-166` follows any URL passed as `data_link` with `follow_redirects=True`. While `data_link` is only sourced from Plaud API responses (not MCP caller input), a compromised or misbehaving Plaud API could supply a URL pointing to an internal network resource (SSRF). This is documented as informational note 2 in `SECURITY.md`.
- Files: `src/plaud_mcp/server.py:160`
- Current mitigation: Architectural — `data_link` values are never exposed as MCP tool parameters.
- Recommendations: Add an explicit URL prefix assertion (e.g., `*.amazonaws.com` or `*.s3.*.amazonaws.com`) if moving to ASVS Level 2 or multi-tenant deployment.

**`get-token.py` prints token to stdout by default:**
- Risk: When invoked without `--output`, the script prints `PLAUD_TOKEN=<cleartext>` to stdout. This could be captured in shell history, terminal scrollback, or CI logs.
- Files: `scripts/get-token.py:128-133`
- Current mitigation: The `--output` flag writes to a file instead (and the test verifies the token is not echoed when `--output` is used).
- Recommendations: Default to `--output` mode or add a warning banner when printing to a terminal.

**Redirect domain validation uses suffix match only:**
- Risk: `client.py:94` checks `new_domain.endswith("plaud.ai")` which would also match `evil-plaud.ai` or `notplaud.ai`. A more precise check would verify the domain is exactly `plaud.ai` or a subdomain (`*.plaud.ai`).
- Files: `src/plaud_mcp/client.py:94`
- Current mitigation: The Plaud API is the only source of redirect domains in practice.
- Recommendations: Change check to `new_domain == "plaud.ai" or new_domain.endswith(".plaud.ai")`.

**Docker Compose exposes port 8080 on all host interfaces:**
- Risk: `docker-compose.yml` binds `"8080:8080"` which maps to `0.0.0.0:8080` on the host, making the MCP server accessible from the network. The K8s deployment correctly uses ClusterIP (T-03-04), but the Docker Compose alternative does not restrict binding.
- Files: `docker-compose.yml:7`
- Current mitigation: None. Single-user tool assumption.
- Recommendations: Bind to loopback only: `"127.0.0.1:8080:8080"`.

## Performance Bottlenecks

**`search_transcripts` downloads transcripts sequentially:**
- Problem: The `search_transcripts` tool iterates up to 100 files and downloads each transcript one at a time in a serial loop (`for f in files: ... await client.get(...)`, then `await asyncio.to_thread(_fetch_s3_content, ...)`).
- Files: `src/plaud_mcp/server.py:563-596`
- Cause: Sequential `await` inside a `for` loop. Each iteration requires an API call to `/file/detail/{id}` plus an S3 download, with 30-second timeouts each.
- Improvement path: Use `asyncio.gather` with a semaphore to fetch transcripts concurrently (e.g., 5-10 concurrent downloads). This could reduce search latency from O(n * 2 requests) to O(n/concurrency * 2 requests).

**`get_folder_files` fetches all files to filter client-side:**
- Problem: To find files in a folder, the server paginates through up to 2000 files (20 pages x 100 per page) and filters by `filetag_id_list` membership in Python. For accounts with many recordings, this is wasteful.
- Files: `src/plaud_mcp/server.py:315-336`, `src/plaud_mcp/server.py:488-537`
- Cause: The Plaud API provides no server-side folder filter endpoint (confirmed by reverse engineering in `scripts/discover_phase1_contracts.py`).
- Improvement path: Cache the file list for a short TTL (e.g., 60 seconds) to avoid re-fetching the same data when multiple folder queries are made in quick succession.

**Every tool call creates a new `PlaudClient` (new TCP connection):**
- Problem: Each MCP tool instantiates `PlaudClient()` with a fresh `httpx.AsyncClient`, requiring a new TCP+TLS handshake for every tool invocation.
- Files: `src/plaud_mcp/server.py` (all tool functions use `async with PlaudClient() as client:`)
- Cause: Deliberate simplicity — no shared client state.
- Improvement path: Use a module-level or FastMCP-lifespan-scoped client with connection pooling. httpx supports connection keep-alive natively.

## Fragile Areas

**Hardcoded Plaud API response key names:**
- Files: `src/plaud_mcp/server.py` (throughout), `src/plaud_mcp/client.py:175`
- Why fragile: The server parses Plaud API responses using hardcoded keys like `data_file_list`, `data_user`, `data_filetag_list`, `content_list`, `data_link`, `task_status`, `data_type`. These are reverse-engineered from the undocumented Plaud API. If Plaud changes their API response shape, all parsing silently breaks (returns empty dicts/lists instead of raising errors).
- Safe modification: Always add fallback handling when accessing new response keys. The current code uses `.get()` throughout, which prevents crashes but masks API changes.
- Test coverage: Tests mock the Plaud API entirely, so they cannot detect upstream API changes. No integration test hits the real API.

**`_select_highlight_content_item` precedence logic:**
- Files: `src/plaud_mcp/server.py:178-222`
- Why fragile: This 45-line function implements a complex 7-tier fallback precedence for selecting highlight sources. The logic was reverse-engineered from the Plaud web/desktop apps. Adding new content types or changing precedence requires understanding the full fallback chain.
- Safe modification: The function has dedicated tests for the happy path and one fallback scenario, but not for all 7 tiers. Test all precedence tiers before modifying.
- Test coverage: Partial — `TestGetHighlights` covers `high_light` success, `mark_memo` fallback on failed `high_light`, and `mark_note` markdown. Does not cover: `mark_note` selected over `mark_memo` when no `high_light` exists, or any fallback tier involving non-ready items.

## Scaling Limits

**`get_all_files` pagination cap:**
- Current capacity: `max_pages=100` x `page_size=200` = 20,000 files maximum.
- Limit: An account with more than 20,000 recordings silently truncates the file list.
- Scaling path: This limit is documented in the docstring (`client.py:155-158`). Raise `max_pages` if needed, but the real fix would be server-side filtering (which Plaud's API does not appear to support).

**`search_transcripts` hard cap at 100 files:**
- Current capacity: `_SEARCH_MAX_FILES = 100` in `server.py:404`.
- Limit: Search only covers the 100 most recent files within the day window.
- Scaling path: Increase the cap (at the cost of longer search times) or implement a local search index.

## Dependencies at Risk

**No lockfile present:**
- Risk: The project has no `requirements.txt`, `uv.lock`, `Pipfile.lock`, or any other pinned dependency lockfile. `pyproject.toml` specifies minimum versions with `>=` operators (e.g., `httpx>=0.28.1`, `fastmcp>=3.2.3`, `mcp>=1.27.0`). Every `pip install .` or Docker build may resolve to different transitive dependency versions.
- Impact: Non-reproducible builds. A new release of any dependency could introduce breaking changes, security vulnerabilities, or behavior differences between development and production.
- Migration plan: Generate a lockfile using `pip-compile` (pip-tools), `uv lock`, or `pip freeze > requirements.txt` from a known-good environment. Pin in CI and Docker builds.

**Dockerfile uses `python:3.14-slim` (pre-release Python):**
- Risk: Python 3.14 is in beta/RC as of April 2026. The `python:3.14-slim` Docker image may receive breaking changes. The CI matrix only tests against Python 3.10, 3.11, and 3.12 — Python 3.14 is not tested in CI but is used in production.
- Impact: Runtime behavior in the Docker container may differ from what CI validates.
- Migration plan: Either add Python 3.14 to the CI test matrix, or change Dockerfile to use a stable Python version that matches a CI-tested version (e.g., `python:3.12-slim`).

**`fastmcp` and `mcp` are fast-moving early-stage libraries:**
- Risk: Both `fastmcp>=3.2.3` and `mcp>=1.27.0` are actively developed MCP libraries with frequent breaking changes. Without a lockfile, a `pip install` could pull a version with incompatible API changes.
- Impact: Broken builds or subtle runtime behavior changes.
- Migration plan: Pin to exact versions in a lockfile. Monitor changelogs before upgrading.

## Missing Critical Features

**No authentication on the MCP HTTP transport:**
- Problem: When running in HTTP mode (`MCP_TRANSPORT=http`), the server binds to port 8080 with no authentication. Any client that can reach the port can invoke all 11 tools. The K8s deployment mitigates this with ClusterIP, but the Docker Compose deployment exposes the port to the host network.
- Blocks: Multi-user deployment, exposure beyond localhost.

**No structured logging:**
- Problem: The codebase has zero logging calls. Errors in `search_transcripts` are silently swallowed (`except Exception: continue` at `server.py:581`). There is no way to diagnose failed API calls, S3 download failures, or auth issues in production without attaching a debugger.
- Blocks: Operational visibility, incident investigation, audit trail compliance.

**No rate limiting on outbound Plaud API calls:**
- Problem: `search_transcripts` can fire up to 200 HTTP requests (100 detail + 100 S3) in rapid succession. `get_all_files` can fire up to 100 pagination requests. There is no rate limiter or backoff strategy.
- Blocks: Could trigger Plaud API rate limiting or account suspension.

## Test Coverage Gaps

**`_select_highlight_content_item` precedence tiers not fully covered:**
- What's not tested: The 7-tier fallback logic has 3 tested paths out of ~7 possible selection outcomes. Missing test cases: `mark_note` preferred over `mark_memo` when no `high_light` exists; fallback to non-ready items; empty `content_list`.
- Files: `src/plaud_mcp/server.py:178-222`, `tests/test_server.py:362-458`
- Risk: Precedence regressions would go unnoticed.
- Priority: Medium

**`_fetch_s3_content` never tested with real gzip decompression:**
- What's not tested: The synchronous `_fetch_s3_content` helper is always bypassed in tests by mocking `asyncio.to_thread`. The gzip decompression path, `json.JSONDecodeError` fallback to `raw.decode("utf-8")`, and `httpx.get` error handling are untested.
- Files: `src/plaud_mcp/server.py:146-166`
- Risk: A change to the S3 response format (e.g., uncompressed responses) would break silently.
- Priority: Medium

**`_fetch_all_folder_candidate_files` pagination edge cases:**
- What's not tested: The multi-page pagination in `_fetch_all_folder_candidate_files` (early termination on `data_file_total`, partial page detection, `MAX_FILE_LIST_PAGES` cap) has no dedicated unit tests. The `get_folder_files` test only exercises a single-page response.
- Files: `src/plaud_mcp/server.py:315-336`, `tests/test_server.py:486-520`
- Risk: Pagination bugs (off-by-one, infinite loops) could go undetected.
- Priority: Low

**No test for `health_check` endpoint:**
- What's not tested: The `/health` custom route (`server.py:41-45`) has no test. If FastMCP changes its custom route API, the health check could silently break, causing K8s liveness probe failures.
- Files: `src/plaud_mcp/server.py:41-45`
- Risk: K8s pod restart loops in production.
- Priority: Medium

**`get-token.py` decrypt/derive path untested with real crypto:**
- What's not tested: The `derive_key` and `decrypt_token` functions are monkeypatched out in tests. The actual PBKDF2+AES decryption flow is never exercised.
- Files: `scripts/get-token.py:50-76`, `tests/test_get_token.py`
- Risk: Low — these functions are straightforward wrappers around the `cryptography` library.
- Priority: Low

**`config.py` `get_token()` priority and edge cases:**
- What's not tested: When both `plaud_token` and `plaud_token_file` are set, `get_token()` prefers `plaud_token_file`. This priority behavior has no explicit test. The `model_validator` that requires at least one token source is tested in `test_client.py`.
- Files: `src/plaud_mcp/config.py:39-44`
- Risk: A refactor could silently swap priority.
- Priority: Low

---

*Concerns audit: 2026-04-13*
