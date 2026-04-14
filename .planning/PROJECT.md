# Plaud MCP Server

## What This Is

Plaud MCP Server is a self-hosted MCP server that exposes a user's Plaud recordings, transcripts, summaries, highlights, and folder data to Claude and other MCP clients. It wraps Plaud's undocumented cloud API behind a small Python service that can run locally over `stdio`, as an HTTP service in containers, or in Kubernetes.

## Core Value

An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## Current Milestone: None Active

**Latest completed milestone:** v1.2 Release Readiness

**Latest outcome:**
- README rewritten around the actual product intent and supported usage modes
- Public `docs/OPERATIONS.md` and `docs/RELEASE-CHECKLIST.md` added
- Release-facing package metadata improved
- Package build plus Docker and Podman local verification commands revalidated successfully

## Requirements

### Validated

- ✓ MCP clients can list Plaud recordings and fetch recording metadata through 11 exposed tools — existing
- ✓ MCP clients can retrieve transcripts, summaries, highlights, and folder-scoped recording views — existing
- ✓ The server runs as a single Python service over stdio or streamable HTTP with container and Kubernetes deployment paths — existing
- ✓ Authentication can be supplied by direct environment variables or a rotated token file — existing
- ✓ The codebase already has unit tests covering core client and tool flows — existing
- ✓ Support Podman-based local container workflows on macOS without regressing Docker Desktop support — validated in Phases 5-6
- ✓ Provide a repeatable local validation path for build, startup, and test execution on a Mac laptop using Podman — validated in Phase 6
- ✓ Keep container auth, mounted state, and transport behavior consistent across supported runtimes — validated in Phase 5
- ✓ Document Podman installation, machine setup, and runtime-specific usage for local development — validated in Phase 7

### Active

- [x] The public docs explain the project intent, auth modes, transports, and tool surface without contradiction or misleading runtime guidance — validated in Phase 8
- [x] The repo’s release-facing files and metadata are coherent enough for public consumption and onboarding — validated in Phase 9
- [x] The documented setup and verification flows are validated against the actual code and repo commands before release — validated in Phase 10

### Out of Scope

- Broad deployment redesign beyond the current local/container/Kubernetes architecture — this milestone is about release readiness, not platform expansion
- New Plaud API features — the milestone is about making the current product understandable and shippable
- CI release automation beyond the current local verification checklist — deferred for future work

## Context

Current state: milestone v1.2 is complete. The README now reflects the real product, the repo has a public operations guide and release checklist, and the documented setup and verification paths were revalidated against the live repository. Podman and Docker local validation both pass on the target Mac, and package builds now complete cleanly with modernized metadata.

## Constraints

- **Platform**: Local validation must work on macOS — the primary target environment is the user's Mac laptop.
- **Runtimes**: Docker Desktop support must continue working while Podman is added — no breaking change to existing users.
- **Auth**: `PLAUD_TOKEN` or `PLAUD_TOKEN_FILE` plus `PLAUD_DEVICE_ID` remain required — runtime changes must not weaken secret handling.
- **Architecture**: Single-process, stateless Python service — runtime support should not introduce extra infrastructure.
- **Documentation**: Docs updates are part of done — setup and troubleshooting must be captured in-repo.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat Podman support as the next milestone instead of a backlog note | The user explicitly wants local Podman support now, and the repo already contains the Docker-based baseline to extend | ✓ Good |
| Scope this milestone to local macOS parity, not broad runtime redesign | The immediate value is reliable local build/run/test support on one laptop, not abstracting every possible container platform | ✓ Good |
| Keep Docker Desktop as a first-class supported path while adding Podman | Existing docs and users already assume Docker, so Podman must be additive rather than disruptive | ✓ Validated in Phases 5-6 |
| Treat the next milestone as release readiness instead of more runtime expansion | The immediate issue after v1.1 was public clarity and releasability, not more runtime capability | ✓ Validated in Phases 8-10 |
| Split public docs into a concise README plus a public operations guide | The README needed a stronger narrative, but detailed runtime and deployment guidance still needed a durable public home | ✓ Good |
| Include package build and both local runtime verification commands in release readiness | A release claim is weak unless the docs, packaging, and validated runtime commands are all rechecked together | ✓ Good |

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
*Last updated: 2026-04-14 after completing milestone v1.2 Release Readiness*
