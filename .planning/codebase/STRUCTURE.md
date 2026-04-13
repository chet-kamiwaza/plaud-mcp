# Codebase Structure

**Analysis Date:** 2026-04-13

## Directory Layout

```
Plaud tool/
├── src/
│   └── plaud_mcp/              # Main Python package (the MCP server)
│       ├── __init__.py          # Empty (package marker)
│       ├── __main__.py          # Entrypoint: transport selection (stdio/http)
│       ├── server.py            # 11 MCP tool definitions + helpers
│       ├── client.py            # PlaudClient: authenticated httpx async client
│       ├── config.py            # Settings (pydantic-settings): env var loading
│       └── errors.py            # PlaudError, PlaudAuthError, PlaudAPIError
├── tests/
│   ├── __init__.py              # Package marker
│   ├── conftest.py              # pytest fixtures (env var injection)
│   ├── test_server.py           # Unit tests for all 11 MCP tools
│   ├── test_client.py           # Unit tests for PlaudClient (auth, redirect, pagination)
│   └── test_get_token.py        # Unit tests for scripts/get-token.py
├── scripts/
│   ├── get-token.py             # macOS utility: extract Plaud token from desktop app
│   └── discover_phase1_contracts.py  # Discovery: generate redacted API contract artifacts
├── deploy/
│   ├── deployment.yaml          # K8s Deployment (HTTP transport, non-root, probes)
│   ├── service.yaml             # K8s Service (ClusterIP on port 8080)
│   └── secret.yaml              # K8s Secret TEMPLATE (placeholder values only)
├── .github/
│   ├── workflows/
│   │   ├── test.yml             # CI: pytest on Python 3.10/3.11/3.12
│   │   ├── bandit.yml           # CI: Bandit security scan → SARIF
│   │   └── codacy.yml           # CI: Codacy security scan → SARIF
│   └── dependabot.yml           # Dependabot: pip, docker, github-actions (weekly)
├── .planning/                   # GSD planning artifacts (gitignored)
│   ├── config.json              # GSD project configuration
│   ├── codebase/                # Codebase analysis docs (this file lives here)
│   └── phases/                  # Phase planning artifacts
├── .claude/
│   ├── settings.local.json      # Claude Code local settings
│   └── worktrees/               # Claude Code worktree configs
├── pyproject.toml               # Build config, dependencies, pytest config
├── Dockerfile                   # Single-stage python:3.14-slim, non-root UID 1000
├── docker-compose.yml           # Docker Compose: single plaud-mcp service
├── CLAUDE.md                    # Claude Code project instructions (GSD sections)
├── README.md                    # Project documentation
├── SECURITY.md                  # Security policy
├── LICENSE                      # License file
├── .env.example                 # Environment variable template (PLAUD_TOKEN, PLAUD_DEVICE_ID)
├── .gitignore                   # Ignores .planning/, __pycache__/, .env, deploy/secret.yaml
└── .dockerignore                # Excludes tests/, scripts/, deploy/, .planning/ from build
```

## Directory Purposes

**`src/plaud_mcp/`:**
- Purpose: The entire MCP server application
- Contains: 5 Python modules (server, client, config, errors, __main__) plus __init__.py
- Key files: `server.py` (608 lines, the core logic), `client.py` (185 lines, HTTP client), `config.py` (47 lines, settings)

**`tests/`:**
- Purpose: Unit tests covering all tool functions, client auth behavior, pagination, and the get-token script
- Contains: 3 test modules + conftest fixture
- Key files: `test_server.py` (all 11 tools), `test_client.py` (auth headers, redirect, pagination, token file reload), `test_get_token.py` (token extraction script)

**`scripts/`:**
- Purpose: Standalone utilities for development and API discovery
- Contains: 2 Python scripts (not part of the installable package)
- Key files: `get-token.py` (extract bearer token from macOS Plaud desktop app), `discover_phase1_contracts.py` (generate API contract artifacts from web/desktop bundles or live API)

**`deploy/`:**
- Purpose: Kubernetes manifests for production deployment
- Contains: Deployment, Service, and Secret template
- Key files: `deployment.yaml` (pod spec with probes, resource limits, security context), `secret.yaml` (template only -- real values must never be committed)

**`.github/`:**
- Purpose: CI/CD workflows and dependency management
- Contains: 3 workflow files + dependabot config
- Key files: `workflows/test.yml` (matrix test across 3 Python versions)

**`.planning/`:**
- Purpose: GSD (Get Stuff Done) planning artifacts for development workflow
- Contains: Project config, codebase analysis, phase plans
- Generated: Yes (by GSD commands)
- Committed: No (gitignored)

## Key File Locations

**Entry Points:**
- `src/plaud_mcp/__main__.py`: Package entrypoint -- transport selection and `mcp.run()`
- `src/plaud_mcp/server.py`: All 11 MCP tool definitions (line 34: `mcp = FastMCP("plaud")`)

**Configuration:**
- `src/plaud_mcp/config.py`: `Settings` pydantic model, `settings` singleton
- `pyproject.toml`: Build system, dependencies, pytest options, console scripts
- `.env.example`: Template for required env vars (`PLAUD_TOKEN`, `PLAUD_DEVICE_ID`)
- `Dockerfile`: Container build (python:3.14-slim, non-root)
- `docker-compose.yml`: Single service, HTTP transport, env passthrough

**Core Logic:**
- `src/plaud_mcp/server.py`: Tool definitions, S3 content fetching, highlight selection/normalization, folder/file normalization
- `src/plaud_mcp/client.py`: `PlaudClient` class -- auth headers, redirect handling, error mapping, pagination

**Error Handling:**
- `src/plaud_mcp/errors.py`: `PlaudError` (base), `PlaudAuthError`, `PlaudAPIError`

**Testing:**
- `tests/conftest.py`: Auto-use fixture injecting `PLAUD_TOKEN` and `PLAUD_DEVICE_ID`
- `tests/test_server.py`: 583 lines covering all 11 tools
- `tests/test_client.py`: 411 lines covering auth, redirect, pagination, token file reload
- `tests/test_get_token.py`: 56 lines covering the token extraction script

**Deployment:**
- `deploy/deployment.yaml`: K8s Deployment with liveness/readiness probes on `/health`
- `deploy/service.yaml`: ClusterIP Service on port 8080
- `deploy/secret.yaml`: Template (never committed with real values)

**CI:**
- `.github/workflows/test.yml`: pytest on push/PR to master (Python 3.10, 3.11, 3.12)
- `.github/workflows/bandit.yml`: Bandit security scan on push/PR + weekly schedule
- `.github/workflows/codacy.yml`: Codacy analysis on push/PR + weekly schedule

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `server.py`, `client.py`, `config.py`)
- Scripts: `kebab-case.py` or `snake_case.py` (e.g., `get-token.py`, `discover_phase1_contracts.py`)
- K8s manifests: `lowercase.yaml` (e.g., `deployment.yaml`, `service.yaml`)
- Workflows: `lowercase.yml` (e.g., `test.yml`, `bandit.yml`)

**Directories:**
- Python packages: `snake_case` (e.g., `plaud_mcp`)
- Top-level dirs: `lowercase` (e.g., `src`, `tests`, `scripts`, `deploy`)

**Classes:**
- PascalCase: `PlaudClient`, `Settings`, `PlaudAuthError`, `PlaudAPIError`

**Functions:**
- snake_case: `check_connection`, `get_file_count`, `_fetch_s3_content`
- Private helpers: prefixed with underscore (e.g., `_select_highlight_content_item`, `_normalize_highlight_payload`)

## Where to Add New Code

**New MCP Tool:**
- Add the `@mcp.tool()` decorated async function to `src/plaud_mcp/server.py`
- Follow the pattern: validate inputs, create `PlaudClient` context, call API, normalize response, return dict
- Add tests in `tests/test_server.py` following the existing `TestToolName` class pattern with `make_mock_client()` helper
- Update the tool list docstring at the top of `server.py`

**New Plaud API Integration:**
- If a new endpoint requires special handling, add methods to `PlaudClient` in `src/plaud_mcp/client.py`
- For new pagination patterns, follow the `get_all_files()` approach
- Add tests in `tests/test_client.py` using `respx` for HTTP mocking

**New Configuration:**
- Add fields to the `Settings` class in `src/plaud_mcp/config.py`
- Update `.env.example` with the new variable
- Update `deploy/deployment.yaml` and `deploy/secret.yaml` if the new config is secret

**New Error Type:**
- Add to `src/plaud_mcp/errors.py` inheriting from `PlaudError`
- Handle in `PlaudClient._request()` in `src/plaud_mcp/client.py`

**New Utility Script:**
- Add to `scripts/` directory
- Add tests in `tests/test_<script_name>.py` following the `test_get_token.py` pattern (dynamic module loading via importlib)

**New K8s Resource:**
- Add to `deploy/` directory
- Follow existing naming and labeling conventions (`app: plaud-mcp`)

## Special Directories

**`src/`:**
- Purpose: Python source root (setuptools `packages.find` uses `where = ["src"]`)
- Generated: No
- Committed: Yes

**`.planning/`:**
- Purpose: GSD planning and codebase analysis artifacts
- Generated: Yes (by GSD commands and codebase mapping)
- Committed: No (in `.gitignore`)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (in `.gitignore`)

**`.pytest_cache/`:**
- Purpose: pytest incremental test cache
- Generated: Yes (by pytest)
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2026-04-13*
