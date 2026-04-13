# Roadmap: Plaud MCP Server

## v1.1 Podman Support

## Overview

This milestone advances the existing containerized Plaud MCP server by adding Podman support alongside Docker Desktop for local macOS development. The focus is practical local parity: make the repo runnable and testable on a Mac laptop with Podman, preserve the existing Docker workflow, and update documentation so the new runtime path is explicit and supportable.

## Phases

**Phase Numbering:**
- Integer phases (5, 6, 7): Planned milestone work
- Decimal phases (5.1, 5.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 5: Podman Runtime Compatibility** - Make the local container workflow work under Podman without breaking Docker Desktop
- [ ] **Phase 6: Local Mac Validation Workflow** - Define and verify the Podman-based local build, startup, and test path on macOS
- [ ] **Phase 7: Documentation and Rollout Guidance** - Update README and related docs for installation, usage, and troubleshooting across both runtimes

## Phase Details

### Phase 5: Podman Runtime Compatibility
**Goal**: Adapt the current Docker-oriented local workflow so the service can run cleanly under Podman on macOS.
**Depends on**: Nothing (first phase of milestone)
**Requirements**: RT-01, RT-02
**Success Criteria** (what must be TRUE):
  1. The image builds and the service starts locally with Podman on macOS using repo-defined commands or scripts
  2. Required environment variables, mounted token storage, and exposed ports behave correctly under Podman
  3. Existing Docker Desktop usage remains intact or is intentionally adjusted with clear compatibility handling
**Plans**: 2 plans

Plans:
- [ ] 05-01: Audit and update runtime-specific container configuration for Podman compatibility
- [ ] 05-02: Add any repo-level command, script, or config changes needed to support both Docker Desktop and Podman locally

### Phase 6: Local Mac Validation Workflow
**Goal**: Prove the project can be verified locally on a Mac laptop through a repeatable Podman workflow.
**Depends on**: Phase 5
**Requirements**: VAL-01, VAL-02
**Success Criteria** (what must be TRUE):
  1. Podman installation and local machine prerequisites for macOS are defined and verifiable
  2. A local verification workflow covers image build, service startup, and automated tests under Podman
  3. Docker Desktop verification still works and any runtime differences are explicitly accounted for
**Plans**: 2 plans

Plans:
- [ ] 06-01: Establish the local Podman setup and verification commands for macOS
- [ ] 06-02: Run and document local regression checks for both supported runtimes where feasible

### Phase 7: Documentation and Rollout Guidance
**Goal**: Make the new runtime support usable by documenting setup, commands, and troubleshooting in the repo.
**Depends on**: Phase 6
**Requirements**: DOC-01, DOC-02
**Success Criteria** (what must be TRUE):
  1. The README explains Podman installation and setup for local macOS usage in this repo
  2. Runtime-specific examples and prerequisites are clear for Docker Desktop and Podman users
  3. Feature enhancement notes and troubleshooting guidance reflect the final implemented workflow
**Plans**: 2 plans

Plans:
- [ ] 07-01: Update README quick-start and prerequisites for dual-runtime support
- [ ] 07-02: Add troubleshooting and feature-enhancement notes covering Podman usage on macOS

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Podman Runtime Compatibility | 0/2 | Not started | - |
| 6. Local Mac Validation Workflow | 0/2 | Not started | - |
| 7. Documentation and Rollout Guidance | 0/2 | Not started | - |
