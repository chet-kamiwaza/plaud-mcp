# Requirements: Plaud MCP Server

**Defined:** 2026-04-08
**Core Value:** An MCP client can query a user's Plaud recordings, transcripts, and summaries via a self-hosted container using only an injected bearer token.

## v1 Requirements

### Auth

- [x] **AUTH-01**: Server reads `PLAUD_TOKEN` and `PLAUD_DEVICE_ID` from environment variables at startup
- [x] **AUTH-02**: Every API request includes required Plaud headers: `Authorization: bearer <token>`, `X-Device-Id`, `edit-from: desktop`, `app-platform: desktop`, `app-versionNumber`, `app-language`
- [x] **AUTH-03**: Server handles `-302` domain-redirect response by updating base URL and retrying the request
- [x] **AUTH-04**: Server surfaces clear auth error to MCP client when `-10000` status received (token invalid/expired)

### MCP Tools

- [ ] **TOOL-01**: `check_connection` — verifies token is valid and returns total file count
- [ ] **TOOL-02**: `get_file_count` — returns total number of recordings in the account
- [ ] **TOOL-03**: `get_recent_files(days)` — returns files created in the last N days
- [ ] **TOOL-04**: `get_files(start_date, end_date, limit)` — returns files with optional date range filter
- [ ] **TOOL-05**: `get_file(file_id)` — returns metadata for a specific recording
- [ ] **TOOL-06**: `get_transcript(file_id)` — returns full transcript with speaker labels from the recording's signed S3 content URL
- [ ] **TOOL-07**: `get_summary(file_id)` — returns AI-generated summary/notes from the recording's signed S3 content URL
- [ ] **TOOL-08**: `search_transcripts(query, days)` — searches transcript content across recent files client-side

### Container

- [ ] **CONT-01**: Runs as MCP server over `stdio` transport (primary — for Claude Code / Claude Desktop)
- [ ] **CONT-02**: Supports `streamable-http` transport for Kubernetes service exposure
- [ ] **CONT-03**: Single `Dockerfile` builds a self-contained image (Python + all deps, no external volumes needed)
- [ ] **CONT-04**: Kubernetes `Deployment` + `Service` YAML with token injected from a `Secret`
- [ ] **CONT-05**: Health/liveness probe endpoint available when running in HTTP mode

## v2 Requirements

### Auth improvements

- **AUTH-V2-01**: Token refresh flow — detect expiry and prompt re-injection without container restart
- **AUTH-V2-02**: Interactive OAuth setup endpoint — one-time login via `plaud://` callback to seed the token

### Additional tools

- **TOOL-V2-01**: `get_highlights(file_id)` — AI-generated highlights/bookmarks
- **TOOL-V2-02**: `list_folders` / `get_files_in_folder` — folder-level browsing
- **TOOL-V2-03**: `download_audio(file_id)` — download the original audio file

## Out of Scope

| Feature | Reason |
|---------|--------|
| CDP / Plaud Desktop dependency | Requires running Desktop app; unusable in containers |
| Official developer API | User has personal account only — no client credentials available |
| Audio recording or upload | Cloud read-only; no hardware integration needed |
| macOS / Windows deployment | Linux container target only |
| Token refresh automation | Manual re-injection is sufficient for v1; refresh adds complexity |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1: API Client | Complete |
| AUTH-02 | Phase 1: API Client | Complete |
| AUTH-03 | Phase 1: API Client | Complete |
| AUTH-04 | Phase 1: API Client | Complete |
| TOOL-01 | Phase 2: MCP Tools | Pending |
| TOOL-02 | Phase 2: MCP Tools | Pending |
| TOOL-03 | Phase 2: MCP Tools | Pending |
| TOOL-04 | Phase 2: MCP Tools | Pending |
| TOOL-05 | Phase 2: MCP Tools | Pending |
| TOOL-06 | Phase 2: MCP Tools | Pending |
| TOOL-07 | Phase 2: MCP Tools | Pending |
| TOOL-08 | Phase 2: MCP Tools | Pending |
| CONT-01 | Phase 3: Container & Kubernetes | Pending |
| CONT-02 | Phase 3: Container & Kubernetes | Pending |
| CONT-03 | Phase 3: Container & Kubernetes | Pending |
| CONT-04 | Phase 3: Container & Kubernetes | Pending |
| CONT-05 | Phase 3: Container & Kubernetes | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-08*
*Last updated: 2026-04-08 — traceability updated with phase names after roadmap creation*
