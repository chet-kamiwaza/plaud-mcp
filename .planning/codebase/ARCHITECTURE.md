# Architecture

**Analysis Date:** 2026-04-13

## Pattern Overview

**Overall:** Single-process MCP (Model Context Protocol) server exposing a reverse-engineered cloud API as AI-consumable tools.

**Key Characteristics:**
- **Thin tool layer over HTTP proxy** -- each MCP tool is a stateless async function that instantiates a `PlaudClient`, calls the Plaud cloud API, transforms the response, and returns a normalized dict.
- **No local state** -- no database, no cache, no session store. Every tool invocation starts fresh with a new `PlaudClient` context manager.
- **Dual transport** -- runs as stdio (for Claude Code / Claude Desktop) or streamable-http on port 8080 (for Kubernetes / Docker).
- **Security-first auth** -- bearer token and device UUID are injected via environment; never baked into images. Token can optionally be read from a file at each request for hot-reload.

## Layers

**Transport Layer (FastMCP runtime):**
- Purpose: Accept MCP protocol messages and dispatch them to registered tool functions.
- Location: Handled by FastMCP library; configured in `src/plaud_mcp/__main__.py`
- Contains: Transport selection logic (stdio vs streamable-http), health check endpoint
- Depends on: `fastmcp` library, `mcp` SDK
- Used by: MCP clients (Claude Code, Claude Desktop, remote HTTP clients)

**Tool Layer:**
- Purpose: Define the 11 MCP tools that MCP clients can invoke. Each tool is a decorated async function.
- Location: `src/plaud_mcp/server.py`
- Contains: Tool definitions (`@mcp.tool()`), response normalization helpers, S3 content fetching, highlight selection logic
- Depends on: `PlaudClient` from `src/plaud_mcp/client.py`
- Used by: FastMCP runtime (dispatches incoming tool calls to these functions)

**HTTP Client Layer:**
- Purpose: Authenticated async HTTP client handling all communication with `api.plaud.ai`. Encapsulates auth headers, domain redirects, and error mapping.
- Location: `src/plaud_mcp/client.py`
- Contains: `PlaudClient` class with async context manager protocol, request method with status code handling, pagination helper `get_all_files()`
- Depends on: `Settings` from `src/plaud_mcp/config.py`, error classes from `src/plaud_mcp/errors.py`, `httpx` library
- Used by: Tool layer (`server.py`)

**Configuration Layer:**
- Purpose: Load and validate runtime settings from environment variables / `.env` file.
- Location: `src/plaud_mcp/config.py`
- Contains: `Settings` pydantic-settings model, singleton `settings` instance, token-file read logic
- Depends on: `pydantic-settings` library
- Used by: `PlaudClient` (reads token and device ID on every request)

**Error Layer:**
- Purpose: Typed exception hierarchy for Plaud API errors.
- Location: `src/plaud_mcp/errors.py`
- Contains: `PlaudError` (base), `PlaudAuthError` (status -10000), `PlaudAPIError` (other non-zero)
- Depends on: Nothing (pure Python exceptions)
- Used by: `PlaudClient` raises these; tool functions propagate them to MCP runtime

## Data Flow

**Standard Tool Invocation (e.g. get_transcript):**

```
MCP Client (Claude)
    |
    v
FastMCP Runtime (stdio or streamable-http)
    |
    v
@mcp.tool() async function in server.py
    |
    v
PlaudClient.__aenter__() — creates httpx.AsyncClient with auth headers
    |
    v
PlaudClient.get("/file/detail/{file_id}") — sends request to api.plaud.ai
    |                                         handles -302 redirect, -10000 auth error
    v
Parse response → extract content_list → find "transaction" item → get data_link
    |
    v
asyncio.to_thread(_fetch_s3_content, data_link) — download gzip from signed S3 URL
    |                                                (no auth headers; URL is self-signed)
    v
Decompress gzip → parse JSON → build normalized response dict
    |
    v
Return dict to MCP client
```

**Authentication Flow:**

```
Settings() singleton — loaded at import time from env / .env
    |
    +-- PLAUD_TOKEN (direct env var) or PLAUD_TOKEN_FILE (path to file)
    +-- PLAUD_DEVICE_ID (device UUID)
    |
PlaudClient._refresh_auth_headers() — called before EVERY request
    |
    +-- settings.get_token() — if plaud_token_file is set, reads file each time
    |                           (enables hot-reload of rotated tokens)
    +-- Sets Authorization: bearer {token}
    +-- Sets X-Device-Id: {device_id}
```

**Domain Redirect Flow (AUTH-03):**

```
Request to api.plaud.ai
    |
    v
Response status == -302, body has data.domains.api
    |
    v
Validate new domain ends with "plaud.ai" (T-01-02)
    |
    v
Update httpx client base_url → retry request once
    |
    v
_redirect_attempted flag prevents infinite loops
```

**State Management:**
- No persistent state. Each tool call creates a fresh `PlaudClient` via `async with PlaudClient() as client:`.
- The `Settings` singleton (`config.settings`) is created once at module import time and reused across all requests.
- Token file is re-read on every request when `PLAUD_TOKEN_FILE` is configured, enabling external token rotation without restart.

## Key Abstractions

**PlaudClient (Async Context Manager):**
- Purpose: Single-request-lifecycle HTTP client for the Plaud cloud API
- Location: `src/plaud_mcp/client.py`
- Pattern: `async with PlaudClient() as client:` — creates httpx.AsyncClient, refreshes auth headers before each `.get()` call, closes on exit
- Handles application-level status codes: 0 (success), -302 (redirect), -10000 (auth error)

**Settings (Pydantic BaseSettings):**
- Purpose: Configuration validated at startup, token retrieval at request time
- Location: `src/plaud_mcp/config.py`
- Pattern: Module-level singleton (`settings = Settings()`). Supports both direct `PLAUD_TOKEN` env var and `PLAUD_TOKEN_FILE` for file-based token injection (K8s Secret mount).

**FastMCP Tool Registry:**
- Purpose: Each `@mcp.tool()` function is auto-registered as an MCP tool with name, description, and parameter schema derived from the function signature and docstring.
- Location: `src/plaud_mcp/server.py`, line `mcp = FastMCP("plaud")`
- Pattern: Decorator-based registration; FastMCP handles JSON schema generation from type hints.

**Content Item Selection (Highlights):**
- Purpose: The Plaud API returns multiple content items per recording (transcript, summary, high_light, mark_memo, mark_note). The highlight tools use a precedence-based selector to pick the best available source.
- Location: `src/plaud_mcp/server.py` — `_select_highlight_content_item()`, `_highlight_item_is_ready()`
- Pattern: Priority cascade: ready high_light > (failed high_light + ready mark_memo) > ready mark_note > ready mark_memo > fallback high_light > fallback mark_note > fallback mark_memo

## Entry Points

**Package Entrypoint (`python -m plaud_mcp`):**
- Location: `src/plaud_mcp/__main__.py`
- Triggers: Docker CMD, CLI invocation, `plaud-mcp` console script
- Responsibilities: Read `MCP_TRANSPORT` env var, call `mcp.run()` with appropriate transport (stdio or streamable-http on 0.0.0.0:8080)

**Console Script (`plaud-mcp`):**
- Location: Defined in `pyproject.toml` `[project.scripts]`, points to `plaud_mcp.__main__:main`
- Triggers: After `pip install .`, the `plaud-mcp` command is available on PATH

**Health Check Endpoint:**
- Location: `src/plaud_mcp/server.py` — `@mcp.custom_route("/health", methods=["GET"])`
- Triggers: Kubernetes liveness/readiness probes (HTTP mode only)
- Responsibilities: Returns `{"status": "ok"}` — lightweight check that the process is alive

## The 11 MCP Tools

| ID | Function | Plaud API Endpoint(s) | S3 Download |
|----|----------|----------------------|-------------|
| TOOL-01 | `check_connection()` | `/user/me`, `/file/simple/web` (all pages) | No |
| TOOL-02 | `get_file_count()` | `/file/simple/web` (all pages) | No |
| TOOL-03 | `get_recent_files(days)` | `/file/simple/web` (all pages) | No |
| TOOL-04 | `get_files(start_date, end_date, limit)` | `/file/simple/web` (all pages) | No |
| TOOL-05 | `get_file(file_id)` | `/file/detail/{file_id}` | No |
| TOOL-06 | `get_transcript(file_id)` | `/file/detail/{file_id}` | Yes (gzip JSON) |
| TOOL-07 | `get_summary(file_id)` | `/file/detail/{file_id}` | Yes (gzip JSON) |
| TOOL-08 | `get_highlights(file_id)` | `/file/detail/{file_id}` | Yes (gzip JSON) |
| TOOL-09 | `list_folders()` | `/filetag/` | No |
| TOOL-10 | `get_folder_files(folder_id)` | `/filetag/`, `/file/simple/web` (paginated) | No |
| TOOL-11 | `search_transcripts(query, days)` | `/file/simple/web`, `/file/detail/{id}` per file | Yes (per file) |

## Error Handling

**Strategy:** Typed exception hierarchy with fail-fast semantics. Errors propagate to the MCP runtime which serializes them for the client.

**Patterns:**
- `PlaudAuthError` raised for invalid/expired tokens (Plaud status -10000). When `PLAUD_TOKEN_FILE` is configured, a single reload-and-retry is attempted before raising.
- `PlaudAPIError` raised for all other non-zero Plaud status codes.
- `ValueError` raised for invalid tool inputs (empty `file_id`, empty `query`).
- HTTP transport errors (httpx exceptions) propagate directly.
- In `search_transcripts`, per-file errors are silently caught to avoid one bad file aborting the entire search.

**Input Validation:**
- `file_id` and `folder_id` parameters are validated non-empty and stripped of whitespace before use (security control T-02-01).
- `data_link` URLs for S3 downloads are never accepted from MCP caller input -- they are always sourced from Plaud API responses (security control T-02-02).

## Cross-Cutting Concerns

**Logging:** No structured logging framework. Errors propagate as exceptions. No request/response logging in production code.

**Validation:** Input validation via explicit checks at the top of each tool function. Configuration validation via pydantic-settings model validator at import time.

**Authentication:** Bearer token + device UUID injected via environment. Token refreshed from settings before every HTTP request. Domain redirect validated against `*.plaud.ai`. See AUTH-02, AUTH-03, AUTH-04 contracts in client module docstring.

**Security Controls (documented in code):**
- T-01-01: Token value never logged (only last 4 chars safe to log)
- T-01-02: Redirect domain validated against *.plaud.ai
- T-01-03: `_redirect_attempted` flag prevents infinite redirect loops
- T-01-05: 30-second timeout on all requests
- T-02-01: file_id validated non-empty before URL construction
- T-02-02: S3 URLs only sourced from API response, never caller input
- T-03-01: Credentials never baked into Docker image
- T-03-02: Container runs as non-root UID 1000
- T-03-03: Secret template with placeholder values only
- T-03-04: ClusterIP service prevents direct external exposure

---

*Architecture analysis: 2026-04-13*
