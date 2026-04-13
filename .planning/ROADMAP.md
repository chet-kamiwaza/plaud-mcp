# Roadmap: Plaud MCP Server

## Overview

This brownfield roadmap starts from an already working Plaud MCP server and focuses the first milestone on hardening the service for safer self-hosting, easier diagnosis, better scalability, and more reproducible releases. The existing `.planning/codebase/` analysis remains the baseline for current-state understanding; these phases define what to improve next.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Security Hardening** - Tighten transport exposure and credential-safety defaults
- [ ] **Phase 2: Runtime Stability and Observability** - Make failures diagnosable and configuration loading less brittle
- [ ] **Phase 3: Performance and Scaling Guardrails** - Reduce latency and waste in search and folder/file traversal paths
- [ ] **Phase 4: Release Reproducibility and Test Confidence** - Align runtime versions, lock dependencies, and close risky coverage gaps

## Phase Details

### Phase 1: Security Hardening
**Goal**: Reduce the most immediate security and deployment-default risks in the current server.
**Depends on**: Nothing (first phase)
**Requirements**: SEC-01, SEC-02
**Success Criteria** (what must be TRUE):
  1. Local HTTP deployment defaults do not expose the server on untrusted interfaces unless explicitly configured
  2. Redirect validation only trusts `plaud.ai` and true subdomains, not suffix lookalikes
  3. Configuration and error paths avoid cleartext token leakage in common diagnostics
**Plans**: 2 plans

Plans:
- [ ] 01-01: Lock down transport and redirect validation behavior
- [ ] 01-02: Redact secrets safely in configuration and diagnostics paths

### Phase 2: Runtime Stability and Observability
**Goal**: Make the service easier to operate and safer to import, test, and extend.
**Depends on**: Phase 1
**Requirements**: OPS-01, OPS-02
**Success Criteria** (what must be TRUE):
  1. Tool failures produce enough structured signal to diagnose auth, API, and S3 retrieval issues
  2. Configuration can be loaded lazily for code paths and tests that do not require live credentials at import time
  3. Existing behavior for stdio and HTTP transports stays intact while internals become easier to maintain
**Plans**: 2 plans

Plans:
- [ ] 02-01: Introduce runtime diagnostics and error visibility
- [ ] 02-02: Refactor settings lifecycle away from import-time hard failure

### Phase 3: Performance and Scaling Guardrails
**Goal**: Improve responsiveness for large Plaud libraries without abandoning the current stateless design.
**Depends on**: Phase 2
**Requirements**: PERF-01, PERF-02
**Success Criteria** (what must be TRUE):
  1. Transcript search no longer performs fully serialized per-file fetches across the search window
  2. Folder/file listing avoids unnecessary repeated full-library scans where bounded reuse can help
  3. Performance limits and safeguards are documented in code and tests so regressions are visible
**Plans**: 2 plans

Plans:
- [ ] 03-01: Add bounded concurrency to transcript search and related fetch paths
- [ ] 03-02: Reduce repeated full-library work and document scaling limits

### Phase 4: Release Reproducibility and Test Confidence
**Goal**: Make builds deterministic and close high-risk gaps in automated verification.
**Depends on**: Phase 3
**Requirements**: REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. Local, CI, and container Python/runtime expectations align or are intentionally pinned with documentation
  2. Dependency installation is reproducible from a known-good locked or pinned state
  3. High-risk helpers and currently uncovered edge cases have automated tests guarding them
**Plans**: 2 plans

Plans:
- [ ] 04-01: Align runtime and dependency reproducibility
- [ ] 04-02: Close targeted testing gaps around helpers and edge cases

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Security Hardening | 0/2 | Not started | - |
| 2. Runtime Stability and Observability | 0/2 | Not started | - |
| 3. Performance and Scaling Guardrails | 0/2 | Not started | - |
| 4. Release Reproducibility and Test Confidence | 0/2 | Not started | - |

## Backlog

### Phase 999.1: add support for Podman containers (BACKLOG)

**Goal:** Captured for future planning
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd-review-backlog when ready)
