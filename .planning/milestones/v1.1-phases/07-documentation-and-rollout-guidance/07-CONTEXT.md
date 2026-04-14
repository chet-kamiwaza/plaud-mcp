# Phase 7: Documentation and Rollout Guidance - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Derived from roadmap, requirements, current README, and Phase 5-6 execution artifacts

<domain>
## Phase Boundary

Convert the validated dual-runtime implementation into user-facing documentation. This phase should update the repo docs so a macOS user can install Podman, choose Docker Desktop or Podman intentionally, run the correct repo-owned commands, and troubleshoot the known runtime differences without needing to reverse-engineer the Phase 5 and 6 planning artifacts.

</domain>

<decisions>
## Implementation Decisions

### Documentation surface
- The public README is the primary deliverable for this phase because the roadmap requirements explicitly target README coverage.
- Phase 7 should document the repo-owned command surface (`scripts/container-runtime.sh` and `scripts/verify-local-mac.sh`) rather than reintroducing raw `docker compose`-only examples as the default path.
- User-facing docs should stay concise and operational; planning evidence remains in `.planning` and should only inform the README wording.

### Runtime guidance
- Podman support on macOS must be documented as a `podman machine` workflow, not as a generic Linux-host Podman setup.
- Docker Desktop remains supported and should stay visible in the docs as a first-class option, not only as a fallback.
- The external compose-provider caveat and sequential `8080` validation expectation should be documented as troubleshooting guidance because both were observed during validated local runs.

### Scope boundaries
- This phase is documentation-only; no runtime behavior changes are required unless a doc example is provably wrong and cannot be documented accurately without a small supporting adjustment.
- Keep public guidance secret-safe: explain required variables and auth modes without exposing any real credentials or `.env` contents beyond the example contract already in the repo.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Validated runtime and validation artifacts
- `scripts/container-runtime.sh` — canonical runtime wrapper for Docker Desktop and Podman commands
- `scripts/verify-container-runtime.sh` — lower-level runtime verification path
- `scripts/verify-local-mac.sh` — validated macOS-local verification entrypoint
- `.planning/phases/05-podman-runtime-compatibility/05-01-SUMMARY.md` — runtime helper and compose decisions
- `.planning/phases/05-podman-runtime-compatibility/05-02-SUMMARY.md` — runtime verification behavior and caveats
- `.planning/phases/06-local-mac-validation-workflow/06-VALIDATION.md` — exact validated Podman and Docker results on the target Mac
- `.planning/phases/06-local-mac-validation-workflow/06-VERIFICATION.md` — confirms Phase 6 passed and captures the final runtime truths

### Current documentation and config surface
- `README.md` — current public setup and usage docs
- `.env.example` — supported auth contract and runtime command comments
- `docker-compose.yml` — loopback binding, mounted token path, and HTTP transport defaults

### Milestone scope
- `.planning/PROJECT.md` — current milestone state and active remaining requirement
- `.planning/REQUIREMENTS.md` — `DOC-01` and `DOC-02`
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, and plan split
- `.planning/STATE.md` — current next-phase status

</canonical_refs>

<specifics>
## Specific Ideas

- Replace Docker-only quick-start examples with runtime-neutral setup that explicitly shows Docker Desktop and Podman command variants.
- Add a concise Podman-on-macOS install/setup section that includes installation, `podman machine` readiness, and the validated local verification command.
- Include a troubleshooting section that covers port `8080` conflicts, Podman machine readiness, Docker daemon readiness, and the external compose-provider note observed in validation.

</specifics>

<deferred>
## Deferred Ideas

- CI/runtime-matrix documentation for future automated validation work
- Linux-specific Podman guidance beyond the validated macOS target
- Broader deployment-platform documentation outside the local Mac workflow

</deferred>

---

*Phase: 07-documentation-and-rollout-guidance*
*Context gathered: 2026-04-14 via derived planning context*
