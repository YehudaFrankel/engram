#!/usr/bin/env python3
"""
Claude Code Stop hook — warns if memory files have unsaved changes.

Shows a reminder ONLY when changes are detected — silent otherwise.
Output: JSON with systemMessage (shown in Claude UI) or nothing at all.
Hook event: Stop (fires when Claude finishes responding)

No configuration needed — auto-detects memory directory.
No git required — works with any sync method or no sync at all.
"""

import json
import os
from pathlib import Path
import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def find_memory_dir():
    """Auto-detect the .claude/memory directory."""
    for path in ROOT.rglob('MEMORY.md'):
        if '.claude' in path.parts:
            return path.parent
    return ROOT / '.claude/memory'


def has_unsaved_changes(memory_dir):
    """
    Check for unsaved memory changes.

    Strategy 1: git status (if git is available and memory is in a repo)
    Strategy 2: compare file mtimes against STATUS.md (fallback for non-git users)
    """
    # Try git first
    try:
        import subprocess
        result = subprocess.run(
            ['git', '-C', str(memory_dir), 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except Exception:
        pass

    # Fallback: check if any memory file is newer than STATUS.md
    status_file = ROOT / 'STATUS.md'
    if not status_file.exists():
        return False
    try:
        status_mtime = status_file.stat().st_mtime
        for md_file in memory_dir.rglob('*.md'):
            if md_file.stat().st_mtime > status_mtime:
                return True
    except Exception:
        pass

    return False


def main():
    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        return

    if has_unsaved_changes(memory_dir):
        print(json.dumps({
            'systemMessage': 'Memory has unsaved changes. Type "End Session" to save.'
        }))


if __name__ == '__main__':
    main()
