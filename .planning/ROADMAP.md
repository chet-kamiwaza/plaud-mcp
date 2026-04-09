# Roadmap: Plaud MCP Server

## Overview

Three phases deliver a working MCP server from nothing: first prove the API works (authenticated HTTP client against Plaud's cloud), then expose all data as MCP tools over stdio, then package and deploy to Kubernetes. Each phase delivers a completely verifiable capability before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: API Client** - Authenticated HTTP client that successfully talks to Plaud's cloud API (completed 2026-04-09)
- [ ] **Phase 2: MCP Tools** - All 8 tools exposed and functional over stdio transport
- [ ] **Phase 3: Container & Kubernetes** - Single Docker image deployable to Kubernetes

## Phase Details

### Phase 1: API Client
**Goal**: An authenticated Python HTTP client successfully retrieves data from Plaud's cloud API
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. Server starts without error when PLAUD_TOKEN and PLAUD_DEVICE_ID are set in environment
  2. A test call to the Plaud API returns data (not 401 or auth error) when using the full required header set
  3. A -302 redirect response causes the client to update its base URL and retry, returning data on the second attempt
  4. A -10000 response causes the server to surface a clear auth error message (not a raw exception)
**Plans:** 1/1 plans complete

Plans:
- [x] 01-01-PLAN.md — Project scaffold, PlaudClient implementation, and live API smoke test

### Phase 2: MCP Tools
**Goal**: All 8 Plaud data tools are callable via MCP stdio and return useful data
**Depends on**: Phase 1
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06, TOOL-07, TOOL-08
**Success Criteria** (what must be TRUE):
  1. Claude Code (or MCP inspector) can call check_connection and receive a valid file count
  2. get_recent_files, get_files, and get_file return structured recording metadata
  3. get_transcript returns a readable transcript with speaker labels for a given file_id
  4. get_summary returns the AI-generated summary text for a given file_id
  5. search_transcripts returns matching files when given a query term present in recent transcripts
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md — All 8 MCP tools (server scaffold, file listing, content retrieval, unit tests)

### Phase 3: Container & Kubernetes
**Goal**: The MCP server runs inside a Docker container and deploys to Kubernetes with token injected from a Secret
**Depends on**: Phase 2
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, CONT-05
**Success Criteria** (what must be TRUE):
  1. docker build produces an image and docker run --env PLAUD_TOKEN=... starts the server successfully
  2. The server accepts MCP requests over stdio when run via docker exec or as a Claude Code remote
  3. The server accepts MCP requests over HTTP/SSE transport when the container is started in HTTP mode
  4. kubectl apply of the provided manifests creates a running Pod with token from a Secret
  5. The health endpoint returns 200 OK and the liveness probe keeps the Pod alive under normal operation
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. API Client | 1/1 | Complete   | 2026-04-09 |
| 2. MCP Tools | 0/1 | Not started | - |
| 3. Container & Kubernetes | 0/TBD | Not started | - |
