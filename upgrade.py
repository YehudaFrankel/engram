#!/usr/bin/env python3
"""
Upgrade from Lite to Full memory mode.

Adds tools/memory.py + lifecycle hooks to an existing Lite setup.
Keeps @rules/ files in parallel — static conventions stay in rules/,
dynamic session data (drift, journal, stop-check) handled by memory.py.

Usage: python upgrade.py
"""

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MEMORY_PY_URL = (
    "https://raw.githubusercontent.com/"
    "YehudaFrankel/Claude-Code-memory-starter-kit/main/tools/memory.py"
)

HOOKS = {
    "PostToolUse": [
        {
            "matcher": "Edit|Write",
            "hooks": [
                {
                    "type": "command",
                    "command": "python tools/memory.py --check-drift --silent",
                }
            ],
        }
    ],
    "Stop": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python tools/memory.py --journal",
                    "timeout": 10,
                    "statusMessage": "Capturing session journal...",
                },
                {
                    "type": "command",
                    "command": "python tools/memory.py --stop-check",
                    "timeout": 5,
                },
            ]
        }
    ],
}


def main():
    print("\n=== Upgrade to Full ===\n")

    # ── Python version check ──────────────────────────────────────────────────
    if sys.version_info < (3, 7):
        print(f"Error: Python 3.7+ required. You have {sys.version}")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} — OK")

    # ── Install tools/memory.py ───────────────────────────────────────────────
    dst = ROOT / "tools" / "memory.py"

    if dst.exists():
        print(f"tools/memory.py already present — skipping download")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nFetching memory.py from GitHub...")
        try:
            with urllib.request.urlopen(MEMORY_PY_URL) as response:
                dst.write_bytes(response.read())
            print("  Created tools/memory.py")
        except Exception as e:
            print(f"\nError downloading memory.py: {e}")
            print(f"Manual install:")
            print(f"  1. Download: {MEMORY_PY_URL}")
            print(f"  2. Save as: tools/memory.py")
            print(f"  3. Re-run: python upgrade.py")
            sys.exit(1)

    # ── Add hooks to .claude/settings.json ───────────────────────────────────
    settings_path = ROOT / ".claude" / "settings.json"

    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {"permissions": {"allow": ["Read", "Glob", "Grep"], "deny": []}}

    print()
    if "hooks" in settings:
        existing = list(settings["hooks"].keys())
        print(f".claude/settings.json already has hooks: {', '.join(existing)}")
        confirm = input("Add memory.py hooks alongside existing hooks? [y/N] ").strip().lower()
        if confirm != "y":
            print("Skipped hooks — add manually if needed.")
        else:
            changed = False
            for event, value in HOOKS.items():
                if event not in settings["hooks"]:
                    settings["hooks"][event] = value
                    print(f"  Added: {event}")
                    changed = True
                else:
                    print(f"  Skipped {event} — already exists")
            if changed:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
    else:
        settings["hooks"] = HOOKS
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        print("  Added lifecycle hooks to .claude/settings.json")

    # ── Done ─────────────────────────────────────────────────────────────────
    print(f"""
Done. Full mode is now active.

  tools/memory.py          — drift detection, session journal, stop reminders
  .claude/settings.json    — 3 hooks: PostToolUse (drift), Stop x2 (journal + reminders)

Your @rules/ files remain — static conventions load via @rules/ imports.
Dynamic tracking (drift, lessons, decisions) now handled by memory.py.

Restart Claude Code for hooks to take effect.
""")


if __name__ == "__main__":
    main()
