# Roadmap: Plaud MCP Server

## v1.2 Release Readiness

## Overview

This milestone focuses on making Plaud MCP Server release-ready as a public repo. The priority is not adding more runtime features, but making sure the docs accurately describe the product, the public repo surface is coherent, and the documented setup and verification flows match the actual code and validated commands.

## Phases

**Phase Numbering:**
- Integer phases (8, 9, 10): Planned milestone work
- Decimal phases (8.1, 8.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 8: Product Narrative and README Repair** - Rewrite the docs so they reflect the real project intent, usage modes, and supported workflows
- [ ] **Phase 9: Repo Surface and Release Assets** - Tighten the repo’s public-facing files and release-oriented onboarding surface
- [ ] **Phase 10: Release Verification and Ship Checklist** - Validate the documented flows and record a release-readiness result

## Phase Details

### Phase 8: Product Narrative and README Repair
**Goal**: Make the primary docs accurately describe what Plaud MCP Server is, how it works, and how someone is supposed to use it.
**Depends on**: Nothing (first phase of milestone)
**Requirements**: DOCS-01, DOCS-02
**Success Criteria** (what must be TRUE):
  1. The README explains the real product intent and supported usage modes without contradiction
  2. Auth modes, transports, and runtime workflows are documented in language that matches the actual code paths
  3. The README becomes a credible onboarding document instead of a confusing mix of partial workflows
**Plans**: 2 plans

Plans:
- [ ] 08-01: Audit and rewrite the README around the real product intent and user flows
- [ ] 08-02: Align README setup, auth, transport, and runtime guidance with the validated code paths

### Phase 9: Repo Surface and Release Assets
**Goal**: Make the repository itself look intentional and release-ready for someone encountering it fresh.
**Depends on**: Phase 8
**Requirements**: REPO-01, REPO-02
**Success Criteria** (what must be TRUE):
  1. Release-facing repo files and metadata are coherent and helpful for public consumption
  2. The repo includes a maintainable public usage surface that does not depend on internal `.planning` artifacts
  3. Any supporting release assets needed for onboarding or packaging are updated consistently
**Plans**: 2 plans

Plans:
- [ ] 09-01: Audit and improve release-facing repo files and metadata
- [ ] 09-02: Add or refine public onboarding assets needed for releasability

### Phase 10: Release Verification and Ship Checklist
**Goal**: Verify the repo is genuinely releasable by checking the documented flows against the actual code and recording the result.
**Depends on**: Phase 9
**Requirements**: REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. Documented install, run, and verification commands are checked against the repo
  2. The milestone ends with a release-readiness record that captures what was validated and what caveats remain
  3. The repo has a clear ship checklist or equivalent release verification artifact for future use
**Plans**: 2 plans

Plans:
- [ ] 10-01: Run and capture release-oriented validation for the documented flows
- [ ] 10-02: Produce the release-readiness checklist and final milestone verification record

## Progress

**Execution Order:**
Phases execute in numeric order: 8 -> 9 -> 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. Product Narrative and README Repair | 0/2 | Not started | - |
| 9. Repo Surface and Release Assets | 0/2 | Not started | - |
| 10. Release Verification and Ship Checklist | 0/2 | Not started | - |
