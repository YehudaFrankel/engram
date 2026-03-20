#!/usr/bin/env python3
"""
Claude Code Stop hook — warns if memory files have unsaved git changes.

Shows a reminder ONLY when changes are detected — silent otherwise.
Output: JSON with systemMessage (shown in Claude UI) or nothing at all.
Hook event: Stop (fires when Claude finishes responding)

No configuration needed — auto-detects memory directory.
"""

import json
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def find_memory_dir():
    """Auto-detect the .claude/memory directory."""
    for path in ROOT.rglob('MEMORY.md'):
        if '.claude' in path.parts:
            return path.parent
    return ROOT / '.claude/memory'


def main():
    memory_dir = find_memory_dir()

    if not memory_dir.exists():
        return  # No memory dir yet — nothing to check

    # Check for uncommitted changes in the memory directory
    try:
        result = subprocess.run(
            ['git', '-C', str(memory_dir), 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            # Changes detected — show a reminder
            output = {
                'systemMessage': 'Memory has unsaved changes. Type "End Session" to update and save.'
            }
            print(json.dumps(output))
        # If no changes or git not available: exit silently
    except Exception:
        pass  # Never block the session on a hook error


if __name__ == '__main__':
    main()
