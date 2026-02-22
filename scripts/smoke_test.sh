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

exec "$PYTHON" "$ROOT_DIR/scripts/smoke_test.py"
