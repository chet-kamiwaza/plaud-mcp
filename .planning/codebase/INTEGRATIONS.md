# External Integrations

**Analysis Date:** 2026-04-13

## APIs & External Services

**Plaud Cloud API:**
- Base URL: `https://api.plaud.ai` (configurable via `PLAUD_BASE_URL`)
- No public documentation; all endpoints reverse-engineered from Plaud web/desktop apps
- Client: `src/plaud_mcp/client.py` (`PlaudClient` class, wraps `httpx.AsyncClient`)
- Auth: Bearer token via `Authorization` header + device UUID via `X-Device-Id` header
- Required env vars: `PLAUD_TOKEN` (or `PLAUD_TOKEN_FILE`) + `PLAUD_DEVICE_ID`

**Plaud API Endpoints Used:**
| Endpoint | Method | Used By | Purpose |
|----------|--------|---------|---------|
| `/user/me` | GET | `check_connection()` in `src/plaud_mcp/server.py` | Verify token, get user info |
| `/file/simple/web` | GET | `PlaudClient.get_all_files()` in `src/plaud_mcp/client.py`, `_fetch_all_folder_candidate_files()` in `src/plaud_mcp/server.py` | Paginated file listing |
| `/file/detail/{file_id}` | GET | `get_file()`, `get_transcript()`, `get_summary()`, `get_highlights()` in `src/plaud_mcp/server.py` | File metadata + content_list with S3 URLs |
| `/filetag/` | GET | `list_folders()`, `get_folder_files()` in `src/plaud_mcp/server.py` | List Plaud folders (file tags) |

**Plaud API Request Headers (AUTH-02):**
All requests include these headers set in `src/plaud_mcp/client.py` lines 33-43:
- `Authorization: bearer {token}`
- `X-Device-Id: {device_id}`
- `edit-from: desktop`
- `app-platform: desktop`
- `app-versionNumber: 5.3.9`
- `app-language: en`
- `User-Agent: Mozilla/5.0 ... Electron/29.0.0 ...`
- `Origin: https://web.plaud.ai`
- `Referer: https://web.plaud.ai/`

**Plaud API Status Codes:**
- `0` - Success (return response body)
- `-302` - Domain redirect; new domain in `data.domains.api` (handled in `src/plaud_mcp/client.py` lines 79-107)
- `-10000` - Auth failure / token expired; raises `PlaudAuthError` (handled in `src/plaud_mcp/client.py` lines 109-133)

**AWS S3 (Signed URLs):**
- Purpose: Hosts gzip-compressed transcript, summary, and highlight content
- Access: Signed URLs from Plaud API's `content_list[].data_link` field (no auth headers needed)
- Client: Direct `httpx.get()` call in `_fetch_s3_content()` at `src/plaud_mcp/server.py` line 160
- Content is gzip-compressed JSON, decompressed in `_fetch_s3_content()`
- Security: URLs are never sourced from MCP caller input (T-02-02)

## MCP Tools Exposed

The server exposes 11 MCP tools via `@mcp.tool()` decorators in `src/plaud_mcp/server.py`:

| Tool | Parameters | Returns |
|------|-----------|---------|
| `check_connection` | none | `{status, user_id, email, file_count}` |
| `get_file_count` | none | `{count}` |
| `get_recent_files` | `days: int = 7` | `{files, count, days}` |
| `get_files` | `start_date, end_date, limit` | `{files, count}` |
| `get_file` | `file_id: str` | file detail data dict |
| `get_transcript` | `file_id: str` | `{file_id, transcript, speaker_count}` |
| `get_summary` | `file_id: str` | `{file_id, summary}` |
| `get_highlights` | `file_id: str` | `{file_id, source_type, highlights, count}` |
| `list_folders` | none | `{folders, count}` |
| `get_folder_files` | `folder_id: str` | `{folder_id, folder_name, folder_exists, files, count}` |
| `search_transcripts` | `query: str, days: int = 30` | `{query, days, matches, match_count, files_searched}` |

**Custom HTTP Route:**
- `GET /health` - Health check endpoint for Kubernetes liveness/readiness probes (HTTP transport mode only; `src/plaud_mcp/server.py` line 41)

## Data Storage

**Databases:**
- None. The server is stateless; all data is fetched live from the Plaud API on every request.

**File Storage:**
- No local file storage for application data
- `PLAUD_TOKEN_FILE` optionally reads a token from a mounted file (supports K8s Secret volume mounts and token rotation; `src/plaud_mcp/config.py` lines 24-37)

**Caching:**
- None. Every tool invocation makes fresh API calls to Plaud.

## Authentication & Identity

**Plaud API Auth:**
- Static bearer token extracted from the Plaud desktop app's Electron safeStorage
- Token extraction: `scripts/get-token.py` decrypts from `~/Library/Application Support/Plaud/encryption.json` using macOS Keychain password + PBKDF2/AES-128-CBC
- Device ID: Read from `~/Library/Application Support/Plaud/misc.json` (`systemInfo.uuid`)
- Token lifetime: ~26 days (per `README.md`)
- Token rotation: Manual re-extraction, or use `PLAUD_TOKEN_FILE` for hot-reload without restart

**MCP Client Auth:**
- No authentication between MCP client and the plaud-mcp server
- In K8s: `ClusterIP` service type prevents external exposure (T-03-04; `deploy/service.yaml` line 13)
- In Docker Compose: exposed on `localhost:8080` only

## Monitoring & Observability

**Error Tracking:**
- None. Custom exception hierarchy in `src/plaud_mcp/errors.py`: `PlaudError` -> `PlaudAuthError`, `PlaudAPIError`
- Errors propagate as MCP tool errors to the client

**Logs:**
- No logging framework configured (accepted risk AR-03 in `SECURITY.md`)
- Zero logging calls in production code (security measure T-01-01 to prevent token leakage)

**Health Checks:**
- `GET /health` returns `{"status": "ok"}` (HTTP mode only; `src/plaud_mcp/server.py` line 41)
- K8s liveness probe: `GET /health:8080`, initial delay 5s, period 15s, failure threshold 3 (`deploy/deployment.yaml` lines 50-55)
- K8s readiness probe: `GET /health:8080`, initial delay 3s, period 10s (`deploy/deployment.yaml` lines 56-60)

## CI/CD & Deployment

**Container Registry:**
- `ghcr.io/chet-kamiwaza/plaud-mcp:latest` (GitHub Container Registry)
- Referenced in `docker-compose.yml` line 3

**Docker:**
- `Dockerfile` - Single-stage build from `python:3.14-slim`
- `docker-compose.yml` - Pulls pre-built image, maps port 8080, injects env vars from `.env`
- Container runs as non-root UID 1000 (T-03-02)

**Kubernetes:**
- `deploy/deployment.yaml` - Single-replica Deployment with resource limits, health probes, and secret injection
- `deploy/service.yaml` - ClusterIP Service on port 8080
- `deploy/secret.yaml` - Template for `plaud-credentials` Secret (placeholder values; real values must not be committed per T-03-03)
- Apply: `kubectl apply -f deploy/`

**CI Pipeline:**
- Not detected (no `.github/workflows/`, `Jenkinsfile`, or similar CI config found)

## Environment Configuration

**Required env vars:**
- `PLAUD_TOKEN` or `PLAUD_TOKEN_FILE` (one required) - Plaud bearer token
- `PLAUD_DEVICE_ID` (required) - Device UUID

**Optional env vars:**
- `MCP_TRANSPORT` - `stdio` (default) or `http`
- `PLAUD_BASE_URL` - Override API base URL (default: `https://api.plaud.ai`)
- `PLAUD_APP_VERSION` - Override app version header (default: `5.3.9`)

**Env file:**
- `.env.example` - Template with placeholder values
- `.env` - Local development config (git-ignored, docker-ignored)
- pydantic-settings reads `.env` automatically (`src/plaud_mcp/config.py` line 16)

**Secrets in Kubernetes:**
- Injected via `envFrom.secretRef` referencing `plaud-credentials` Secret (`deploy/deployment.yaml` lines 39-41)
- Never baked into container image (T-03-01)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Scripts

**`scripts/get-token.py`:**
- Extracts Plaud bearer token from macOS desktop app's encrypted storage
- Reads `~/Library/Application Support/Plaud/encryption.json` (encrypted token)
- Reads `~/Library/Application Support/Plaud/misc.json` (device UUID)
- Decrypts using macOS Keychain password via `security` CLI
- Requires `cryptography` pip package (not a project dependency)
- Supports `--output` flag to write token to a file

**`scripts/discover_phase1_contracts.py`:**
- API discovery/reverse-engineering tool for documenting Plaud API contracts
- Two modes: `source` (inspects web app bundle + desktop app) and `live` (makes real API calls)
- Outputs redacted JSON artifacts to `.planning/phases/01-api-discovery-contracts/artifacts/`

---

*Integration audit: 2026-04-13*
