# Phase 6: Local Mac Validation Workflow - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Derived from roadmap, requirements, Phase 5 summaries, and current repo state

<domain>
## Phase Boundary

Turn the Phase 5 runtime compatibility work into a repeatable macOS-local validation flow. This phase should define one repo-owned command path a Mac user can run to validate Podman locally, preserve Docker Desktop as a non-broken path, and capture execution evidence in planning artifacts without doing the public README rewrite reserved for Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Validation surface
- Build Phase 6 on top of `scripts/container-runtime.sh` and `scripts/verify-container-runtime.sh` rather than introducing a second independent runtime flow.
- Treat macOS validation as a runtime-preflight plus automated-test workflow: runtime readiness, container build/start checks, and pytest coverage should all be part of the repeatable command path.
- Keep the validation entrypoint non-interactive so it can be re-run whenever local runtime regressions are suspected.

### Podman scope
- Podman on macOS means a running `podman machine`, not only a binary on `PATH`.
- Podman validation should check machine readiness explicitly before attempting container startup so failures are actionable.
- The current Podman compose provider caveat is acceptable, but it must be recorded in phase-local validation evidence for later documentation.

### Docker regression scope
- Docker Desktop remains a first-class supported runtime and must keep passing the same repo-owned validation flow.
- Phase 6 should generate concrete regression evidence for Docker rather than assuming Docker still works because Phase 5 succeeded once.

### Documentation boundary
- End-user README and troubleshooting updates belong to Phase 7.
- Phase 6 may create phase-local validation evidence inside `.planning/phases/06-local-mac-validation-workflow/`, because that is implementation proof rather than user-facing documentation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Runtime foundation from Phase 5
- `scripts/container-runtime.sh` — canonical runtime wrapper for Docker Desktop and Podman
- `scripts/verify-container-runtime.sh` — current end-to-end runtime verification path
- `tests/test_runtime_scripts.py` — regression expectations for the runtime scripts
- `.planning/phases/05-podman-runtime-compatibility/05-01-SUMMARY.md` — runtime helper and compose decisions
- `.planning/phases/05-podman-runtime-compatibility/05-02-SUMMARY.md` — verification behavior and known Podman caveats

### Project scope and requirements
- `.planning/PROJECT.md` — milestone scope and local-mac constraint
- `.planning/REQUIREMENTS.md` — `VAL-01` and `VAL-02`
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, and plan split
- `.planning/STATE.md` — current phase status after Phase 5 completion

### Existing validation surface
- `README.md` — current Docker-oriented quick start and prerequisite wording
- `pyproject.toml` — existing pytest collection behavior
- `tests/` — current automated test suite already passing locally

</canonical_refs>

<specifics>
## Specific Ideas

- Prefer a single macOS validation script that can run `podman`, `docker`, or `all` so the same command surface covers both requirements.
- Record runtime versions, machine/daemon readiness, and command outcomes in a dedicated Phase 6 validation artifact rather than scattering evidence across ad hoc terminal output.
- Keep validation output secret-safe by reporting command results and runtime state without printing Plaud credentials or `.env` contents.

</specifics>

<deferred>
## Deferred Ideas

- Public README quick-start updates for Podman installation and dual-runtime usage (Phase 7)
- User-facing troubleshooting guidance and caveats for Podman compose on macOS (Phase 7)
- CI automation for runtime-matrix validation (future milestone work)

</deferred>

---

*Phase: 06-local-mac-validation-workflow*
*Context gathered: 2026-04-14 via derived planning context*
