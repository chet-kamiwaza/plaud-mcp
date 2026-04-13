# Phase 5: Podman Runtime Compatibility - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Source:** Derived from milestone definition, roadmap, requirements, and current repo state

<domain>
## Phase Boundary

Add Podman-compatible local container support for macOS without regressing the existing Docker Desktop workflow. This phase should make the repo's runtime entrypoints and container configuration work under Podman, while preserving the existing environment contract, mounted token storage behavior, and local-only HTTP exposure expectations.

</domain>

<decisions>
## Implementation Decisions

### Runtime scope
- Support Podman as an additive local runtime on macOS; Docker Desktop remains supported and is not being replaced.
- Treat Podman on macOS as a `podman machine` workflow, not a Linux-host assumption.
- Encapsulate runtime differences in repo-owned scripts or commands instead of maintaining two diverging container definitions if one shared definition can work.

### Configuration invariants
- Preserve the current environment contract: `PLAUD_TOKEN`, `PLAUD_TOKEN_FILE`, `PLAUD_DEVICE_ID`, `PLAUD_EMAIL`, `PLAUD_PASSWORD`, `PLAUD_AUTO_REFRESH`, and `MCP_TRANSPORT` keep their existing meanings.
- Preserve mounted writable state under `/app/data` so token-file auth and auto-refresh continue to work.
- Keep the local HTTP workflow loopback-scoped where possible for developer-machine safety.

### Verification boundary
- Phase 5 focuses on runtime compatibility and executable runtime helpers, not full documentation polish.
- Small self-describing command help text or inline script usage is acceptable, but the README overhaul belongs to Phase 7.

### Human setup assumptions
- Local Podman support assumes Podman is installed on the Mac and a Podman machine can be initialized and started.
- Human-required setup can be listed in plan `user_setup`, but the implementation should automate as much of the runtime selection and validation path as possible.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current runtime surface
- `docker-compose.yml` — current local container entrypoint and runtime env/volume mapping
- `Dockerfile` — image build, runtime user, and `/app/data` expectations
- `.env.example` — supported local auth modes and env contract
- `src/plaud_mcp/__main__.py` — HTTP transport host/port behavior when running in-container

### Existing project scope
- `.planning/PROJECT.md` — milestone goals, constraints, and active scope
- `.planning/REQUIREMENTS.md` — `RT-01` and `RT-02` requirements
- `.planning/ROADMAP.md` — phase goal, success criteria, and plan split

### Supporting codebase context
- `.planning/codebase/ARCHITECTURE.md` — current container/runtime architecture
- `.planning/codebase/STACK.md` — runtime and tooling baseline
- `.planning/codebase/TESTING.md` — current test patterns and commands

</canonical_refs>

<specifics>
## Specific Ideas

- Prefer a runtime wrapper script that accepts `docker` and `podman` explicitly, and defaults sensibly when only one runtime is available.
- Keep local runtime commands non-interactive where possible so they can be reused in later validation steps.
- If Compose behavior differs between Docker Desktop and Podman, make that difference explicit in the repo-owned command layer instead of hiding it in docs alone.

</specifics>

<deferred>
## Deferred Ideas

- README quick-start rewrite and Podman troubleshooting details (Phase 7)
- End-to-end local regression runbook for both runtimes (Phase 6)
- CI runtime-matrix validation for Docker and Podman (future milestone work)

</deferred>

---

*Phase: 05-podman-runtime-compatibility*
*Context gathered: 2026-04-13 via derived planning context*

