# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Framework

**Runner:**
- pytest >= 9.0.3
- Config: `pyproject.toml` `[tool.pytest.ini_options]`

**Async Support:**
- pytest-asyncio with `asyncio_mode = "auto"` (all async test methods run automatically without `@pytest.mark.asyncio`)

**HTTP Mocking:**
- respx (for httpx-based client tests)
- unittest.mock (AsyncMock, MagicMock, patch) for server tool tests

**Run Commands:**
```bash
pytest                 # Run all tests
pytest tests/          # Run all tests explicitly
pytest -v              # Verbose output
```

No coverage tool is configured. No Makefile or tox.ini exists.

## Test File Organization

**Location:** Separate `tests/` directory at project root (not co-located with source).

**Naming:** `test_<source_module>.py` mirrors source module names:
```
tests/
├── __init__.py            # Empty
├── conftest.py            # Shared fixtures and env setup
├── test_client.py         # Tests for src/plaud_mcp/client.py
├── test_server.py         # Tests for src/plaud_mcp/server.py (all 11 MCP tools)
├── test_get_token.py      # Tests for scripts/get-token.py
```

**Test-to-source mapping:**
| Test File | Source File | Scope |
|-----------|------------|-------|
| `tests/test_client.py` | `src/plaud_mcp/client.py` | PlaudClient auth, redirect, pagination |
| `tests/test_server.py` | `src/plaud_mcp/server.py` | All 11 MCP tool functions |
| `tests/test_get_token.py` | `scripts/get-token.py` | Token extraction script |

## Test Configuration

**`pyproject.toml`:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Dev dependencies** (installed via `pip install .[dev]`):
```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio",
    "respx",
]
```

## Test Structure

**Suite organization:** Tests are grouped into classes by feature/requirement. Each class maps to a named requirement or component:

```python
class TestAuth02Headers:
    """AUTH-02: All six required headers present on every request."""

    @respx.mock
    async def test_all_required_headers_sent(self):
        """Every GET request must include all six AUTH-02 headers."""
        ...

class TestAuth03Redirect:
    """AUTH-03: -302 redirect updates base URL and retries once."""

    @respx.mock
    async def test_redirect_updates_base_url_and_retries(self):
        ...

    @respx.mock
    async def test_redirect_loop_guard(self):
        ...
```

**Server tool test classes** follow TOOL-NN naming from `server.py` module docstring:
```python
class TestCheckConnection:     # TOOL-01
class TestGetFileCount:        # TOOL-02
class TestGetRecentFiles:      # TOOL-03
class TestGetFiles:            # TOOL-04
class TestGetFile:             # TOOL-05
class TestGetTranscript:       # TOOL-06
class TestGetSummary:          # TOOL-07
class TestGetHighlights:       # TOOL-08
class TestListFolders:         # TOOL-09
class TestGetFolderFiles:      # TOOL-10
class TestSearchTranscripts:   # TOOL-11
```

**Test method naming:** `test_<behavior_description>` in snake_case:
- `test_returns_connected_status_and_file_count`
- `test_auth_error_propagates`
- `test_redirect_rejects_non_plaud_domain`
- `test_empty_file_id_raises_value_error`

## Shared Setup (conftest.py)

**Location:** `tests/conftest.py`

**Environment variable injection:** Required env vars are set at module level (before any plaud_mcp imports) AND via an autouse fixture:

```python
# Module-level — prevents pydantic-settings ValidationError at import time
os.environ.setdefault("PLAUD_TOKEN", "test-token-abc123")
os.environ.setdefault("PLAUD_DEVICE_ID", "test-device-uuid-001")

@pytest.fixture(autouse=True)
def plaud_env_vars(monkeypatch):
    """Inject required env vars so Settings() does not raise during tests."""
    monkeypatch.setenv("PLAUD_TOKEN", "test-token-abc123")
    monkeypatch.setenv("PLAUD_DEVICE_ID", "test-device-uuid-001")
```

**Why both:** The `Settings()` singleton in `src/plaud_mcp/config.py` is instantiated at import time. The module-level `setdefault` ensures collection does not fail. The autouse fixture ensures each test has clean env state.

## Mocking Patterns

### Pattern 1: respx for HTTP Client Tests (`tests/test_client.py`)

Used when testing `PlaudClient` directly — mocks at the httpx transport level:

```python
@respx.mock
async def test_all_required_headers_sent(self):
    route = respx.get("https://api.plaud.ai/user/current").mock(
        return_value=httpx.Response(
            200, json={"status": 0, "data": {"id": "user-123"}}
        )
    )

    async with PlaudClient() as client:
        await client.get("/user/current")

    request = route.calls[0].request
    headers = {k.lower(): v for k, v in request.headers.items()}
    assert "authorization" in headers
```

**Side effects for multi-response sequences:**
```python
respx.get("https://api.plaud.ai/file/simple/web").mock(
    side_effect=[
        httpx.Response(200, json={"status": 0, "data_file_list": page1}),
        httpx.Response(200, json={"status": 0, "data_file_list": page2}),
    ]
)
```

### Pattern 2: unittest.mock for Server Tool Tests (`tests/test_server.py`)

Used when testing MCP tool functions — mocks `PlaudClient` entirely and patches `asyncio.to_thread`:

**Helper factory function:**
```python
def make_mock_client(get_side_effects=None, all_files=None):
    """Return a mock PlaudClient context manager."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    if get_side_effects is not None:
        if isinstance(get_side_effects, list):
            mock_client.get = AsyncMock(side_effect=get_side_effects)
        else:
            mock_client.get = AsyncMock(return_value=get_side_effects)
    else:
        mock_client.get = AsyncMock(return_value={"status": 0, "data": {}})

    mock_client.get_all_files = AsyncMock(return_value=all_files or [])
    return mock_client
```

**Usage in tests:**
```python
async def test_returns_transcript_with_speaker_count(self):
    mock_client = make_mock_client(get_side_effects=detail_resp)

    with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
         patch("plaud_mcp.server.asyncio") as mock_asyncio:
        mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
        from plaud_mcp.server import get_transcript
        result = await get_transcript("abc123")

    assert result["file_id"] == "abc123"
```

**What to mock:**
- `plaud_mcp.server.PlaudClient` — replace the real HTTP client with `make_mock_client()`
- `plaud_mcp.server.asyncio` — replace `asyncio.to_thread()` to avoid real S3 downloads
- `client_module.settings` attributes — use `patch.object()` for token file tests

**What NOT to mock:**
- The MCP tool functions themselves (those are the units under test)
- Pydantic Settings validation logic (tested via real `Settings()` instantiation)
- Helper/normalizer functions in `server.py` (tested indirectly through tool functions)

### Pattern 3: monkeypatch for Script Tests (`tests/test_get_token.py`)

Script modules loaded dynamically via `importlib.util`, then functions monkeypatched:

```python
def load_script_module():
    spec = importlib.util.spec_from_file_location("plaud_get_token", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_output_writes_token_file_without_echoing_secret(tmp_path, monkeypatch, capsys):
    module = load_script_module()
    monkeypatch.setattr(module, "get_keychain_password", lambda: "pw")
    monkeypatch.setattr(module, "derive_key", lambda password: b"key")
    monkeypatch.setattr(module, "decrypt_token", lambda encrypted_b64, key: "secret-token")
    module.main(["--output", str(output_path)])
```

## Fixtures and Factories

**Built-in fixtures used:**
- `tmp_path` — temporary directory for token file tests
- `monkeypatch` — env var and attribute patching
- `capsys` — stdout capture for script output tests

**Custom fixtures:**
- `plaud_env_vars` (autouse, in `conftest.py`) — injects `PLAUD_TOKEN` and `PLAUD_DEVICE_ID`

**Factory functions:**
- `make_mock_client()` in `tests/test_server.py` — builds a fully mocked `PlaudClient` async context manager
- `_ms(seconds_ago)` in `tests/test_server.py` — generates epoch-millisecond timestamps relative to now

## Coverage

**Requirements:** None enforced. No coverage tool configured. No `.coveragerc` or `[tool.coverage]` in `pyproject.toml`.

**Adding coverage:** To add coverage, install `pytest-cov` and run:
```bash
pytest --cov=plaud_mcp --cov-report=html
```

## Test Types

**Unit Tests:**
- All tests in the repo are unit tests
- No live network calls; all HTTP mocked via respx or unittest.mock
- Tests exercise individual functions/methods in isolation

**Integration Tests:**
- Not present. No tests exercise the full MCP server via MCP protocol.

**E2E Tests:**
- Not present. No tests run the Docker container or connect to the real Plaud API.

## CI Integration

**GitHub Actions workflow:** `.github/workflows/test.yml`

```yaml
name: Tests
on:
  push:
    branches: [ "master" ]
  pull_request:
    branches: [ "master" ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-python@v6
      with:
        python-version: ${{ matrix.python-version }}
    - run: pip install .[dev]
    - run: pytest
```

**Matrix:** Tests run against Python 3.10, 3.11, and 3.12 with `fail-fast: false`.

**Security CI (not test-related but relevant):**
- `.github/workflows/bandit.yml` — Bandit security scan on `src/` (weekly + push/PR to master), uploads SARIF
- `.github/workflows/codacy.yml` — Codacy CLI analysis (weekly + push/PR to master), uploads SARIF

## Common Patterns

**Async Testing:**
```python
# No decorator needed — asyncio_mode = "auto" handles it
async def test_returns_connected_status_and_file_count(self):
    mock_client = make_mock_client(get_side_effects=user_resp, all_files=all_files)
    with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
        from plaud_mcp.server import check_connection
        result = await check_connection()
    assert result["status"] == "connected"
```

**Error Testing:**
```python
async def test_auth_error_raises_plaud_auth_error(self):
    respx.get("https://api.plaud.ai/user/current").mock(
        return_value=httpx.Response(200, json={"status": -10000, "msg": "token expired"})
    )
    async with PlaudClient() as client:
        with pytest.raises(PlaudAuthError) as exc_info:
            await client.get("/user/current")
    message = str(exc_info.value).lower()
    assert "invalid" in message or "expired" in message
```

**Input validation testing:**
```python
async def test_empty_file_id_raises_value_error(self):
    with patch("plaud_mcp.server.PlaudClient"):
        from plaud_mcp.server import get_file
        with pytest.raises(ValueError, match="file_id must be a non-empty string"):
            await get_file("")
```

**Asserting on request details (headers, URL params):**
```python
request = route.calls[0].request
headers = {k.lower(): v for k, v in request.headers.items()}
assert "authorization" in headers
assert headers["authorization"].startswith("bearer ")
```

## Adding New Tests

**For a new MCP tool:**
1. Add a new test class in `tests/test_server.py` named `TestToolName`
2. Use `make_mock_client()` to construct the mock
3. Patch `plaud_mcp.server.PlaudClient` and optionally `plaud_mcp.server.asyncio`
4. Import the tool function inside the `with patch(...)` block
5. Test both happy path and error cases (empty input, missing data)

**For a new client feature:**
1. Add a new test class in `tests/test_client.py`
2. Use `@respx.mock` decorator
3. Mock the specific URL endpoint with `respx.get(...).mock()`
4. Create `PlaudClient()` via `async with` and call the method
5. Assert on both the return value and the outgoing request properties

**For a new script:**
1. Add `tests/test_<script_name>.py`
2. Use `importlib.util` to load the script module dynamically
3. Use `monkeypatch.setattr()` to stub external dependencies
4. Use `capsys` to capture and assert on printed output
5. Use `tmp_path` for any file I/O

---

*Testing analysis: 2026-04-13*
