# Plaud MCP Server

## What This Is

Plaud MCP Server is a self-hosted MCP server that exposes a user's Plaud recordings, transcripts, summaries, highlights, and folder data to Claude and other MCP clients. It wraps Plaud's undocumented cloud API behind a small Python service that can run locally or in containers, and this milestone expands the local container story beyond Docker Desktop to also support Podman on macOS.

## Core Value

An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## Current Milestone: v1.1 Podman Support

**Goal:** Add Podman support alongside Docker Desktop so the project can be built, run, and tested locally on a Mac with either runtime.

**Target features:**
- Podman-compatible local container workflow in addition to Docker Desktop
- Local macOS setup guidance that includes installing and validating Podman
- Local test and verification flow that runs against the Podman-based setup
- Updated docs covering the feature enhancement, setup, usage, and troubleshooting

## Requirements

### Validated

- ✓ MCP clients can list Plaud recordings and fetch recording metadata through 11 exposed tools — existing
- ✓ MCP clients can retrieve transcripts, summaries, highlights, and folder-scoped recording views — existing
- ✓ The server runs as a single Python service over stdio or streamable HTTP with container and Kubernetes deployment paths — existing
- ✓ Authentication can be supplied by direct environment variables or a rotated token file — existing
- ✓ The codebase already has unit tests covering core client and tool flows — existing

### Active

- [ ] Support Podman-based local container workflows on macOS without regressing Docker Desktop support
- [ ] Provide a repeatable local validation path for build, startup, and test execution on a Mac laptop using Podman
- [ ] Document Podman installation, machine setup, and runtime-specific usage for local development
- [ ] Keep container auth, mounted state, and transport behavior consistent across supported runtimes

### Out of Scope

- Kubernetes deployment changes unrelated to local runtime compatibility — this milestone is about local Mac workflows
- Linux-only Podman tuning or production Podman deployment guidance — not needed for the local support goal
- Replacing Docker Desktop as the primary documented runtime — the goal is dual support, not migration

## Context

The project already ships a Dockerfile, `docker-compose.yml`, and README workflows that assume Docker Desktop. Podman support is currently only tracked as a backlog item, but the immediate need is to make local macOS usage work with Podman as well, including a clear install path and local verification steps. Because this project handles sensitive Plaud credentials, any runtime changes must preserve the current discipline around injected secrets, mounted token state, and non-root container behavior.

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
| Keep Docker Desktop as a first-class supported path while adding Podman | Existing docs and users already assume Docker, so Podman must be additive rather than disruptive | — Pending |

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
*Last updated: 2026-04-13 after milestone v1.1 definition*
