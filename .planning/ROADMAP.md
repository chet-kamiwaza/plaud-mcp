# Roadmap: Plaud MCP Server

## Milestones

- v1.0 MVP - Phases 1-4 (shipped)
- v1.1 Container Runtime Parity - Phases 5-7 (shipped)
- v1.2 Release Readiness - Phases 8-10 (shipped)
- v1.3 Code Scanning Fixes - Phase 11 (in progress)

<details>
<summary>v1.0 through v1.2 (Phases 1-10) - SHIPPED</summary>

Archived in `.planning/milestones/`. See milestone-specific roadmap and requirements files there.

</details>

## v1.3 Code Scanning Fixes (In Progress)

**Milestone Goal:** Resolve all 8 open GitHub code scanning alerts to bring the repo to a clean lint/analysis state.

## Phases

- [ ] **Phase 11: Fix Code Scanning Alerts** - Resolve all markdownlint, shellcheck, and PyLint alerts across 4 files

## Phase Details

### Phase 11: Fix Code Scanning Alerts
**Goal**: All GitHub code scanning alerts are resolved and the repo reports zero open alerts
**Depends on**: Phase 10 (v1.2 complete)
**Requirements**: MDLINT-01, SHELL-01, SHELL-02, SHELL-03, PYLINT-01
**Success Criteria** (what must be TRUE):
  1. docs/OPERATIONS.md passes markdownlint with no MD056 violations (table rows have correct cell count)
  2. scripts/container-runtime.sh, scripts/verify-local-mac.sh, and scripts/verify-container-runtime.sh pass shellcheck with no SC1007 warnings (no space after `=` in variable assignments)
  3. src/plaud_mcp/server.py passes PyLint with no E1101 error on the gzip.BadGzipFile reference
  4. GitHub code scanning shows zero open alerts for the repository
**Plans**: TBD

## Progress

**Execution Order:** Phase 11 only.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 11. Fix Code Scanning Alerts | v1.3 | 0/0 | Not started | - |
