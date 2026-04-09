# plaud-mcp

A containerized [MCP](https://modelcontextprotocol.io) server that gives Claude (and other MCP clients) access to your [Plaud](https://www.plaud.ai) recordings, transcripts, and AI summaries — with no Desktop app dependency.

## What you get

Eight tools available to Claude once connected:

| Tool | What it does |
|------|-------------|
| `check_connection` | Verify token, return file count |
| `get_file_count` | Total number of recordings |
| `get_recent_files` | Recordings from the last N days |
| `get_files` | Recordings with optional date filter |
| `get_file` | Metadata for a specific recording |
| `get_transcript` | Full transcript with speaker labels |
| `get_summary` | AI-generated summary |
| `search_transcripts` | Search across recent transcripts |

## Quick start

```bash
git clone https://github.com/chet-kamiwaza/plaud-mcp
cd plaud-mcp
pip install cryptography
python scripts/get-token.py   # prints your PLAUD_TOKEN + PLAUD_DEVICE_ID
cp .env.example .env          # edit .env with the values above
docker compose up -d
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

Open a new Claude Code session — the Plaud tools are ready.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Claude Code](https://claude.ai/code) CLI installed
- Plaud desktop app installed and signed in (macOS) — needed once to extract your token

## Setup

### 1. Get your Plaud token (macOS)

The Plaud token is stored encrypted in the desktop app. The helper script extracts it automatically:

```bash
pip install cryptography
python scripts/get-token.py
```

Copy the output — you'll need it in the next step.

### 2. Create your `.env` file

```bash
cp .env.example .env
# Edit .env and paste your token values
```

`.env`:
```
PLAUD_TOKEN=eyJ...
PLAUD_DEVICE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 3. Start the container

```bash
docker compose up -d
```

The `docker-compose.yml` pulls the pre-built image from `ghcr.io/chet-kamiwaza/plaud-mcp:latest` automatically. The container will restart whenever Docker Desktop starts (`restart: unless-stopped`).

### 4. Connect to Claude Code

```bash
claude mcp add --transport http --scope user plaud http://localhost:8080/mcp
```

That's it. Open a new Claude Code session and the Plaud tools will be available.

## Usage

Once connected, ask Claude things like:

- *"Show me my last 5 recordings"*
- *"Get the transcript from my meeting yesterday"*
- *"Search my recordings for anything about the budget"*
- *"Summarize the recording from April 8th"*

## Token refresh

Plaud tokens expire roughly every 26 days. When yours expires, re-run the helper script and update `.env`:

```bash
python scripts/get-token.py
# Update .env with the new token
docker compose up -d --force-recreate
```

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

## Publishing a new image version

```bash
docker build -t ghcr.io/chet-kamiwaza/plaud-mcp:latest -t ghcr.io/chet-kamiwaza/plaud-mcp:vX.Y .
docker push ghcr.io/chet-kamiwaza/plaud-mcp:latest
docker push ghcr.io/chet-kamiwaza/plaud-mcp:vX.Y
```

> **Note:** After the first push, the ghcr.io package defaults to private. To allow others to pull without authenticating:
> GitHub → your profile → **Packages** → `plaud-mcp` → **Package settings** → **Change visibility → Public**.

## Stack

- Python 3.10 + [FastMCP](https://github.com/jlowin/fastmcp)
- Runs as non-root (UID 1000)
- No state stored in container — all data fetched live from Plaud API
