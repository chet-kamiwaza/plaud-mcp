# Phase 8: Product Narrative and README Repair - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Derived from milestone definition, current README, runtime scripts, and live server code

<domain>
## Phase Boundary

Repair the public-facing narrative for Plaud MCP Server so the README explains the actual product instead of leading with fragmented runtime instructions. This phase is about documentation truthfulness and onboarding clarity, not adding new runtime features.

</domain>

<decisions>
## Implementation Decisions

### Narrative direction
- Lead with what the project is: a self-hosted MCP server that exposes Plaud recordings, transcripts, summaries, highlights, and folders to MCP clients.
- Explain the two real execution models separately: local Python `stdio` and HTTP via container/Kubernetes.
- Treat the README as the top-level product and onboarding document; move longer operational detail into a public doc if needed later in the milestone.

### Auth guidance
- Present the supported auth modes in the order a new user should evaluate them rather than in historical order.
- Keep the three existing auth paths because the code supports all three: browser-auth token file, auto-refresh with email/password, and manual token extraction.
- Recommend browser-auth or auto-refresh first, and label manual token extraction as legacy.

### Accuracy boundary
- Do not invent client-specific commands that have not been validated in this repo.
- Keep every runtime, transport, and auth statement aligned with the live code in `src/plaud_mcp` and the repo-owned runtime scripts.
- Preserve the validated Podman and Docker local flow, but stop letting it dominate the opening sections.

</decisions>

<canonical_refs>
## Canonical References

- `README.md` - current broken public narrative
- `src/plaud_mcp/server.py` - actual tool surface and health endpoint
- `src/plaud_mcp/__main__.py` - actual transport modes and HTTP binding behavior
- `src/plaud_mcp/config.py` - required environment variables and auth-source contract
- `scripts/container-runtime.sh` - canonical local container entrypoint
- `scripts/verify-local-mac.sh` - canonical local macOS validation flow
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`

</canonical_refs>

<specifics>
## Specific Ideas

- Use a compact capability table for transports, runtimes, and auth modes.
- Keep the tool list, but make it secondary to the value proposition and quick start.
- Add a short “choose your path” flow so a new user can decide between local Python and containers without reading the whole document first.

</specifics>

<deferred>
## Deferred Ideas

- Packaging metadata and release-facing repo assets (Phase 9)
- Final release-readiness checklist and milestone verification (Phase 10)

</deferred>

---

*Phase: 08-product-narrative-and-readme-repair*
*Context gathered: 2026-04-14 via derived planning context*
