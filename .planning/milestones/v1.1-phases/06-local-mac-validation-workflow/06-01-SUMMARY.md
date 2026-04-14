---
phase: 06-local-mac-validation-workflow
plan: 01
subsystem: testing
tags: [macos, podman, docker, validation, pytest, shell]
requires:
  - phase: 05-podman-runtime-compatibility
    provides: runtime helper and runtime verification script
provides:
  - Repo-owned macOS validation entrypoint for Podman and Docker Desktop
  - Structural regression tests for the local macOS validation contract
  - Runtime readiness enforcement for Podman machine and Docker daemon
affects: [phase-06-validation-evidence, phase-07-docs, local-validation]
tech-stack:
  added: [macos validation shell script, pytest coverage for local validation contract]
  patterns: [mac-only validation gate, runtime readiness checks, repo-owned verification entrypoint]
key-files:
  created:
    - scripts/verify-local-mac.sh
    - tests/test_local_mac_validation.py
  modified: []
key-decisions:
  - "Keep local Mac validation in one repo-owned script rather than spreading runtime and test commands across docs."
  - "Gate Podman validation on a running podman machine so macOS failures are explicit and actionable."
patterns-established:
  - "Local validation runs through scripts/verify-local-mac.sh before user-facing docs reference it."
  - "The macOS validation contract is regression-tested by reading the shell script as a repo artifact."
requirements-completed: [VAL-01]
duration: 10min
completed: 2026-04-14
---

# Phase 6: Local Mac Validation Workflow Summary

**Single-command macOS validation flow for Podman and Docker Desktop with structural regression coverage**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-14T08:48:00-04:00
- **Completed:** 2026-04-14T08:58:00-04:00
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `scripts/verify-local-mac.sh` as the repo-owned macOS validation entrypoint for `podman`, `docker`, or `all`.
- Enforced runtime readiness checks for Podman machine state and Docker daemon availability before container verification starts.
- Added `tests/test_local_mac_validation.py` so the Darwin gate, runtime selection, and helper reuse are covered by pytest.

## Task Commits

1. **Task 1: Add a macOS-local validation entrypoint for Podman and Docker** - `da62a0d` (`feat(validation): add mac local verification flow`)
2. **Task 2: Add regression coverage for the macOS validation contract** - `da62a0d` (`feat(validation): add mac local verification flow`)

**Plan metadata:** `590db59` (`docs(06): plan local mac validation workflow`)

## Files Created/Modified

- `scripts/verify-local-mac.sh` - Non-interactive macOS validation wrapper that checks runtime readiness, runs runtime verification, and executes pytest.
- `tests/test_local_mac_validation.py` - Structural coverage for the local Mac validation script contract.

## Decisions Made

- Run automated tests from the same validation entrypoint so runtime checks and repo test health are coupled.
- Keep platform enforcement explicit by failing fast outside macOS instead of letting runtime-specific commands fail later.

## Deviations from Plan

None - plan executed as intended.

## Issues Encountered

- Running Podman and Docker validation concurrently caused host port `8080` contention. The intended validation mode is sequential per runtime, and the repo-owned script works correctly in that mode.

## User Setup Required

- Keep Docker Desktop running before invoking `bash scripts/verify-local-mac.sh docker`.
- Keep `podman machine` running before invoking `bash scripts/verify-local-mac.sh podman`.

## Next Phase Readiness

- Phase 6 now has a stable entrypoint to use for actual validation evidence.
- Phase 7 can document `scripts/verify-local-mac.sh` as the canonical local Mac verification path after documentation work begins.

---
*Phase: 06-local-mac-validation-workflow*
*Completed: 2026-04-14*
