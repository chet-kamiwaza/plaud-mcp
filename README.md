# plaud-mcp

`plaud-mcp` is a self-hosted [MCP](https://modelcontextprotocol.io) server for Plaud. It lets an MCP client query your Plaud recordings, transcripts, summaries, highlights, and folders without depending on the Plaud desktop app at runtime.

This repo is for people who want their own Plaud data available inside Claude Code, Claude Desktop, or another MCP-compatible client through either:

- a local Python process over `stdio`
- an HTTP service running locally in Docker Desktop or Podman
- an HTTP deployment using the included Kubernetes manifests

## What it exposes

Once connected, the server provides 11 tools:

| Tool | Purpose |
|------|---------|
| `check_connection` | Verify auth and return account metadata |
| `get_file_count` | Count all recordings |
| `get_recent_files` | List recent recordings by day range |
| `get_files` | List recordings with optional date filters |
| `get_file` | Fetch metadata for a specific recording |
| `get_transcript` | Return the transcript for a recording |
| `get_summary` | Return the AI-generated summary |
| `get_highlights` | Return highlights for a recording |
| `list_folders` | List Plaud folders |
| `get_folder_files` | List recordings in a folder |
| `search_transcripts` | Search transcript text across recent recordings |

## Supported modes

| Area | Supported paths |
|------|-----------------|
| Transport | `stdio` and HTTP |
| Local container runtimes on macOS | Docker Desktop and Podman |
| Auth sources | `PLAUD_TOKEN`, `PLAUD_TOKEN_FILE`, or `PLAUD_AUTO_REFRESH=true` with email/password |

Runtime selection does not change the Plaud auth contract. The same environment variables drive local Python, Docker, Podman, and Kubernetes flows.

## Choose your path

Use `stdio` if you want the simplest local setup and your MCP client can launch a command directly.

Use HTTP if you want a long-running local service on `http://127.0.0.1:8080/mcp`, or if you plan to run the server in a container or Kubernetes.

## Quick start

### 1. Clone and configure auth

```bash
git clone https://github.com/chet-kamiwaza/plaud-mcp
cd plaud-mcp
cp .env.example .env
```

Pick one auth mode:

| Auth mode | Use this when | What to set |
|-----------|---------------|-------------|
| Browser auth token file | You sign in with Google or Apple SSO | Run `python scripts/setup-auth.py`, then set `PLAUD_TOKEN_FILE` and `PLAUD_DEVICE_ID` |
| Auto-refresh login | You sign in to Plaud with email/password | Set `PLAUD_AUTO_REFRESH=true`, `PLAUD_EMAIL`, `PLAUD_PASSWORD`, `PLAUD_TOKEN_FILE`, and `PLAUD_DEVICE_ID` |
| Manual token extraction | You need the legacy desktop-token path | Set `PLAUD_TOKEN` and `PLAUD_DEVICE_ID` after running `python scripts/get-token.py` |

Recommended order:

- Use browser auth for Google or Apple SSO accounts.
- Use auto-refresh for Plaud email/password accounts.
- Use manual token extraction only if the other two do not fit your setup.

### 2. Run the server

#### Option A: local Python over `stdio`

```bash
python -m pip install .
PLAUD_TOKEN=your_token PLAUD_DEVICE_ID=your_device_id python -m plaud_mcp
```

`stdio` is the default transport. Configure your MCP client to launch that command directly.

#### Option B: local HTTP with Docker Desktop or Podman on macOS

Docker Desktop:

```bash
bash scripts/container-runtime.sh docker up
```

Podman on macOS:

```bash
brew install podman
podman machine init   # first run only
podman machine start
bash scripts/container-runtime.sh podman up
```

Then connect your MCP client to:

```text
http://127.0.0.1:8080/mcp
```

Claude Code example:

```bash
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

### 3. Verify the local runtime

The repo-owned validation entrypoint for macOS is:

```bash
bash scripts/verify-local-mac.sh docker
bash scripts/verify-local-mac.sh podman
```

Run Podman and Docker checks sequentially on the same machine. Both local HTTP paths use loopback port `8080`.

## Auth details

### Browser auth token file

This is the best fit for Google and Apple SSO accounts. The script opens the browser flow used by the Plaud desktop app and writes a long-lived token to a file.

```bash
python scripts/setup-auth.py
```

After it writes the token:

- set `PLAUD_TOKEN_FILE` to that file path
- set `PLAUD_DEVICE_ID` to the device UUID printed by the script

### Auto-refresh login

If your Plaud account uses email and password, the server can refresh the token automatically before it expires.

Required variables:

- `PLAUD_AUTO_REFRESH=true`
- `PLAUD_EMAIL`
- `PLAUD_PASSWORD`
- `PLAUD_TOKEN_FILE`
- `PLAUD_DEVICE_ID`

### Manual token extraction

This is the legacy macOS desktop-app path:

```bash
python -m pip install cryptography
python scripts/get-token.py
```

Use the printed values for `PLAUD_TOKEN` and `PLAUD_DEVICE_ID`.

## Local runtime commands

Use the runtime helper for local container actions:

```bash
bash scripts/container-runtime.sh docker build
bash scripts/container-runtime.sh docker up
bash scripts/container-runtime.sh docker down

bash scripts/container-runtime.sh podman build
bash scripts/container-runtime.sh podman up
bash scripts/container-runtime.sh podman down
```

The helper keeps Docker Desktop and Podman on the same compose file and environment contract. The local HTTP service binds to `127.0.0.1:8080`.

## Deployment

For HTTP deployments outside local development, use the manifests in [`deploy/`](deploy). The server exposes:

- `/mcp` for the MCP HTTP transport
- `/health` for liveness and readiness checks

The Kubernetes manifests assume credentials are injected at runtime and keep the service cluster-internal by default.

## Verification and operations

Release-facing operational details live in [docs/OPERATIONS.md](docs/OPERATIONS.md). That document covers:

- local install, run, and verify flows
- Docker Desktop and Podman behavior on macOS
- `stdio` versus HTTP usage
- Kubernetes deployment notes
- troubleshooting for the validated local runtime paths

## Example prompts

Once connected, ask your MCP client things like:

- "Show me my last 5 recordings"
- "Get the transcript from my meeting yesterday"
- "Search my recordings for anything about budget planning"
- "Summarize the recording from April 8"
- "List my Plaud folders"

## Troubleshooting

- Port `8080` already in use: stop the existing listener before running either local HTTP workflow or verification script.
- Podman installed but startup fails: confirm `podman machine list` shows a running machine and `podman info` succeeds.
- Docker installed but commands fail: Docker Desktop is probably not fully booted yet.
- Need deeper runtime guidance: use [docs/OPERATIONS.md](docs/OPERATIONS.md).

## Security notes

- The server does not bake Plaud credentials into the image.
- For container and Kubernetes usage, inject credentials at runtime.
- See [SECURITY.md](SECURITY.md) for the current threat register and audit trail.
