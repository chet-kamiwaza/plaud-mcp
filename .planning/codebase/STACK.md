# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- Python >=3.10 - All application code, scripts, and tests

**Secondary:**
- YAML - Kubernetes manifests (`deploy/deployment.yaml`, `deploy/service.yaml`, `deploy/secret.yaml`), Docker Compose (`docker-compose.yml`)
- TOML - Build configuration (`pyproject.toml`)

## Runtime

**Environment:**
- Python 3.14-slim (Docker image base: `python:3.14-slim` in `Dockerfile`)
- Requires Python >=3.10 per `pyproject.toml`

**Package Manager:**
- pip (used directly in `Dockerfile` via `pip install --no-cache-dir .`)
- No lockfile present (no `requirements.txt`, `pip-tools`, or `poetry.lock`)
- Build system: setuptools >=82.0.1 (`pyproject.toml` `[build-system]`)

## Frameworks

**Core:**
- FastMCP >=3.2.3 - MCP server framework; creates the `FastMCP("plaud")` application instance in `src/plaud_mcp/server.py`
- MCP >=1.27.0 - Model Context Protocol SDK (underlying protocol library used by FastMCP)

**HTTP Client:**
- httpx >=0.28.1 - Async HTTP client for Plaud API calls (`src/plaud_mcp/client.py`) and synchronous S3 content fetches (`src/plaud_mcp/server.py`)

**Configuration:**
- pydantic-settings >=2.13.1 - Environment-based settings with validation (`src/plaud_mcp/config.py`)

**Testing:**
- pytest >=9.0.3 - Test runner (config in `pyproject.toml` `[tool.pytest.ini_options]`)
- pytest-asyncio - Async test support (asyncio_mode = "auto")
- respx - httpx mock/stub library for testing HTTP calls

**Build/Dev:**
- setuptools >=82.0.1 - Build backend (`pyproject.toml` `[build-system]`)
- Docker - Container build and runtime (`Dockerfile`)
- Docker Compose - Local development orchestration (`docker-compose.yml`)

## Key Dependencies

**Critical:**
- `fastmcp` >=3.2.3 - The entire server is built on FastMCP's `@mcp.tool()` decorator pattern and transport handling (stdio + streamable-http)
- `httpx` >=0.28.1 - All Plaud API communication goes through `httpx.AsyncClient` (authenticated) and `httpx.get` (S3 signed URLs)
- `pydantic-settings` >=2.13.1 - Settings singleton (`src/plaud_mcp/config.py`) validates required env vars at import time; failure here prevents startup

**Infrastructure:**
- `gzip` (stdlib) - Decompresses S3 transcript/summary/highlight payloads in `_fetch_s3_content()`
- `starlette` (transitive via FastMCP) - Used for the `/health` custom route response (`JSONResponse`)

**Script-only (not installed as dependencies):**
- `cryptography` - Required by `scripts/get-token.py` for decrypting Plaud desktop app token (PBKDF2 + AES-128-CBC)

## Configuration

**Environment:**
- `PLAUD_TOKEN` - Bearer token for Plaud API authentication (or use `PLAUD_TOKEN_FILE`)
- `PLAUD_TOKEN_FILE` - Path to file containing the bearer token (alternative to `PLAUD_TOKEN`; supports rotation without restart)
- `PLAUD_DEVICE_ID` - Device UUID sent as `X-Device-Id` header (required)
- `MCP_TRANSPORT` - Transport mode: `stdio` (default) or `http` (`src/plaud_mcp/__main__.py`)
- `PLAUD_BASE_URL` - API base URL, defaults to `https://api.plaud.ai` (`src/plaud_mcp/config.py`)
- `PLAUD_APP_VERSION` - App version header, defaults to `5.3.9` (`src/plaud_mcp/config.py`)
- `.env` file supported via pydantic-settings `env_file` config

**Build:**
- `pyproject.toml` - Single build config file (setuptools backend, project metadata, pytest config, optional dev deps)
- `Dockerfile` - Single-stage build from `python:3.14-slim`
- `docker-compose.yml` - Pulls `ghcr.io/chet-kamiwaza/plaud-mcp:latest`, exposes port 8080
- `.dockerignore` - Excludes tests, scripts, .planning, .git, .env, docs from build context

## Entry Point

**CLI:**
- `plaud-mcp` console script -> `plaud_mcp.__main__:main` (defined in `pyproject.toml` `[project.scripts]`)
- `python -m plaud_mcp` -> `src/plaud_mcp/__main__.py`

**Transport modes:**
- `stdio` (default) - MCP over stdin/stdout for Claude Code / Claude Desktop
- `http` - MCP over streamable-http on `0.0.0.0:8080` for Kubernetes / container deployments

## Platform Requirements

**Development:**
- Python >=3.10
- macOS recommended (token extraction script `scripts/get-token.py` requires macOS Keychain + Plaud desktop app)
- Docker Desktop for container-based development

**Production:**
- Docker or Kubernetes cluster
- Container runs as non-root UID 1000 (`Dockerfile` line 25-26)
- Port 8080 exposed only in HTTP transport mode
- Resource limits: CPU 50m-500m, Memory 64Mi-256Mi (`deploy/deployment.yaml` lines 43-48)

---

*Stack analysis: 2026-04-13*
