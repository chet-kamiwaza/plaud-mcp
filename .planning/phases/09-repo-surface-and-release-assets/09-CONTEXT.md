# Phase 9: Repo Surface and Release Assets - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Derived from updated README, package metadata, deploy assets, and public release goals

<domain>
## Phase Boundary

Make the public repo surface coherent for release. This phase is about the files a new user, packager, or reviewer sees first: packaging metadata, release-facing docs, and public onboarding assets that stand on their own without `.planning`.

</domain>

<decisions>
## Implementation Decisions

### Repo surface direction
- Keep the README as the landing page, but move deeper operational details into a public `docs/` file instead of relying on planning artifacts.
- Improve Python package metadata so builds and package consumers see a useful description, README, URLs, and classifiers.
- Add light regression coverage for release assets where it meaningfully protects the new public surface.

### Scope guardrails
- Do not redesign deployment architecture in this phase.
- Do not add broad contributor-process docs unless they materially help releasability.
- Keep release-facing assets tightly aligned with the code and validated runtime behavior.

</decisions>

<canonical_refs>
## Canonical References

- `README.md`
- `pyproject.toml`
- `deploy/`
- `scripts/container-runtime.sh`
- `scripts/verify-local-mac.sh`
- `src/plaud_mcp/__main__.py`
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`

</canonical_refs>

<specifics>
## Specific Ideas

- Add a public operations guide that covers install, run, verify, and deploy at a practical level.
- Add `build` to dev tooling so release packaging can be checked in the next phase without ad hoc environment changes.
- Add a small metadata/doc consistency test so public-facing regressions are caught by `pytest`.

</specifics>

<deferred>
## Deferred Ideas

- Release-readiness validation record and ship checklist (Phase 10)
- CI expansion for packaging and docs checks (future milestone)

</deferred>

---

*Phase: 09-repo-surface-and-release-assets*
*Context gathered: 2026-04-14 via derived planning context*
