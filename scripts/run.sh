#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Error: virtualenv not found at $VENV_DIR" >&2
  echo "Run ./scripts/setup.sh first." >&2
  exit 1
fi

if ! ls /tmp/audacity_script_pipe.to.* /tmp/audacity_script_pipe.from.* >/dev/null 2>&1; then
  echo "Warning: Audacity mod-script-pipe files were not found in /tmp." >&2
  echo "Start Audacity and enable mod-script-pipe (Modules), then retry." >&2
fi

exec "$PYTHON" "$ROOT_DIR/audacity_mcp_server.py"
