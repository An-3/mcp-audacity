#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: Python executable '$PYTHON_BIN' not found." >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Error: Python 3.10+ is required.")
print(f"Using Python {sys.version.split()[0]}")
PY

echo "[1/3] Creating virtual environment at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "[2/3] Upgrading pip"
"$VENV_DIR/bin/python" -m pip install --upgrade pip

echo "[3/3] Installing dependencies"
"$VENV_DIR/bin/python" -m pip install "mcp[cli]>=1.6.0" "httpx>=0.28.1"

echo "Setup complete."
echo "Next:"
echo "  1) Start Audacity and enable mod-script-pipe in Modules settings"
echo "  2) Run: ./scripts/smoke_test.sh"
echo "  3) Run: ./scripts/run.sh"
