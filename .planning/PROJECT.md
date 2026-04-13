# Plaud MCP Server

## What This Is

Plaud MCP Server is a self-hosted MCP server that exposes a user's Plaud recordings, transcripts, summaries, highlights, and folder data to Claude and other MCP clients. It wraps Plaud's undocumented cloud API behind a small Python service that can run over stdio for local use or HTTP for container and Kubernetes deployments.

## Core Value

An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## Requirements

### Validated

- ✓ MCP clients can list Plaud recordings and fetch recording metadata through 11 exposed tools — existing
- ✓ MCP clients can retrieve transcripts, summaries, highlights, and folder-scoped recording views — existing
- ✓ The server runs as a single Python service over stdio or streamable HTTP with container and Kubernetes deployment paths — existing
- ✓ Authentication can be supplied by direct environment variables or a rotated token file — existing
- ✓ The codebase already has unit tests covering core client and tool flows — existing

### Active

- [ ] Harden HTTP transport defaults and credential-handling safety for self-hosted deployments
- [ ] Improve runtime observability and reduce fragile import-time configuration behavior
- [ ] Reduce latency and scaling risk in transcript search and large-library folder queries
- [ ] Make builds and verification more reproducible across local, CI, and container runtimes

### Out of Scope

- Native Plaud authentication or token issuance flow — the server depends on externally supplied Plaud credentials
- Persistent local database or caching layer — current architecture is intentionally stateless
- Desktop application UX — this project exposes an MCP server, not a GUI client

## Context

This is a brownfield Python project with an existing `.planning/codebase/` map that should remain the canonical snapshot of the current implementation. The Plaud API is undocumented and reverse engineered, so defensive handling around redirects, parsing, and deployment defaults matters more than broad feature expansion. Current gaps surfaced by the codebase map include HTTP transport exposure defaults, missing structured logging, import-time settings instantiation, lack of dependency locking, and a few targeted test coverage holes.

## Constraints

- **API**: `https://api.plaud.ai` is undocumented — behavior must be inferred from the live service and existing reverse-engineering work.
- **Auth**: `PLAUD_TOKEN` or `PLAUD_TOKEN_FILE` plus `PLAUD_DEVICE_ID` are required — no interactive login can happen inside the runtime.
- **Architecture**: Single-process, stateless Python service — avoid designs that require a database or sidecar.
- **Deployment**: Must keep working for local Docker, Claude stdio usage, and Kubernetes HTTP deployment paths.
- **Security**: Tokens must stay out of committed artifacts, image contents, and casual logging output.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Preserve the existing codebase map and bootstrap around it | Brownfield repo already has useful architecture analysis that downstream GSD commands should reuse | ✓ Good |
| Keep planning docs local-only via existing `commit_docs: false` config | The repo already ignores `.planning/`, and the current workflow is configured not to track planning artifacts in git | ✓ Good |
| Start with a coarse 4-phase roadmap focused on hardening and maintainability | The product already works; the next leverage is making it safer, more observable, and easier to evolve | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after initialization*
