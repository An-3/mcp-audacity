#!/usr/bin/env python3
"""Simple local connectivity smoke test for Audacity MCP server plumbing.

This verifies that Audacity pipes are reachable and command responses are valid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from audacity_mcp_server import get_audacity_connection  # noqa: E402


def _without_batch_footer(text: str) -> str:
    lines = [line for line in text.splitlines() if "BatchCommand finished" not in line]
    return "\n".join(lines).strip()


def main() -> int:
    try:
        conn = get_audacity_connection()
    except Exception as exc:
        print(f"FAIL: Could not connect to Audacity pipes: {exc}")
        print("Hint: Start Audacity and enable mod-script-pipe in Modules settings.")
        return 1

    try:
        help_resp = conn.send_command("Help:")
        if "BatchCommand finished: OK" not in help_resp:
            print("FAIL: Help command did not complete successfully.")
            return 1

        tracks_resp = conn.send_command("GetInfo: Type=Tracks")
        if "BatchCommand finished: OK" not in tracks_resp:
            print("FAIL: GetInfo command did not complete successfully.")
            return 1

        payload = _without_batch_footer(tracks_resp)
        tracks = json.loads(payload) if payload else []

        print("PASS: Audacity pipe connection is healthy.")
        print(f"Tracks detected: {len(tracks)}")
        if tracks:
            names = [str(t.get("name", "<unnamed>")) for t in tracks[:5]]
            print("Example tracks:")
            for name in names:
                print(f"  - {name}")
        return 0
    except Exception as exc:
        print(f"FAIL: Smoke test error: {exc}")
        return 1
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
