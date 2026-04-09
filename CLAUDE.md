<!-- GSD:project-start source:PROJECT.md -->
## Project

**Plaud MCP Server**

A containerized MCP (Model Context Protocol) server that exposes Plaud cloud API data as tools for AI assistants. Deployed as a single Docker container on Kubernetes, it gives Claude and other MCP clients access to a user's Plaud recordings, transcripts, and AI summaries — with no Desktop app dependency.

**Core Value:** An MCP client can query a user's Plaud recordings, transcripts, and summaries via a self-hosted container using only an injected bearer token.

### Constraints

- **API**: `https://api.plaud.ai` — no public docs; all knowledge from reverse engineering
- **Auth**: Bearer token + device UUID must be injected; no interactive login flow in container
- **Stack**: Python (matches reference impl, `mcp` SDK has excellent Python support)
- **Container**: Single image, no sidecar, no external state store
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
