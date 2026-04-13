# Requirements: Plaud MCP Server

**Defined:** 2026-04-13
**Core Value:** An MCP client can reliably query Plaud data through a self-hosted server using injected credentials, without depending on the Plaud desktop app at runtime.

## v1 Requirements

Requirements for the first tracked hardening milestone on top of the existing brownfield codebase.

### Security

- [ ] **SEC-01**: HTTP transport defaults do not expose the MCP server broadly on developer machines without an explicit opt-in
- [ ] **SEC-02**: Redirect validation and configuration object handling do not permit accidental token disclosure or overly broad trusted domains

### Operations

- [ ] **OPS-01**: Runtime failures in MCP tool execution are observable through structured logs or equivalent diagnosable signals
- [ ] **OPS-02**: Configuration loading does not require Plaud credentials at Python import time for code paths that do not need live API access

### Performance

- [ ] **PERF-01**: Transcript search completes with bounded concurrency and does not serialize every file fetch end-to-end
- [ ] **PERF-02**: Large folder and file listing flows avoid repeated full-library scans where short-lived reuse or explicit limits can reduce latency

### Reliability

- [ ] **REL-01**: Dependency and runtime selection are reproducible across local development, CI, and container deployment
- [ ] **REL-02**: High-risk helper paths and uncovered edge cases have automated test coverage

## v2 Requirements

### Future Enhancements

- **FUT-01**: Support alternative local container runtimes such as Podman
- **FUT-02**: Consider authenticated or multi-tenant HTTP transport if the project moves beyond single-user trusted networks

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native Plaud login inside the server | Plaud credentials are intentionally injected from outside the runtime |
| Persistent local cache or database | Current service value is a thin stateless bridge, not a stateful sync engine |
| Desktop or web frontend for browsing recordings | The product surface is MCP tools for AI clients |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| OPS-01 | Phase 2 | Pending |
| OPS-02 | Phase 2 | Pending |
| PERF-01 | Phase 3 | Pending |
| PERF-02 | Phase 3 | Pending |
| REL-01 | Phase 4 | Pending |
| REL-02 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initial definition*
