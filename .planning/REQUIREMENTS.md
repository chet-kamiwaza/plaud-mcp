# Requirements: Plaud MCP Server

**Defined:** 2026-04-14
**Core Value:** An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## v1.3 Requirements

Requirements for milestone v1.3 Code Scanning Fixes. Each maps to roadmap phases.

### Markdown Lint

- [ ] **MDLINT-01**: docs/OPERATIONS.md markdown table has correct cell count per row (alert #772, MD056)

### Shell Script Lint

- [ ] **SHELL-01**: scripts/container-runtime.sh variable assignments use correct syntax with no space after `=` (alerts #770-771, SC1007)
- [ ] **SHELL-02**: scripts/verify-local-mac.sh variable assignments use correct syntax with no space after `=` (alerts #768-769, SC1007)
- [ ] **SHELL-03**: scripts/verify-container-runtime.sh variable assignments use correct syntax with no space after `=` (alerts #766-767, SC1007)

### Python Lint

- [ ] **PYLINT-01**: src/plaud_mcp/server.py gzip.BadGzipFile reference resolves without PyLint E1101 error (alert #765)

## Future Requirements

None — this is a targeted fix milestone.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dismissed alerts | Already triaged and accepted — not reopening |
| New linting rules or tooling | Fix existing alerts only, no new static analysis |
| Code refactoring beyond alert fixes | Minimal changes to resolve each alert |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MDLINT-01 | Phase 11 | Pending |
| SHELL-01 | Phase 11 | Pending |
| SHELL-02 | Phase 11 | Pending |
| SHELL-03 | Phase 11 | Pending |
| PYLINT-01 | Phase 11 | Pending |

**Coverage:**
- v1.3 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0

---
*Requirements defined: 2026-04-14*
*Last updated: 2026-04-14 after roadmap creation*
