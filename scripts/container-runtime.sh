#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"

usage() {
  cat <<'EOF'
Usage: bash scripts/container-runtime.sh <docker|podman> <build|up|down|logs|ps|config>

Examples:
  bash scripts/container-runtime.sh docker up
  bash scripts/container-runtime.sh podman build
EOF
}

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

require_runtime() {
  runtime="$1"
  if ! command -v "$runtime" >/dev/null 2>&1; then
    if [ "$runtime" = "podman" ]; then
      fail "Podman is not installed. Install it with: brew install podman"
    fi
    fail "Docker is not installed. Install Docker Desktop and ensure 'docker' is on PATH."
  fi
}

if [ "$#" -ne 2 ]; then
  usage >&2
  exit 1
fi

runtime="$1"
action="$2"

case "$runtime" in
  docker|podman)
    ;;
  *)
    usage >&2
    fail "Unsupported runtime: $runtime"
    ;;
esac

case "$action" in
  build|up|down|logs|ps|config)
    ;;
  *)
    usage >&2
    fail "Unsupported action: $action"
    ;;
esac

require_runtime "$runtime"

case "$runtime" in
  docker)
    set -- docker compose -f "$COMPOSE_FILE"
    ;;
  podman)
    set -- podman compose -f "$COMPOSE_FILE"
    ;;
esac

case "$action" in
  build)
    set -- "$@" build
    ;;
  up)
    set -- "$@" up -d
    ;;
  down)
    set -- "$@" down --remove-orphans
    ;;
  logs)
    set -- "$@" logs --tail=200
    ;;
  ps)
    set -- "$@" ps
    ;;
  config)
    set -- "$@" config
    ;;
esac

cd "$REPO_ROOT"
exec "$@"
