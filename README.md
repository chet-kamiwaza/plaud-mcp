# plaud-mcp

A containerized [MCP](https://modelcontextprotocol.io) server that gives Claude (and other MCP clients) access to your [Plaud](https://www.plaud.ai) recordings, transcripts, and AI summaries — with no Desktop app dependency.

## What you get

Eleven tools available to Claude once connected:

| Tool | What it does |
|------|-------------|
| `check_connection` | Verify token, return file count |
| `get_file_count` | Total number of recordings |
| `get_recent_files` | Recordings from the last N days |
| `get_files` | Recordings with optional date filter |
| `get_file` | Metadata for a specific recording |
| `get_transcript` | Full transcript with speaker labels |
| `get_summary` | AI-generated summary |
| `get_highlights` | AI-generated highlights for a recording |
| `list_folders` | List Plaud folders (file tags) |
| `get_folder_files` | Recordings that belong to a specific folder |
| `search_transcripts` | Search across recent transcripts |

## Quick start

Local container workflows now support both Docker Desktop and Podman on macOS. The repo-owned helper scripts below are the canonical way to build, start, and validate the service locally.

### Choose a runtime

- **Docker Desktop** — supported and still works for local macOS usage
- **Podman** — supported on macOS with a running `podman machine`

### Runtime prerequisites

#### Docker Desktop

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Start Docker Desktop and wait for it to finish booting

#### Podman on macOS

```bash
brew install podman
podman machine init   # only needed the first time
podman machine start
```

Confirm the Podman VM is ready before continuing:

```bash
podman machine list
podman info
```

### Validate your local runtime

Run the repo-owned validation flow before or after setup changes:

```bash
bash scripts/verify-local-mac.sh docker
bash scripts/verify-local-mac.sh podman
```

If you want to validate both runtimes on the same machine, run them sequentially. Both use loopback port `8080` during local verification.

Choose the auth mode that matches your Plaud account:

### Option A — Auto-refresh (you sign in to Plaud with email + password)

The container logs in automatically and refreshes the token before it expires. Set it up once and forget about it.

```bash
git clone https://github.com/chet-kamiwaza/plaud-mcp
cd plaud-mcp
cp .env.example .env
# Edit .env: set PLAUD_AUTO_REFRESH=true, PLAUD_EMAIL, PLAUD_PASSWORD, PLAUD_DEVICE_ID
bash scripts/container-runtime.sh docker up
# or:
# bash scripts/container-runtime.sh podman up
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

### Option B — Browser auth (you sign in to Plaud with Google or Apple SSO)

SSO accounts can't use the password login endpoint. Run the setup script once to grab a long-lived token (~10 months) via the same browser flow the desktop app uses.

```bash
git clone https://github.com/chet-kamiwaza/plaud-mcp
cd plaud-mcp
python scripts/setup-auth.py
# Sign in with Google/Apple in the browser that opens.
# Copy the plaud:// redirect URL from the address bar and paste it back.
cp .env.example .env
# Set PLAUD_TOKEN_FILE=/app/data/plaud.token, PLAUD_DEVICE_ID=...
bash scripts/container-runtime.sh docker up
# or:
# bash scripts/container-runtime.sh podman up
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

Re-run `scripts/setup-auth.py` when the token nears expiry (it prints the date).

### Option C — Manual token (legacy)

Extract the token directly from a logged-in macOS Plaud desktop app. Requires re-extraction every ~26 days.

```bash
pip install cryptography
python scripts/get-token.py
cp .env.example .env          # set PLAUD_TOKEN and PLAUD_DEVICE_ID
bash scripts/container-runtime.sh docker up
# or:
# bash scripts/container-runtime.sh podman up
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

## Prerequisites

- Either [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Podman installed for container-based local usage on macOS
- [Claude Code](https://claude.ai/code) CLI installed
- A Plaud account (any sign-in method)
- For Option C only: the Plaud desktop app on macOS, signed in

## Local runtime commands

Use the repo-owned runtime helper for local container actions:

```bash
bash scripts/container-runtime.sh docker build
bash scripts/container-runtime.sh docker up
bash scripts/container-runtime.sh docker down

bash scripts/container-runtime.sh podman build
bash scripts/container-runtime.sh podman up
bash scripts/container-runtime.sh podman down
```

The helper keeps Docker Desktop and Podman on the same compose and env contract. The service binds locally on `127.0.0.1:8080`.

## Usage

Once connected, ask Claude things like:

- *"Show me my last 5 recordings"*
- *"Get the transcript from my meeting yesterday"*
- *"Search my recordings for anything about the budget"*
- *"Summarize the recording from April 8th"*
- *"Show me the highlights from my last meeting"*
- *"List my Plaud folders"*
- *"Show me the recordings in my Work folder"*

## Token refresh

The behaviour depends on which auth mode you picked:

- **Option A (auto-refresh):** Nothing to do. The server decodes the JWT's `exp` claim, and re-logs in automatically when the token is within 30 days of expiry. The new token is persisted to the mounted `plaud-data` volume.
- **Option B (SSO browser auth):** Re-run `python scripts/setup-auth.py` once every ~10 months. The script prints the expiry date when it writes the token.
- **Option C (manual token):** Re-run `python scripts/get-token.py` every ~26 days, update `.env`, and restart with `bash scripts/container-runtime.sh <docker|podman> up`.

For Kubernetes/mounted-secret workflows, `PLAUD_TOKEN_FILE` is reloaded on subsequent requests without restarting the process — useful when an external system rotates the token.

## Running without Docker

```bash
pip install .
PLAUD_TOKEN=... PLAUD_DEVICE_ID=... python -m plaud_mcp
```

Add to Claude Code with `--transport stdio` instead of `--transport http`.

## Building the image yourself

```bash
docker build -t plaud-mcp:latest .
```

Or with Podman:

```bash
podman build -t plaud-mcp:latest .
```

## Troubleshooting

- **Port `8080` is already in use**
  Stop the existing listener before running `bash scripts/verify-local-mac.sh docker`, `bash scripts/verify-local-mac.sh podman`, or either runtime helper `up` command.
- **Podman is installed but local startup fails**
  Check `podman machine list` and make sure the machine is running. If needed, run `podman machine start` and retry `bash scripts/verify-local-mac.sh podman`.
- **Docker commands fail even though Docker is installed**
  Docker Desktop may not be fully started yet. Wait for Docker Desktop to finish booting, then retry `bash scripts/verify-local-mac.sh docker`.
- **Podman prints a compose-provider message on macOS**
  That is expected on the validated Mac environment used for this milestone. Podman may delegate compose execution to an external compose provider while still using the repo-owned runtime commands successfully.
- **You want to validate both runtimes on one Mac**
  Run the Podman and Docker validation commands sequentially, not concurrently, because both use loopback port `8080` during startup checks.

## Runtime support note

This repo now supports Podman on macOS in addition to Docker Desktop. Docker Desktop remains a supported local path, and Podman has been validated locally with the repo-owned runtime and verification scripts:

```bash
bash scripts/container-runtime.sh <docker|podman> up
bash scripts/verify-local-mac.sh <docker|podman>
```

## Stack

- Python 3.10 + [FastMCP](https://github.com/jlowin/fastmcp)
- Runs as non-root (UID 1000)
- No state stored in container — all data fetched live from Plaud API
