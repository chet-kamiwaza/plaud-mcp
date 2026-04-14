# Operations Guide

This guide is the public install, run, verify, and deploy reference for `plaud-mcp`.

## Runtime choices

Use the mode that matches how you want your MCP client to talk to the server:

| Mode | When to use it | Entry point |
|------|----------------|-------------|
| Local Python over `stdio` | Your MCP client can launch a command directly | `python -m plaud_mcp` |
| Local HTTP on macOS | You want a long-running local MCP endpoint | `bash scripts/container-runtime.sh <docker|podman> up` |
| Kubernetes HTTP deployment | You want a cluster-hosted MCP endpoint | `kubectl apply -f deploy/` |

## Prerequisites

- Python 3.10 or newer
- A Plaud account
- One of the supported auth setups:
  - browser-auth token file
  - Plaud email/password with auto-refresh
  - manual token extraction
- For local HTTP on macOS: Docker Desktop or Podman

## Auth setup

### Browser auth token file

Best for Google or Apple SSO accounts.

```bash
python scripts/setup-auth.py
```

Set these values in `.env` or your runtime environment:

- `PLAUD_TOKEN_FILE`
- `PLAUD_DEVICE_ID`

### Auto-refresh login

Best for Plaud accounts that use email and password directly.

Set:

- `PLAUD_AUTO_REFRESH=true`
- `PLAUD_EMAIL`
- `PLAUD_PASSWORD`
- `PLAUD_TOKEN_FILE`
- `PLAUD_DEVICE_ID`

The server refreshes the token before expiry and writes the current token to `PLAUD_TOKEN_FILE`.

### Manual token extraction

Legacy fallback for macOS desktop-app users.

```bash
python -m pip install cryptography
python scripts/get-token.py
```

Set:

- `PLAUD_TOKEN`
- `PLAUD_DEVICE_ID`

## Local Python over stdio

```bash
python -m pip install .
PLAUD_TOKEN=your_token PLAUD_DEVICE_ID=your_device_id python -m plaud_mcp
```

Behavior:

- `stdio` is the default transport.
- No container runtime is required.
- This is the simplest path when your MCP client can spawn the process directly.

## Local HTTP on macOS

### Docker Desktop

```bash
bash scripts/container-runtime.sh docker build
bash scripts/container-runtime.sh docker up
```

### Podman

```bash
brew install podman
podman machine init   # first run only
podman machine start
bash scripts/container-runtime.sh podman build
bash scripts/container-runtime.sh podman up
```

Both runtimes use the same compose file and `.env` contract. The server listens on:

```text
http://127.0.0.1:8080/mcp
```

Stop the local service with:

```bash
bash scripts/container-runtime.sh docker down
bash scripts/container-runtime.sh podman down
```

## Local verification

The macOS runtime verification entrypoint is:

```bash
bash scripts/verify-local-mac.sh docker
bash scripts/verify-local-mac.sh podman
```

What it checks:

- runtime readiness
- image build
- local service startup
- cleanup
- `pytest -q`

Run Docker and Podman verification sequentially on the same Mac because both use local port `8080`.

## Kubernetes deployment

The `deploy/` directory contains a cluster-internal HTTP deployment:

- `namespace.yaml`
- `deployment.yaml`
- `service.yaml`
- `secret.yaml` template

Typical flow:

```bash
kubectl apply -f deploy/namespace.yaml
kubectl apply -f deploy/secret.yaml
kubectl apply -f deploy/deployment.yaml
kubectl apply -f deploy/service.yaml
```

Important notes:

- Replace placeholder values in `deploy/secret.yaml` before applying it.
- Do not commit real secrets.
- The service is `ClusterIP` by default.
- The deployment expects `MCP_TRANSPORT=http`.

## Packaging and tests

Install the development extras:

```bash
python -m pip install .[dev]
```

Run the full test suite:

```bash
pytest -q
```

Build the package:

```bash
python -m build
```

## Troubleshooting

- Docker installed but commands fail: Docker Desktop is probably not fully ready yet.
- Podman installed but commands fail: `podman machine list` should show a running machine, and `podman info` should succeed.
- Port `8080` already in use: stop the existing listener before starting the local HTTP flow.
- Need a pure local process instead of HTTP: use the `stdio` path with `python -m plaud_mcp`.
