# Requirements: Plaud MCP Server

**Defined:** 2026-04-13
**Core Value:** An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## v1 Requirements

Requirements for milestone v1.1, focused on Podman support for local macOS workflows.

### Runtime Compatibility

- [x] **RT-01**: The project can be built and started locally on macOS using Podman in addition to Docker Desktop
- [x] **RT-02**: Container configuration, mounted data paths, and required environment variables behave correctly under both supported runtimes

### Local Validation

- [x] **VAL-01**: The repository defines a repeatable local verification flow for Podman that covers image build, service startup, and automated tests on a Mac laptop
- [x] **VAL-02**: Docker Desktop remains a documented and non-broken local verification path after Podman support is added

### Documentation

- [x] **DOC-01**: The README documents how to install and validate Podman on macOS for this project
- [x] **DOC-02**: The README documents runtime-specific commands, expected prerequisites, and troubleshooting for both Docker Desktop and Podman users

## v2 Requirements

### Future Enhancements

- **FUT-01**: Add CI coverage for Docker and Podman runtime matrices instead of relying only on local validation
- **FUT-02**: Add Linux-specific Podman guidance and production-grade Podman deployment patterns if the project starts targeting non-macOS Podman users

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replacing Docker Desktop entirely | Existing users and docs already depend on Docker, so this milestone adds parity rather than migration |
| Kubernetes or remote deployment redesign | The user asked for local Mac testing, not deployment-platform changes |
| Interactive secret provisioning inside containers | Current security model depends on externally supplied credentials and should remain that way |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RT-01 | Phase 5 | Complete |
| RT-02 | Phase 5 | Complete |
| VAL-01 | Phase 6 | Complete |
| VAL-02 | Phase 6 | Complete |
| DOC-01 | Phase 7 | Complete |
| DOC-02 | Phase 7 | Complete |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-14 after Phase 7 completion*
