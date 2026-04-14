#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
RUNTIME_VERIFY="$SCRIPT_DIR/verify-container-runtime.sh"

usage() {
  cat <<'EOF'
Usage: bash scripts/verify-local-mac.sh <podman|docker|all>

Examples:
  bash scripts/verify-local-mac.sh podman
  bash scripts/verify-local-mac.sh docker
  bash scripts/verify-local-mac.sh all
EOF
}

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

require_macos() {
  if [ "$(uname -s)" != "Darwin" ]; then
    fail "This validation flow is for macOS only."
  fi
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "$2"
  fi
}

require_podman_ready() {
  require_command "podman" "Podman is not installed. Install it with: brew install podman"
  require_command "python3" "python3 is required to evaluate Podman machine status on macOS."

  machine_json=$(podman machine list --format json 2>/dev/null || printf '[]')
  MACHINE_JSON="$machine_json" python3 - <<'PY'
import json
import os
import sys

try:
    machines = json.loads(os.environ["MACHINE_JSON"])
except Exception:
    sys.exit(1)

running = False
for machine in machines:
    last_up = machine.get("LastUp") or ""
    running_flag = machine.get("Running")
    if running_flag is True or last_up not in ("", "Currently stopped"):
        running = True
        break

if not running:
    sys.exit(1)
PY

  if ! podman info >/dev/null 2>&1; then
    fail "Podman is installed but not ready. Start it with: podman machine start"
  fi
}

require_docker_ready() {
  require_command "docker" "Docker is not installed. Install Docker Desktop and ensure 'docker' is on PATH."
  if ! docker info >/dev/null 2>&1; then
    fail "Docker is installed but the daemon is not ready. Start Docker Desktop and wait for it to finish booting."
  fi
}

run_runtime() {
  runtime="$1"
  case "$runtime" in
    podman)
      require_podman_ready
      ;;
    docker)
      require_docker_ready
      ;;
    *)
      fail "Unsupported runtime: $runtime"
      ;;
  esac

  bash "$RUNTIME_VERIFY" "$runtime"
}

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 1
fi

selection="$1"

require_macos
cd "$REPO_ROOT"

case "$selection" in
  podman)
    run_runtime podman
    ;;
  docker)
    run_runtime docker
    ;;
  all)
    run_runtime podman
    run_runtime docker
    ;;
  *)
    usage >&2
    fail "Unsupported runtime selection: $selection"
    ;;
esac

pytest -q
