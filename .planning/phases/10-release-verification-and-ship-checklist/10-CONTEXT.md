# Phase 10: Release Verification and Ship Checklist - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Derived from completed docs and repo-surface work plus current verification workflows

<domain>
## Phase Boundary

Verify that the release-facing docs, package metadata, and runtime guidance are credible against the actual repository. End the milestone with durable release-readiness evidence and a ship checklist.

</domain>

<decisions>
## Implementation Decisions

- Reuse the repo's normal verification commands wherever possible instead of inventing a separate release-only workflow.
- Validate both documentation and packaging surface, not just Python tests.
- Record what was verified and any remaining user-facing caveats in a durable artifact.

</decisions>

<canonical_refs>
## Canonical References

- `README.md`
- `docs/OPERATIONS.md`
- `pyproject.toml`
- `scripts/container-runtime.sh`
- `scripts/verify-local-mac.sh`
- `deploy/`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`

</canonical_refs>

<specifics>
## Specific Ideas

- Run `pytest -q`
- Run targeted command-level sanity checks for the local runtime scripts
- Build the package with `python -m build`
- Write a release-readiness checklist future maintainers can reuse

</specifics>

---

*Phase: 10-release-verification-and-ship-checklist*
*Context gathered: 2026-04-14 via derived planning context*
