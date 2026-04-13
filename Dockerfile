# syntax=docker/dockerfile:1
# Plaud MCP Server
# Single-stage build - python:3.14-slim base.
#
# Security:
#   T-03-01: PLAUD_TOKEN / PLAUD_DEVICE_ID / PLAUD_PASSWORD are NEVER baked in.
#            They must be injected at runtime via env or K8s Secret.
#   T-03-02: Container runs as non-root UID 1000.

FROM python:3.14-slim

WORKDIR /app

# Copy source and install.
COPY pyproject.toml ./
COPY src/ src/
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

# Default transport: stdio (for Claude Code / Claude Desktop).
# Override at runtime with: -e MCP_TRANSPORT=http
ENV MCP_TRANSPORT=stdio

# Writable directory for the persisted token (used when PLAUD_AUTO_REFRESH=true
# or when a mounted PLAUD_TOKEN_FILE points here). Owned by the non-root user
# so the auto-refresh flow can write a fresh token.
RUN mkdir -p /app/data && chown 1000:1000 /app/data
VOLUME /app/data

# Run as non-root (UID 1000). No home directory needed.
RUN useradd --uid 1000 --no-create-home --shell /bin/false plaud
USER 1000

# Port 8080 is only meaningful when MCP_TRANSPORT=http.
EXPOSE 8080

CMD ["python", "-m", "plaud_mcp"]
