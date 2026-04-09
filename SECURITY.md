# Security

> Threat register and audit trail for plaud-mcp v1.0.

> Milestone-wide security contract covering Phases 1–3. All 17 threats verified closed by automated audit on 2026-04-09.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| env → process | PLAUD_TOKEN and PLAUD_DEVICE_ID enter via shell env or K8s Secret at startup | Bearer token, device UUID |
| process → Plaud API | Authenticated outbound HTTP to api.plaud.ai | Bearer token in Authorization header |
| Plaud API → process | JSON response bodies parsed; -302 can mutate base_url | Redirect domain, file metadata, signed S3 URLs |
| MCP client → tool params | Tool caller supplies file_id, query, days, dates | User-controlled strings used in URL path construction |
| server.py → S3 | Unauthenticated fetch of signed S3 URLs from content_list | Gzip-compressed transcript/summary JSON |
| Host env → Container | PLAUD_TOKEN and PLAUD_DEVICE_ID injected at runtime | Secrets must not appear in image layers |
| MCP client → Container port 8080 | HTTP MCP transport; cluster-internal only | Tool requests/responses |
| Git → secret file | deploy/secret.yaml must never be committed with real values | Kubernetes Secret credentials |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Info Disclosure | config.py / settings | mitigate | Zero logging calls; token value never passed to any logger | closed |
| T-01-02 | Spoofing | -302 redirect in `_request()` | mitigate | `client.py:83-87` — domain must end with `plaud.ai` before base_url mutation | closed |
| T-01-03 | Tampering | base_url mutation on -302 | mitigate | `client.py:27,70-73,89,95` — `_redirect_attempted` flag initialized, set, and reset in finally | closed |
| T-01-04 | Info Disclosure | .env on disk | accept | See Accepted Risks Log | closed |
| T-01-05 | DoS | httpx timeout | mitigate | `client.py:31` — `httpx.Timeout(30.0)` on AsyncClient | closed |
| T-01-06 | EoP | Bearer token static secret | accept | See Accepted Risks Log | closed |
| T-01-07 | Repudiation | No request logging | accept | See Accepted Risks Log | closed |
| T-02-01 | Tampering | file_id URL construction | mitigate | `server.py:169-172,209-212,246-249` — empty/whitespace guard + `.strip()` before URL path | closed |
| T-02-02 | SSRF | `_fetch_s3_content` S3 URL | mitigate | `server.py:220,257,311` — data_link only sourced from `content_list[].data_link`; not MCP-exposed | closed |
| T-02-03 | Info Disclosure | Full transcript returned | accept | See Accepted Risks Log | closed |
| T-02-04 | DoS | `search_transcripts` | mitigate | `server.py:286-290` — `limit: 50`; `server.py:296-314` — `try/except` per file | closed |
| T-02-05 | Spoofing | `check_connection` auth state | accept | See Accepted Risks Log | closed |
| T-03-01 | Info Disclosure | Dockerfile image layers | mitigate | `Dockerfile:22` — only `ENV MCP_TRANSPORT=stdio`; no token ENV/ARG; `.dockerignore:14` excludes .env | closed |
| T-03-02 | EoP | Container runtime | mitigate | `Dockerfile:25-26` — `useradd --uid 1000` + `USER 1000`; `deployment.yaml:26-28` — `runAsNonRoot: true` | closed |
| T-03-03 | Info Disclosure | deploy/secret.yaml in git | mitigate | `deploy/secret.yaml` — placeholder values only; `.gitignore:31` — file listed | closed |
| T-03-04 | Spoofing | Kubernetes Service type | mitigate | `deploy/service.yaml:13` — `type: ClusterIP` | closed |
| T-03-05 | DoS | Container resources | mitigate | `deployment.yaml:43-57` — `limits.cpu: 500m`, `limits.memory: 256Mi`, livenessProbe `failureThreshold: 3` | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-04 | .env is development-time only. `.gitignore` excludes it. Production uses K8s Secret injection — no .env in container image. | chet-kamiwaza | 2026-04-09 |
| AR-02 | T-01-06 | Bearer token is a static secret with no interactive login flow to hijack. Personal-use tool with a single user's account. Token is rotated manually when expired. | chet-kamiwaza | 2026-04-09 |
| AR-03 | T-01-07 | No logging infrastructure in v1.0 scope. Structured request logging (method, path, status — never token) deferred to v1.1+. | chet-kamiwaza | 2026-04-09 |
| AR-04 | T-02-03 | Single-user, self-hosted tool. The token owner is the sole user; no multi-tenant access control needed. Full transcript/summary content is intentionally returned. | chet-kamiwaza | 2026-04-09 |
| AR-05 | T-02-05 | `PlaudAuthError` raised on -10000 propagates as tool error to MCP client. No auth state cached — `PlaudClient` is constructed per-call. | chet-kamiwaza | 2026-04-09 |

---

## Informational Notes (non-blocking, ASVS Level 1)

1. **T-01-01 forward risk** — `Settings` has no `__repr__` redaction. If logging is added in a future phase without redacting the settings object, `plaud_token` will appear in log output. Recommend adding `hide_input_in_errors: True` to `model_config` and a `__repr__` override before any logging infrastructure is introduced.

2. **T-02-02 SSRF depth** — `_fetch_s3_content` validates S3 URLs architecturally (data_link sourced from Plaud API only). No explicit domain allowlist check (e.g., `*.amazonaws.com`) exists in code. Sufficient for ASVS Level 1; would need an explicit URL prefix assertion at Level 2+.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-09 | 17 | 17 | 0 | gsd-security-auditor (claude-sonnet-4-6) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-09
