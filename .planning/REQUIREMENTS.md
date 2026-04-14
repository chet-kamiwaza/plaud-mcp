# Requirements: Plaud MCP Server

**Defined:** 2026-04-14
**Core Value:** An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## v1 Requirements

Requirements for milestone v1.2, focused on release readiness and documentation correctness.

### Documentation Clarity

- [ ] **DOCS-01**: The README clearly explains what the project does, who it is for, and the main supported usage modes
- [ ] **DOCS-02**: The README documents auth modes, transports, and runtime workflows in a way that matches the actual code and validated commands

### Repo Surface

- [ ] **REPO-01**: Release-facing repo files and metadata are coherent enough for public consumption and onboarding
- [ ] **REPO-02**: The repository includes a maintainable release-oriented overview of how to install, run, and verify the project without relying on internal planning artifacts

### Release Verification

- [ ] **REL-01**: The documented setup and verification flows are checked against the actual repo commands before release
- [ ] **REL-02**: The milestone produces a clear release-readiness record identifying what was validated and any remaining public caveats

## v2 Requirements

### Future Enhancements

- **FUT-01**: Add CI-based release checks for docs, packaging, and runtime smoke tests
- **FUT-02**: Add richer public documentation beyond the README, such as architecture and deployment guides

## Out of Scope

| Feature | Reason |
|---------|--------|
| New Plaud API capabilities | This milestone is about making the current product releasable, not adding new end-user features |
| Broad deployment redesign | Release readiness should reflect the current architecture rather than expanding scope into new deployment models |
| Linux/Windows runtime parity work | The immediate problem is public correctness and release quality, not platform expansion |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOCS-01 | Phase 8 | Pending |
| DOCS-02 | Phase 8 | Pending |
| REPO-01 | Phase 9 | Pending |
| REPO-02 | Phase 9 | Pending |
| REL-01 | Phase 10 | Pending |
| REL-02 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0

---
*Requirements defined: 2026-04-14*
*Last updated: 2026-04-14 after milestone v1.2 definition*
