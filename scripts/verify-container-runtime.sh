#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
HELPER="$SCRIPT_DIR/container-runtime.sh"
CONFIG_OUTPUT=$(mktemp "${TMPDIR:-/tmp}/plaud-runtime-config.XXXXXX")

cleanup() {
  rm -f "$CONFIG_OUTPUT"
  if [ "${runtime:-}" != "" ] && [ -x "$HELPER" ]; then
    bash "$HELPER" "$runtime" down >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

if [ "$#" -ne 1 ]; then
  printf '%s\n' "Usage: bash scripts/verify-container-runtime.sh <docker|podman>" >&2
  exit 1
fi

runtime="$1"

case "$runtime" in
  docker|podman)
    ;;
  *)
    printf '%s\n' "Unsupported runtime: $runtime" >&2
    exit 1
    ;;
esac

if ! command -v "$runtime" >/dev/null 2>&1; then
  if [ "$runtime" = "podman" ]; then
    printf '%s\n' "Podman is not installed. Install it with: brew install podman" >&2
  else
    printf '%s\n' "Docker is not installed. Install Docker Desktop and ensure 'docker' is on PATH." >&2
  fi
  exit 1
fi

cd "$REPO_ROOT"

bash "$HELPER" "$runtime" config >"$CONFIG_OUTPUT"
if ! grep -q '127.0.0.1:8080:8080' "$CONFIG_OUTPUT"; then
  grep -q 'host_ip: 127.0.0.1' "$CONFIG_OUTPUT"
  grep -q 'published: "8080"' "$CONFIG_OUTPUT"
  grep -q 'target: 8080' "$CONFIG_OUTPUT"
fi

if lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1; then
  printf '%s\n' "Port 8080 is already in use on this host. Stop the existing listener before running ${runtime} verification." >&2
  lsof -nP -iTCP:8080 -sTCP:LISTEN >&2 || true
  exit 1
fi

bash "$HELPER" "$runtime" build
bash "$HELPER" "$runtime" up
bash "$HELPER" "$runtime" ps >/dev/null
