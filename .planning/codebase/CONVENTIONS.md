# Coding Conventions

**Analysis Date:** 2026-04-13

## Naming Patterns

**Files:**
- Source modules: `snake_case.py` (e.g., `src/plaud_mcp/client.py`, `src/plaud_mcp/errors.py`)
- Test files: `test_<module>.py` co-located in `tests/` (e.g., `tests/test_client.py`, `tests/test_server.py`)
- Scripts: `kebab-case.py` or `snake_case.py` in `scripts/` (e.g., `scripts/get-token.py`, `scripts/discover_phase1_contracts.py`)
- Config/infra: uppercase or standard names (`Dockerfile`, `CLAUDE.md`, `SECURITY.md`)

**Functions:**
- Use `snake_case` for all functions and methods
- Private helpers prefixed with underscore: `_fetch_s3_content()`, `_highlight_item_is_ready()`, `_normalize_highlight_entry()`
- Public methods are plain snake_case: `get_all_files()`, `get_token()`
- MCP tool functions are bare snake_case matching the tool name: `check_connection()`, `get_transcript()`

**Variables:**
- Use `snake_case` for all local variables and parameters
- Module-level constants are `UPPER_SNAKE_CASE`: `HIGHLIGHT_SUCCESS_STATUS`, `FILE_LIST_PAGE_SIZE`, `MAX_FILE_LIST_PAGES`, `_SEARCH_MAX_FILES`
- Private module constants may use underscore prefix: `_SEARCH_MAX_FILES`

**Classes:**
- Use `PascalCase`: `PlaudClient`, `PlaudError`, `PlaudAuthError`, `PlaudAPIError`, `Settings`

**Types:**
- Use Python 3.10+ union syntax: `str | None`, `list[dict]`, `dict | None`
- Import `from __future__ import annotations` at top of module for forward references

## Code Style

**Formatting:**
- No explicit formatter configured (no black, ruff, or yapf config files)
- 4-space indentation (standard Python)
- Line length appears informal; some lines exceed 100 characters in docstrings and complex expressions
- Trailing commas used in multi-line function signatures and dicts

**Linting:**
- **Bandit** (security): Run via GitHub Actions (`bandit -r src/ -ll -f sarif`), scans `src/` only
- **Codacy** (aggregate): Runs pylint, pylintpython3, prospector, bandit, markdownlint via `.codacy.yml`
- **Markdownlint**: Configured in `.markdownlint.yaml` (in worktree; propagated via Codacy)
- No local linter config (no `.flake8`, `ruff.toml`, `.pylintrc`) -- linting is CI-only via Codacy

**Codacy Exclusions** (from `.codacy.yml` in worktree):
- `.planning/**` and `.claude/**` excluded globally
- `tests/**` and `scripts/**` excluded from pylint/prospector/bandit
- `SECURITY.md` excluded from markdownlint line-length

**Bandit inline suppression:** Use `# nosec B104` style comments for intentional security exceptions (see `src/plaud_mcp/__main__.py` line 20).

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first when present)
2. Standard library imports (`asyncio`, `gzip`, `json`, `os`, `time`, `pathlib`)
3. Third-party imports (`httpx`, `pydantic`, `pydantic_settings`, `fastmcp`, `pytest`, `respx`)
4. Local/project imports (`from .client import PlaudClient`, `from .config import settings`, `from .errors import ...`)

**Style:**
- Prefer `from X import Y` over bare `import X` for specific symbols
- Use relative imports within the `plaud_mcp` package: `from .config import settings`, `from .client import PlaudClient`
- Use absolute imports in tests: `from plaud_mcp.client import PlaudClient`
- Group imports by category with a blank line between groups

**Path Aliases:**
- None. The project uses `[tool.setuptools.packages.find] where = ["src"]` so the package is `plaud_mcp` importable from `src/`.

## Type Hints

**Coverage:** Moderate. All function signatures have return type annotations. Parameter types are annotated on public APIs but not always on private helpers.

**Patterns:**
- Return types always specified: `-> dict`, `-> list[dict]`, `-> str`, `-> None`, `-> "PlaudClient"`, `-> "Settings"`
- Use `Any` sparingly: `from typing import Any` when payload shape is unknown (e.g., `_normalize_highlight_entry(item: Any)`)
- Union types use `|` syntax (Python 3.10+): `str | None = None`, `dict | None`, `list[str] | None`
- Forward references via `from __future__ import annotations`
- Pydantic model fields typed directly in the class body (`plaud_token: str | None = None`)

## Docstrings

**Style:** Google-style docstrings (one-line summary, then `Args:` and `Returns:` sections).

**Module-level docstrings:** Always present. Include:
- Description of what the module provides
- Numbered requirement IDs (e.g., `AUTH-02`, `AUTH-03`, `TOOL-01` through `TOOL-11`)
- Security threat IDs (e.g., `T-01-02`, `T-02-01`)

**Function docstrings:** Present on all public functions and MCP tools. Pattern:
```python
async def get_transcript(file_id: str) -> dict:
    """Return the full transcript with speaker labels for a recording.

    Fetches the file detail from Plaud API, then downloads and decompresses
    the transcript from the signed S3 URL in content_list.

    Args:
        file_id: The Plaud file identifier (non-empty string).

    Returns a dict with file_id, transcript (full parsed JSON), and speaker_count.
    Raises ValueError if file_id is empty or no transcript is found.
    """
```

**Private helper docstrings:** One-line summaries, sometimes with inline security annotations:
```python
def _fetch_s3_content(data_link: str) -> Any:
    """Fetch and decompress gzip-compressed content from a signed S3 URL.

    Security: T-02-02 — data_link must be sourced from Plaud API content_list[].data_link,
    never from MCP caller input.
    """
```

**Test docstrings:** Present on test classes (mapping to requirement IDs) and individual test methods:
```python
class TestAuth02Headers:
    """AUTH-02: All six required headers present on every request."""

    async def test_all_required_headers_sent(self):
        """Every GET request must include all six AUTH-02 headers."""
```

## Error Handling

**Custom exception hierarchy** (defined in `src/plaud_mcp/errors.py`):
```
PlaudError (base)
├── PlaudAuthError  — token invalid/expired (API status -10000)
└── PlaudAPIError   — any other non-zero API status
```

**Patterns:**
- MCP tool functions validate input with `ValueError` for empty/whitespace IDs:
  ```python
  if not file_id or not file_id.strip():
      raise ValueError("file_id must be a non-empty string")
  ```
- `PlaudClient._request()` maps API status codes to exceptions:
  - `status == 0` -> success, return body
  - `status == -302` -> domain redirect, retry once
  - `status == -10000` -> `PlaudAuthError`
  - All other non-zero -> `PlaudAPIError`
- Token config errors wrapped as `RuntimeError` then re-raised as `PlaudAuthError`
- In `search_transcripts`, per-file fetch errors are silently caught with bare `except Exception: continue` to allow partial results
- `httpx` HTTP errors propagate via `response.raise_for_status()`

**Input sanitization:**
- All string ID inputs are stripped: `file_id.strip()`, `folder_id.strip()`, `query.strip()`
- Empty-after-strip values rejected with `ValueError`

## Configuration

**Settings pattern:** Single `pydantic_settings.BaseSettings` subclass in `src/plaud_mcp/config.py`, instantiated as module-level singleton `settings = Settings()`.

**Environment variables:**
- `PLAUD_TOKEN` — bearer token (or use `PLAUD_TOKEN_FILE`)
- `PLAUD_TOKEN_FILE` — path to file containing token (hot-reloadable)
- `PLAUD_DEVICE_ID` — required device UUID
- `PLAUD_BASE_URL` — API base URL (default: `https://api.plaud.ai`)
- `PLAUD_APP_VERSION` — spoofed app version (default: `5.3.9`)
- `MCP_TRANSPORT` — `stdio` or `http` (read in `__main__.py`, not in Settings)

**Env file:** `.env` loaded by pydantic-settings; `.env.example` provided as template.

## Logging

**Framework:** None. The codebase uses no logging framework. Errors propagate as exceptions; `print()` is used only in scripts (`scripts/get-token.py`).

## Module Design

**Exports:**
- `src/plaud_mcp/__init__.py` is empty (no re-exports)
- Each module has a clear single responsibility: config, client, errors, server, entrypoint

**Barrel Files:** Not used.

**Module-level singletons:**
- `settings = Settings()` in `src/plaud_mcp/config.py`
- `mcp = FastMCP("plaud")` in `src/plaud_mcp/server.py`

**Async patterns:**
- `PlaudClient` is an async context manager (`async with PlaudClient() as client:`)
- MCP tools are all `async def` decorated with `@mcp.tool()`
- Synchronous I/O (S3 content fetch) wrapped with `asyncio.to_thread()`

## Security Conventions

- Security annotations in docstrings reference threat model IDs (e.g., `T-01-02`, `T-02-01`)
- Token values never logged; redirect domains validated against `*.plaud.ai`
- Container runs as non-root UID 1000 (`Dockerfile`)
- Secrets never baked into Docker image; injected at runtime
- Bandit inline suppressions documented with comment: `# nosec B104`

---

*Convention analysis: 2026-04-13*
