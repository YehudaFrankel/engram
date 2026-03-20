#!/usr/bin/env python3
"""
Claude Code SessionStart hook — injects memory into context automatically.
Claude starts every session warm, with full memory, without needing "Start Session".

Output: JSON with hookSpecificOutput.additionalContext
Hook event: SessionStart (fires when each new session begins)

No configuration needed — auto-detects memory directory.
"""

import json
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
    parts = []

    # ── MEMORY.md (index of all memory files) ────────────────────────────────
    memory_md = memory_dir / 'MEMORY.md'
    if memory_md.exists():
        parts.append('# Memory Index\n')
        parts.append(memory_md.read_text(encoding='utf-8', errors='ignore').strip())

    # ── STATUS.md (session log) ───────────────────────────────────────────────
    status_md = ROOT / 'STATUS.md'
    if status_md.exists():
        text = status_md.read_text(encoding='utf-8', errors='ignore').strip()
        # Show only the last ~30 lines (recent sessions) to keep context tight
        lines = text.splitlines()
        excerpt = '\n'.join(lines[-30:]) if len(lines) > 30 else text
        parts.append('\n\n# Current Status\n')
        parts.append(excerpt)

    if not parts:
        return  # Nothing to inject — exit silently

    context = '\n'.join(parts)

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': context
        }
    }
    print(json.dumps(output))


if __name__ == '__main__':
    main()
