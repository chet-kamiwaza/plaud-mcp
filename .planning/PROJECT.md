# Plaud MCP Server

## What This Is

A containerized MCP (Model Context Protocol) server that exposes Plaud cloud API data as tools for AI assistants. Deployed as a single Docker container on Kubernetes, it gives Claude and other MCP clients access to a user's Plaud recordings, transcripts, and AI summaries — with no Desktop app dependency.

## Core Value

An MCP client can query a user's Plaud recordings, transcripts, and summaries via a self-hosted container using only an injected bearer token.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] MCP server exposes tools: check_connection, get_file_count, get_recent_files, get_files, get_file, get_transcript, get_summary, search_transcripts
- [ ] Auth via bearer token injected as environment variable (PLAUD_TOKEN)
- [ ] Device UUID injected as environment variable (PLAUD_DEVICE_ID) — required by Plaud API
- [ ] All required Plaud API headers sent on every request (Authorization, X-Device-Id, edit-from, app-platform, app-versionNumber, app-language)
- [ ] Handles Plaud -302 domain redirect (updates base URL and retries)
- [ ] Handles -10000 auth error (surfaces clear error to MCP client)
- [ ] Runs as MCP server over stdio transport (for Claude Code / Claude Desktop integration)
- [ ] Also supports HTTP/SSE transport for Kubernetes service exposure
- [ ] Packages cleanly as a single Docker image with all dependencies
- [ ] Kubernetes-deployable: env var config, health endpoint, liveness probe

### Out of Scope

- CDP / Plaud Desktop dependency — requires Desktop app running; unusable in containers
- Official developer API (platform.plaud.cn) — user has personal account only, no client credentials
- Token refresh / OAuth flow — token injected manually; expiry handled by re-injecting
- Audio recording or upload — cloud read-only client
- macOS / Windows deployment targets

## Context

**What Plaud is:** Electron desktop app for the Plaud AI transcription service (`ai.plaud.desktop.plaud`, v1.0.5). Users record with Plaud hardware devices; recordings, transcripts, and AI summaries live in Plaud's cloud.

**Source analysis:** Reverse-engineered from compiled macOS app bundle. Source maps recovered 263 TypeScript files (729KB). API client code fully understood. Extracted source in `/tmp/plaud-src/`.

**Reference implementation:** `github.com/davidlinjiahao/plaud-mcp` — uses Chrome DevTools Protocol (CDP) to piggyback on the running Desktop app's authenticated session. Works locally on macOS; fundamentally incompatible with container deployment (requires `pgrep "Plaud.app/Contents/MacOS/Plaud"` + `SIGUSR1`).

**API:** Base URL `https://api.plaud.ai`. Required headers on every request:
```
Authorization: bearer <token>
edit-from: desktop
app-platform: desktop
app-versionNumber: 1.0.5
app-language: en-US
X-Device-Id: <device-uuid>
```

**Auth warning:** The reference repo's README states direct HTTP clients (httpx, curl, curl_cffi) return 401. This may be due to missing required headers rather than true Chromium-level validation. Must validate with the full header set before concluding a workaround is needed.

**Known API endpoints (from source):**
- `GET /file/simple/web?skip=&limit=&is_trash=2&sort_by=start_time&is_desc=true` — list files
- `GET /file/detail/{file_id}` — file detail + content_list (transcripts, summaries as signed S3 URLs)
- `POST /auth/access-token-auth-code` — exchange auth code for token
- `POST /auth/access-token-logout` — invalidate token
- `GET /user/me` — user profile

**Content retrieval:** File details include `content_list[]` with `data_type` and `data_link` (signed S3 URL). Transcripts are `data_type: "transaction"`, summaries are `data_type: "auto_sum_note"`. Content is gzip-compressed JSON at the S3 URL.

**Status codes:**
- `0` — success
- `-10000` — auth invalid/expired → surface as auth error
- `-302` — domain redirect → update base URL, retry
- `-9999` — application error with `data.alert` message

**Token extraction (for K8s secret injection):** Token likely in `~/Library/Application Support/Plaud/config.json` (electron-store). Device UUID in the same store or derivable from system hardware UUID.

## Constraints

- **API**: `https://api.plaud.ai` — no public docs; all knowledge from reverse engineering
- **Auth**: Bearer token + device UUID must be injected; no interactive login flow in container
- **Stack**: Python (matches reference impl, `mcp` SDK has excellent Python support)
- **Container**: Single image, no sidecar, no external state store

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rewrite (not fork) reference impl | CDP approach fundamentally incompatible with containers | — Pending |
| Python + FastMCP | MCP SDK is excellent in Python; matches reference impl stack | — Pending |
| Token injection via env var | Simplest K8s-compatible auth; token as K8s Secret | — Pending |
| Validate direct HTTP first | 401 claim may be a header issue; must test before building workarounds | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after scope pivot to MCP server + container deployment*
