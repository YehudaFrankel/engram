#!/usr/bin/env python3
"""
Claude Code PreCompact hook — reminds Claude to preserve key context before compaction.

Output: JSON with hookSpecificOutput.additionalContext
Hook event: PreCompact (fires before Claude compacts the conversation)

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

    # Build a reminder with the current memory index so Claude knows what to preserve
    reminder_lines = [
        'BEFORE COMPACTING — check that memory files are up to date:',
        '',
        '• Any JS function added or changed → js_functions.md',
        '• Any HTML element or CSS class changed → html_css_reference.md',
        '• Any endpoint or backend method changed → backend_reference.md',
        '• Any architecture decision or gotcha → project_status.md',
        '',
        'After compaction, MEMORY.md will be auto-loaded at session start.',
        '',
    ]

    # Append the memory index so Claude knows which files exist
    memory_md = memory_dir / 'MEMORY.md'
    if memory_md.exists():
        reminder_lines.append('Current memory index:')
        text = memory_md.read_text(encoding='utf-8', errors='ignore').strip()
        # Show only the index list (skip currentDate and boilerplate)
        for line in text.splitlines():
            if line.startswith('- [') or line.startswith('- **'):
                reminder_lines.append('  ' + line)

    context = '\n'.join(reminder_lines)

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'PreCompact',
            'additionalContext': context
        }
    }
    print(json.dumps(output))


if __name__ == '__main__':
    main()
