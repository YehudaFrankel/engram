#!/usr/bin/env python3
"""
memory.py - Claude Recall memory system.
Single entry point for all memory operations.

Usage:
  python tools/memory.py --session-start              # SessionStart hook
  python tools/memory.py --check-drift                # PostToolUse hook
  python tools/memory.py --check-drift --silent       # silent drift check
  python tools/memory.py --precompact                 # PreCompact hook
  python tools/memory.py --postcompact                # PostCompact hook (re-inject memory after compaction)
  python tools/memory.py --stop-failure               # StopFailure hook (capture interruption state)
  python tools/memory.py --stop-check                 # Stop hook (unsaved + plans)
  python tools/memory.py --journal                    # Stop hook (session journal)
  python tools/memory.py --capture-correction         # UserPromptSubmit hook (correction detection)
  python tools/memory.py --process-corrections        # Stop hook (queue → lessons.md, auto-persist)
  python tools/memory.py --bootstrap                  # One-time codebase indexer
  python tools/memory.py --complexity-scan            # Project complexity scanner
  python tools/memory.py --complexity-scan --silent   # Silent scan (Start Session)
  python tools/memory.py --search "query"             # Search all memory .md files
  python tools/memory.py --search "query" --top 10   # Return top N files (default 5)
  python tools/memory.py --verify-edit                # PostToolUse hook (plan verification)
  python tools/memory.py --quick-learn               # Fast lesson capture (no ceremony)
  python tools/memory.py --kit-health                # Check all kit components are wired
  python tools/memory.py --regret-guard              # UserPromptSubmit: match prompt vs regret.md + decisions.md
  python tools/memory.py --decision-guard            # UserPromptSubmit: warn if prompt contradicts decisions.md
  python tools/memory.py --context-score             # Score CLAUDE.md sections by journal usage (dead weight finder)
  python tools/memory.py --velocity-estimate "task"  # Match task to past velocity entries, report honest estimate
  python tools/memory.py --mine-patterns             # Cluster lessons.md entries, surface recurring mistakes
  python tools/memory.py --error-lookup              # UserPromptSubmit: match debug prompt vs error-lookup.md
  python tools/memory.py --guard-check               # Scan codebase against all guards in guard-patterns.md
  python tools/memory.py --progress-report           # Show compounding metrics: sessions, lessons, errors known, skill accuracy
  python tools/memory.py --suggest-guards            # PostToolUse hook: fires when error-lookup.md is edited, prompts Generate Guards
  python tools/memory.py --log-edit                  # PostToolUse hook: append edited filename to draft-lessons.md
  python tools/memory.py --check-expiry              # SessionStart hook: warn about memory files past their expires: date
  python tools/memory.py --build-index               # Build semantic embedding index from all .md files
  python tools/memory.py --search-semantic "query"   # Semantic search — finds related memories by meaning, not just keywords
  python tools/memory.py --search-semantic "query" --top 10  # Return top N semantic matches
  python tools/memory.py --memory-diff               # Show what memory files changed this session (call at End Session)
  python tools/memory.py --permission-denied         # PermissionRequest hook: log denied tool operations
  python tools/memory.py --file-changed              # FileChanged hook: alert when CLAUDE.md or memory files change externally
  python tools/memory.py --pre-edit                  # PreToolUse hook: surface relevant lessons/regret/decisions before editing a file
  python tools/memory.py --post-read                 # PostToolUse hook (Read|Grep): log when Claude consults a memory file mid-session
  python tools/memory.py --mempalace-audit           # Audit memory files for missing Source blocks and valid_until dates
  python tools/memory.py --init                      # Interactive setup wizard — run once in a new project
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# Windows: default stdout encoding (cp1252) can't handle Unicode arrows, em-dashes, etc.
# Reconfigure to UTF-8 so hooks don't crash when printing status messages.
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
ARGS = set(sys.argv[1:])
SILENT = '--silent' in ARGS

# ─── Telemetry ─────────────────────────────────────────────────────────────────
try:
    from telemetry import ping as _ping
except Exception:
    def _ping(event, properties=None): pass


# ─── SHARED ───────────────────────────────────────────────────────────────────

def find_memory_dir():
    """Auto-detect the .claude/memory directory."""
    for path in ROOT.rglob('MEMORY.md'):
        if '.claude' in path.parts:
            return path.parent
    return ROOT / '.claude' / 'memory'


# ─── KIT HEALTH (silent helper) ──────────────────────────────────────────────

def _kit_health_fails():
    """Returns list of FAIL-level issues for silent check at session start."""
    fails = []
    mem_dir = find_memory_dir()
    if not (mem_dir / 'MEMORY.md').exists():
        fails.append('MEMORY.md missing — memory index not found')
    if not (ROOT / 'STATUS.md').exists():
        fails.append('STATUS.md missing — session tracking not initialized')
    if not (mem_dir / 'tasks').exists():
        fails.append('tasks/ directory missing — run Setup Memory')
    settings_paths = [ROOT / '.claude' / 'settings.json', ROOT / '.claude' / 'settings.local.json']
    if not any(sp.exists() for sp in settings_paths):
        fails.append('settings.json not found in .claude/ — hooks not wired, memory will not auto-load')
    return fails


# ─── SESSION START ────────────────────────────────────────────────────────────
# Injects MEMORY.md + STATUS.md into context before the first message.
# Hook: SessionStart

def _load_memory_context(memory_dir):
    """Return MEMORY.md content block, or ''."""
    memory_md = memory_dir / 'MEMORY.md'
    if not memory_md.exists():
        return ''
    return '# Memory Index\n\n' + memory_md.read_text(encoding='utf-8', errors='ignore').strip()


def _load_status_context():
    """Return last 30 lines of STATUS.md as a block, or ''."""
    status_md = ROOT / 'STATUS.md'
    if not status_md.exists():
        return ''
    text  = status_md.read_text(encoding='utf-8', errors='ignore').strip()
    lines = text.splitlines()
    excerpt = '\n'.join(lines[-30:]) if len(lines) > 30 else text
    return '\n\n# Current Status\n\n' + excerpt


def _check_interruption(memory_dir):
    """Return interruption block if last session was cut off, then delete the file. Returns ''."""
    path = memory_dir / 'tasks' / 'interruption_state.md'
    if not path.exists():
        return ''
    try:
        content = path.read_text(encoding='utf-8').strip()
        path.unlink()
        if content:
            return f'\n\n# \u26a0 LAST SESSION INTERRUPTED (API ERROR)\n{content}'
    except Exception:
        pass
    return ''


def _check_correction_queue(memory_dir):
    """Return pending corrections block if any are queued, or ''."""
    queue_file = memory_dir / 'tasks' / 'corrections_queue.md'
    if not queue_file.exists():
        return ''
    q       = queue_file.read_text(encoding='utf-8', errors='ignore')
    pending = re.findall(r'## \d{4}-\d{2}-\d{2} \d{2}:\d{2}\n\*\*Prompt:\*\* ".+?"', q)
    if not pending:
        return ''
    header = f'\n\n# Pending Corrections ({len(pending)} — apply this session, will persist at Stop)\n'
    return header + '\n'.join(pending)


def _reset_session_counter(memory_dir):
    """Reset the per-session edit counter to 0. Side-effect only."""
    try:
        counter_file = memory_dir / 'tasks' / 'session_edit_count.txt'
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        counter_file.write_text('0', encoding='utf-8')
    except Exception:
        pass


def _auto_team_pull():
    """Run team-pull silently if configured; return a block only when new entries arrive. Returns ''."""
    sync_config_path = ROOT / '.claude' / '.sync-config.json'
    team_config_path = ROOT / '.claude' / 'team_config.json'   # legacy fallback
    has_team = False
    if sync_config_path.exists():
        try:
            cfg      = json.loads(sync_config_path.read_text(encoding='utf-8'))
            has_team = bool(cfg.get('team_repo'))
        except Exception:
            pass
    elif team_config_path.exists():
        try:
            cfg      = json.loads(team_config_path.read_text(encoding='utf-8'))
            has_team = bool(cfg.get('repo'))
        except Exception:
            pass
    if not has_team:
        return ''
    try:
        import subprocess as _sp
        sync_script = ROOT / 'sync.py'
        if not sync_script.exists():
            return ''
        r   = _sp.run([sys.executable, str(sync_script), 'team-pull'],
                      capture_output=True, text=True, timeout=30)
        out = (r.stdout or '').strip()
        if out and ('+' in out or 'new entr' in out.lower()):
            return f'\n\n# Team Sync\n{out}'
    except Exception:
        pass  # Never block session start on team sync failure
    return ''


def _check_token_budget():
    """Return a compaction warning block if context is getting full, or ''."""
    _, pct, _ = _journal_estimate_tokens()
    if pct >= 80:
        return f'\n\n# \u26a0 Context at {pct}% — run /compact NOW before starting new work'
    if pct >= 60:
        return f'\n\n# Context at {pct}% — consider /compact soon'
    return ''


def _check_kit_health():
    """Return a kit health block if there are FAIL-level issues, or ''."""
    kit_fails = _kit_health_fails()
    if not kit_fails:
        return ''
    return '\n\n# \u26a0 Kit Health FAILs\n' + '\n'.join(f'- {f}' for f in kit_fails)


def _snapshot_memory_state(memory_dir):
    """Record line counts of all .md files at session start for end-session diff."""
    try:
        snapshot = {}
        for f in sorted(memory_dir.rglob('*.md')):
            rel = str(f.relative_to(memory_dir))
            try:
                snapshot[rel] = len(f.read_text(encoding='utf-8', errors='ignore').splitlines())
            except Exception:
                snapshot[rel] = 0
        snap_file = memory_dir / 'tasks' / 'session_snapshot.json'
        snap_file.parent.mkdir(parents=True, exist_ok=True)
        snap_file.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
    except Exception:
        pass  # Never block session start


def _last_meaningful_line(path, skip_lines):
    """Return the last non-blank, non-comment line after line index skip_lines."""
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        new_lines = lines[skip_lines:]
        for line in reversed(new_lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('<!--') and not stripped.startswith('#'):
                return stripped[:80] + ('...' if len(stripped) > 80 else '')
    except Exception:
        pass
    return ''


def cmd_memory_diff():
    """
    Compare current memory file state to the session-start snapshot.
    Prints line counts and the last line added per changed file.
    Call at End Session to confirm what was actually written.
    """
    memory_dir = find_memory_dir()
    snap_file  = memory_dir / 'tasks' / 'session_snapshot.json'

    if not snap_file.exists():
        print('No session snapshot found — run Start Session first.')
        return

    try:
        before = json.loads(snap_file.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'Could not read session snapshot: {e}')
        return

    changes = []
    for f in sorted(memory_dir.rglob('*.md')):
        rel = str(f.relative_to(memory_dir))
        try:
            current_lines = f.read_text(encoding='utf-8', errors='ignore').splitlines()
            current = len(current_lines)
        except Exception:
            continue
        before_count = before.get(rel, 0)
        diff = current - before_count
        if diff > 0:
            last = _last_meaningful_line(f, before_count)
            entry = f'{Path(rel).name} +{diff}'
            if last:
                entry += f'  ("{last}")'
            changes.append(entry)
        elif diff < 0:
            changes.append(f'{Path(rel).name} {diff}')

    if changes:
        print('Memory saved this session:')
        for c in changes:
            print(f'  {c}')
    else:
        print('Memory unchanged this session.')


def _auto_expire_memories(memory_dir):
    """Move expired memory files to archive/. Returns count of files archived."""
    today = datetime.now().date()
    archive_dir = memory_dir / 'archive'
    archived = []
    for md_file in sorted(memory_dir.rglob('*.md')):
        # Skip files already in archive or tasks/
        if 'archive' in md_file.parts or 'tasks' in md_file.parts:
            continue
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            m = re.search(r'^(?:expires|valid_until):\s*(\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
            if not m:
                continue
            exp_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
            if exp_date < today:
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / md_file.name
                # Avoid overwriting if name collides
                if dest.exists():
                    stem = md_file.stem
                    dest = archive_dir / f'{stem}_{exp_date.strftime("%Y%m%d")}.md'
                md_file.rename(dest)
                archived.append(md_file.name)
        except Exception:
            continue
    return archived


_STACK_SKILL_MAP = {
    'Java':       ['java-reviewer', 'debug-resin', 'new-endpoint'],
    'Python':     ['debug-session', 'test-runner', 'search-first'],
    'JavaScript': ['js-reviewer',   'debug-session'],
    'TypeScript': ['js-reviewer',   'test-runner'],
    'SQL':        ['add-db-column', 'search-first'],
    'Go':         ['debug-session', 'test-runner'],
    'Ruby':       ['debug-session', 'test-runner'],
    'Rust':       ['debug-session', 'test-runner'],
    'C#':         ['debug-session', 'new-endpoint'],
    'PHP':        ['debug-session', 'new-endpoint'],
}


def _suggest_skills_for_stack(memory_dir):
    """Read complexity_profile.md, compare Recommended Skills to existing skills, return suggestion block."""
    try:
        profile = memory_dir / 'complexity_profile.md'
        if not profile.exists():
            return ''
        text = profile.read_text(encoding='utf-8', errors='ignore')

        # Extract recommended skills from the profile
        rec_section = re.search(r'## Recommended Skills\n(.*?)(?:\n##|\Z)', text, re.DOTALL)
        if not rec_section:
            return ''
        recommended = re.findall(r'^- (\S+)', rec_section.group(1), re.MULTILINE)
        if not recommended:
            return ''

        # What skills already exist?
        skills_dir = ROOT / '.claude' / 'skills'
        existing = set()
        if skills_dir.exists():
            existing = {d.name for d in skills_dir.iterdir() if d.is_dir()}

        missing = [s for s in recommended if s not in existing]
        if not missing:
            return ''

        top = missing[:2]  # Surface at most 2 at a time — don't overwhelm
        skill_list = ', '.join(f'`{s}`' for s in top)
        return (
            f'# Skill suggestion: your complexity profile recommends {skill_list} '
            f'but {"they are" if len(top) > 1 else "it is"} not yet created. '
            f'Run `Create a skill called [name] that [description]` to add '
            f'{"them" if len(top) > 1 else "it"}.'
        )
    except Exception:
        return ''


def _memory_load_summary(memory_dir):
    """Count lessons, decisions, and rejected approaches. Return a one-line summary block."""
    try:
        counts = []

        lessons_file = memory_dir / 'lessons.md'
        if lessons_file.exists():
            text = lessons_file.read_text(encoding='utf-8', errors='ignore')
            n = sum(1 for line in text.splitlines() if line.strip().startswith('- '))
            if n:
                counts.append(f'{n} lesson{"s" if n != 1 else ""}')

        decisions_file = memory_dir / 'decisions.md'
        if decisions_file.exists():
            text = decisions_file.read_text(encoding='utf-8', errors='ignore')
            n = sum(1 for line in text.splitlines() if line.strip().startswith('- '))
            if n:
                counts.append(f'{n} decision{"s" if n != 1 else ""}')

        regret_file = memory_dir / 'tasks' / 'regret.md'
        if regret_file.exists():
            text = regret_file.read_text(encoding='utf-8', errors='ignore')
            # Count table rows (lines with | that aren't headers or separators)
            n = sum(1 for line in text.splitlines()
                    if line.strip().startswith('|') and '---' not in line
                    and not line.strip().startswith('| Approach'))
            if n:
                counts.append(f'{n} rejected approach{"es" if n != 1 else ""}')

        if not counts:
            return ''
        return f'# Memory loaded: {", ".join(counts)}.'
    except Exception:
        return ''


def cmd_session_start():
    memory_dir = find_memory_dir()

    # Auto-expire: move stale memories to archive/ before loading context
    archived = _auto_expire_memories(memory_dir)

    blocks = [
        _memory_load_summary(memory_dir),
        _load_memory_context(memory_dir),
        _load_status_context(),
        _check_interruption(memory_dir),
        _check_correction_queue(memory_dir),
        _auto_team_pull(),
        _check_token_budget(),
        _check_kit_health(),
        _suggest_skills_for_stack(memory_dir),
        f'# {len(archived)} expired memory file(s) archived: {", ".join(archived)}' if archived else '',
    ]
    _reset_session_counter(memory_dir)
    _snapshot_memory_state(memory_dir)
    _ping('session_start')

    parts = [b for b in blocks if b]
    if not parts:
        return

    # Auto-greet: Claude announces session state on first user message without requiring "Start Session"
    auto_greet = (
        'SESSION AUTO-START: Memory is pre-loaded above. '
        'When the user sends their FIRST message this session, begin your response with one line: '
        '"Ready. [last meaningful change from STATUS.md]. [memory count summary]. What are we working on?" '
        '-- then answer their message normally. '
        'Do NOT wait for them to type "Start Session". '
        'If they already asked a specific question, answer it after the one-line greeting.'
    )
    # Memory assist: passive tracking instruction — Claude notes when memory changes its behavior
    mem_assist = (
        'MEMORY ASSIST (passive): As you work this session, mentally note when a lesson, decision, '
        'or rejected approach from memory visibly changes your response — prevents a mistake, '
        'saves a lookup, or avoids a rejected pattern. You will be asked to log these at session end.'
    )
    parts.insert(0, mem_assist)
    parts.insert(0, auto_greet)

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': '\n'.join(parts)
        }
    }
    print(json.dumps(output))


# ─── CAPTURE CORRECTION ──────────────────────────────────────────────────────
# Detects correction language in user prompts and queues them for /learn.
# Hook: UserPromptSubmit

_CORRECTION_PATTERNS = [
    # Direct correction starters
    r'(?i)^no[,!\. ]',                                         # "No, that's not right"
    r'(?i)^wrong[,!\. ]',                                      # "Wrong, I meant..."
    r'(?i)^actually[,\. ].{0,60}(wrong|not right|not what|didn|shouldn|mistake|incorrect)',
    r'(?i)^wait[,\. ].{0,40}(wrong|not right|not what|didn|stop)',

    # Imperative corrections
    r"(?i)\bdon'?t do that\b",
    r"(?i)\bdon'?t add ",
    r"(?i)\bdon'?t use ",
    r"(?i)\bplease don'?t ",
    r"(?i)\bstop doing\b",
    r"(?i)\bnever do \b",
    r"(?i)\bnever use \b",

    # Wrongness assertions
    r"(?i)that'?s wrong",
    r"(?i)that was wrong",
    r"(?i)you'?re wrong",
    r"(?i)you got it wrong",
    r"(?i)that'?s not (right|correct|what i|what we)",
    r"(?i)that'?s (incorrect|backwards|the wrong)",
    r"(?i)\bwrong approach\b",
    r"(?i)\bwrong (way|direction|method|pattern|function|table|file)\b",

    # "not what I" family
    r"(?i)not what i (asked|wanted|meant|said|needed)",
    r"(?i)that (was|is|isn'?t) what i (asked|wanted|meant|needed)",

    # Misunderstanding / mistake
    r"(?i)you misunderstood",
    r"(?i)you (missed|skipped) (the point|step|that)",
    r"(?i)i didn'?t (want|ask|need|mean) you to",
    r"(?i)i didn'?t (ask for|want) that",
    r"(?i)that'?s not what i (asked|said|wanted|needed)",

    # Undo / revert requests
    r"(?i)\bundo\b.{0,30}(just|last|that|you|added|wrote|changed)",
    r"(?i)\brevert\b.{0,20}(that|the last|what you)",
    r"(?i)\broll.?back\b.{0,20}(that|the last|what you)",
]


def _is_correction(prompt):
    for pattern in _CORRECTION_PATTERNS:
        if re.search(pattern, prompt):
            return True
    return False


def cmd_capture_correction():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        prompt = data.get('prompt', '').strip()
    except Exception:
        return

    if not prompt:
        return

    # --- remember: prefix → write directly to draft-lessons.md ---
    if prompt.lower().startswith('remember:'):
        lesson = prompt[len('remember:'):].strip()
        if lesson:
            memory_dir = find_memory_dir()
            draft = memory_dir / 'tasks' / 'draft-lessons.md'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            entry = f'\n- [{timestamp}] {lesson}'
            draft.parent.mkdir(parents=True, exist_ok=True)
            with open(draft, 'a', encoding='utf-8') as f:
                f.write(entry)
        return

    if not _is_correction(prompt):
        return

    memory_dir = find_memory_dir()
    queue_file = memory_dir / 'tasks' / 'corrections_queue.md'

    if not queue_file.exists():
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text(
            '# Corrections Queue\n\n'
            '<!-- Auto-captured by UserPromptSubmit hook. -->\n'
            '<!-- Claude reads and clears this during /learn. -->\n',
            encoding='utf-8'
        )

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    entry = f'\n## {timestamp}\n**Prompt:** "{prompt}"\n'
    with open(queue_file, 'a', encoding='utf-8') as f:
        f.write(entry)


# ─── PROCESS CORRECTIONS ──────────────────────────────────────────────────────
# Moves corrections_queue.md entries → lessons.md rows. Runs at Stop.
# Hook: Stop

def cmd_process_corrections():
    memory_dir = find_memory_dir()
    queue_file = memory_dir / 'tasks' / 'corrections_queue.md'

    if not queue_file.exists():
        return

    content = queue_file.read_text(encoding='utf-8', errors='ignore')
    entries = re.findall(
        r'## (\d{4}-\d{2}-\d{2}) \d{2}:\d{2}\n\*\*Prompt:\*\* "(.+?)"',
        content, re.DOTALL
    )

    if not entries:
        return

    lessons_file = memory_dir / 'tasks' / 'lessons.md'
    with open(lessons_file, 'a', encoding='utf-8') as f:
        for date, prompt_text in entries:
            rule = prompt_text[:120] + ('...' if len(prompt_text) > 120 else '')
            f.write(f'| {date} | Auto-captured correction | {rule} |\n')

    queue_file.write_text(
        '# Corrections Queue\n\n'
        '<!-- Auto-captured by UserPromptSubmit hook. -->\n'
        '<!-- Claude reads and clears this during /learn. -->\n',
        encoding='utf-8'
    )


# ─── CHECK DRIFT ─────────────────────────────────────────────────────────────
# Compares live code against memory files. Flags undocumented changes.
# Hook: PostToolUse (after every Edit/Write)

_EXCLUDE_DIRS = {
    'node_modules', 'vendor', 'dist', 'build', '.git',
    'bower_components', 'coverage', '__pycache__', 'tools',
    '.cache', 'out', 'tmp', 'temp',
}

_MODIFIER_SUFFIXES = (
    '-active', '-open', '-disabled', '-locked', '-empty', '-success',
    '-error', '-loading', '-collapsed', '-dirty', '-sm', '-lg', '-xs',
    '-full', '-inline', '-new', '-replied', '-flush',
)

_FUNC_PATTERNS = [
    re.compile(r'^function\s+(\w+)\s*\(', re.MULTILINE),
    re.compile(r'^async\s+function\s+(\w+)\s*\(', re.MULTILINE),
    re.compile(r'^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(', re.MULTILINE),
    re.compile(r'^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', re.MULTILINE),
    re.compile(r'^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\w+\s*=>', re.MULTILINE),
    re.compile(r'^\s{2,}(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
    re.compile(r'^\s+(\w+)\s*:\s*(?:async\s+)?function', re.MULTILINE),
]

_JS_KEYWORDS = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'return',
    'break', 'continue', 'try', 'catch', 'finally', 'throw', 'new',
    'delete', 'typeof', 'instanceof', 'in', 'of', 'class', 'extends',
    'import', 'export', 'default', 'const', 'let', 'var', 'async',
    'await', 'yield', 'static', 'super', 'this', 'true', 'false', 'null',
    'undefined', 'void', 'debugger', 'with', 'function', 'setTimeout',
    'setInterval', 'clearTimeout', 'clearInterval', 'console', 'window',
    'document', 'module', 'require', 'Promise', 'Object', 'Array',
}


def _drift_is_excluded(path):
    return any(part in _EXCLUDE_DIRS for part in path.parts)


def _drift_is_minified(path):
    return '.min.' in path.name or path.name.endswith('-min.js') or path.name.endswith('-min.css')


def _drift_is_too_large(path):
    try:
        return path.stat().st_size > 500_000
    except OSError:
        return True


def _drift_detect_js_files():
    files = []
    for path in sorted(ROOT.rglob('*.js')):
        if _drift_is_excluded(path) or _drift_is_minified(path) or _drift_is_too_large(path):
            continue
        files.append(path)
    return files


def _drift_detect_css_files():
    files = []
    for path in sorted(ROOT.rglob('*.css')):
        if _drift_is_excluded(path) or _drift_is_minified(path) or _drift_is_too_large(path):
            continue
        files.append(path)
    return files


def _drift_detect_css_prefix(css_files):
    prefix_counts = Counter()
    class_pattern = re.compile(r'\.([\w][\w-]*)')
    for path in css_files:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for m in class_pattern.finditer(text):
            cls = m.group(1)
            parts = cls.split('-')
            if len(parts) >= 2:
                prefix_counts[parts[0] + '-'] += 1
    if not prefix_counts:
        return r'\.([\w-]+)'
    top_prefix, top_count = prefix_counts.most_common(1)[0]
    total = sum(prefix_counts.values())
    if top_count / total >= 0.4 and top_count >= 5:
        return rf'\.({re.escape(top_prefix)}[\w-]+)'
    return r'\.([\w-]+)'


def _drift_extract_js_functions(paths):
    found = {}
    for path in paths:
        if not path.exists():
            if not SILENT:
                print(f'  WARN: JS file not found: {path}')
            continue
        if _drift_is_too_large(path):
            if not SILENT:
                print(f'  WARN: Skipping {path.name} — file exceeds 500KB')
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for pattern in _FUNC_PATTERNS:
            for m in pattern.finditer(text):
                name = m.group(1)
                if name not in _JS_KEYWORDS and name not in found:
                    found[name] = path.name
    return found


def _drift_extract_memory_functions(md_path):
    if not md_path.exists():
        return set()
    text = md_path.read_text(encoding='utf-8', errors='ignore')
    pattern = re.compile(r'`(\w+)(?:\([^)]*\))?`')
    return {m.group(1) for m in pattern.finditer(text)}


def _drift_extract_css_classes(paths, css_pattern):
    found = set()
    pattern = re.compile(css_pattern)
    for path in paths:
        if not path.exists():
            if not SILENT:
                print(f'  WARN: CSS file not found: {path}')
            continue
        if _drift_is_too_large(path):
            if not SILENT:
                print(f'  WARN: Skipping {path.name} — file exceeds 500KB')
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        found.update(m.group(1) for m in pattern.finditer(text))
    return found


def _drift_extract_memory_css(md_path, css_pattern):
    if not md_path.exists():
        return set()
    text = md_path.read_text(encoding='utf-8', errors='ignore')
    return {m.group(1) for m in re.compile(css_pattern).finditer(text)}


def cmd_check_drift():
    memory_dir = find_memory_dir()
    js_files = _drift_detect_js_files()
    css_files = _drift_detect_css_files()
    css_pattern = _drift_detect_css_prefix(css_files)
    js_memory = memory_dir / 'js_functions.md'
    css_memory = memory_dir / 'html_css_reference.md'

    if not js_files and not css_files:
        if not SILENT:
            print('No JS or CSS files found. Are you running from the project root?')
        sys.exit(0)

    if not SILENT:
        print(f'Scanning: {len(js_files)} JS, {len(css_files)} CSS | memory: {memory_dir}')

    drift = False

    if js_files and js_memory.exists():
        code_fns = _drift_extract_js_functions(js_files)
        mem_fns = _drift_extract_memory_functions(js_memory)
        missing = set(code_fns.keys()) - mem_fns
        stale = mem_fns - set(code_fns.keys())
        if missing:
            drift = True
            print('DRIFT DETECTED \u2014 MISSING from js_functions.md (exist in code):')
            for fn in sorted(missing):
                print(f'  + {fn}  [{code_fns[fn]}]')
        if stale:
            drift = True
            print('DRIFT DETECTED \u2014 STALE in js_functions.md (no longer in code):')
            for fn in sorted(stale):
                print(f'  - {fn}')

    if css_files and css_memory.exists():
        code_classes = _drift_extract_css_classes(css_files, css_pattern)
        mem_classes = _drift_extract_memory_css(css_memory, css_pattern)
        stale_css = mem_classes - code_classes
        if stale_css:
            drift = True
            print('DRIFT DETECTED \u2014 STALE in html_css_reference.md (no longer in CSS):')
            for cls in sorted(stale_css):
                print(f'  - .{cls}')
        missing_css = code_classes - mem_classes
        significant = {c for c in missing_css if not any(c.endswith(s) for s in _MODIFIER_SUFFIXES)}
        if significant:
            drift = True
            print('DRIFT DETECTED \u2014 NEW CSS classes not yet in html_css_reference.md:')
            for cls in sorted(significant):
                print(f'  + .{cls}')

    plans_dir = memory_dir / 'plans'
    if plans_dir.exists():
        memory_md = memory_dir / 'MEMORY.md'
        memory_text = memory_md.read_text(encoding='utf-8', errors='ignore') if memory_md.exists() else ''
        plan_files = {p.stem for p in plans_dir.glob('*.md') if not p.name.startswith('_')}
        referenced = set(re.findall(r'\bplans/(?!archive/)([^/)]+)\.md', memory_text))
        undocumented = plan_files - referenced
        if undocumented:
            drift = True
            print('DRIFT DETECTED \u2014 Plan files not referenced in MEMORY.md:')
            for p in sorted(undocumented):
                print(f'  + plans/{p}.md')
        stale_refs = referenced - plan_files
        if stale_refs:
            drift = True
            print('DRIFT DETECTED \u2014 MEMORY.md references missing plan files:')
            for p in sorted(stale_refs):
                print(f'  - plans/{p}.md (missing)')

    if not drift:
        if not SILENT:
            print('OK \u2014 no drift detected')
        sys.exit(0)
    else:
        sys.exit(1)


# ─── PRECOMPACT ───────────────────────────────────────────────────────────────
# Reinjects memory before Claude compacts the conversation.
# Hook: PreCompact

def cmd_precompact():
    memory_dir = find_memory_dir()
    lines = [
        'BEFORE COMPACTING \u2014 check that memory files are up to date:',
        '',
        '\u2022 Any JS function added or changed \u2192 js_functions.md',
        '\u2022 Any HTML element or CSS class changed \u2192 html_css_reference.md',
        '\u2022 Any endpoint or backend method changed \u2192 backend_reference.md',
        '\u2022 Any architecture decision or gotcha \u2192 project_status.md',
        '',
        'After compaction, MEMORY.md will be auto-loaded at session start.',
        '',
    ]
    memory_md = memory_dir / 'MEMORY.md'
    if memory_md.exists():
        lines.append('Current memory index:')
        for line in memory_md.read_text(encoding='utf-8', errors='ignore').strip().splitlines():
            if line.startswith('- [') or line.startswith('- **'):
                lines.append('  ' + line)
    output = {
        'hookSpecificOutput': {
            'hookEventName': 'PreCompact',
            'additionalContext': '\n'.join(lines)
        }
    }
    print(json.dumps(output))


# ─── POST COMPACT ────────────────────────────────────────────────────────────
# Re-injects MEMORY.md after compaction so the session resumes warm.
# Hook: PostCompact

def cmd_postcompact():
    memory_dir = find_memory_dir()
    lines = [
        'COMPACTION COMPLETE — memory re-loaded:',
        '',
    ]
    memory_md = memory_dir / 'MEMORY.md'
    if memory_md.exists():
        lines.append('Current memory index:')
        for line in memory_md.read_text(encoding='utf-8', errors='ignore').strip().splitlines():
            if line.startswith('- [') or line.startswith('- **'):
                lines.append('  ' + line)
    lines += [
        '',
        'Session continues. MEMORY.md is fresh in context.',
    ]
    output = {
        'hookSpecificOutput': {
            'hookEventName': 'PostCompact',
            'additionalContext': '\n'.join(lines)
        }
    }
    print(json.dumps(output))


# ─── STOP FAILURE ─────────────────────────────────────────────────────────────
# Captures interruption state when the session ends due to an API error.
# Surfaced by cmd_session_start() on the next session.
# Hook: StopFailure

def cmd_stop_failure():
    memory_dir = find_memory_dir()
    interrupt_path = memory_dir / 'tasks' / 'interruption_state.md'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    error_detail = ''
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            if payload.get('error'):
                error_detail = f' — Error: {payload["error"]}'
    except Exception:
        pass

    content = (
        f'## Interrupted at {timestamp}{error_detail}\n'
        'Session ended due to API error. Check STATUS.md for last known task.\n'
        'Resume: re-read the task context and verify last edit was saved correctly.\n'
    )
    try:
        interrupt_path.parent.mkdir(parents=True, exist_ok=True)
        interrupt_path.write_text(content, encoding='utf-8')
    except Exception:
        pass


# ─── STOP CHECK ──────────────────────────────────────────────────────────────
# Warns about unsaved memory and surfaces open plans.
# Hook: Stop

def _stop_has_unsaved(memory_dir):
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


def _stop_open_plans(memory_dir):
    plans_dir = memory_dir / 'plans'
    if not plans_dir.exists():
        return []
    open_plans = []
    for plan_file in sorted(plans_dir.glob('*.md')):
        if plan_file.name.startswith('_'):
            continue
        try:
            text = plan_file.read_text(encoding='utf-8')
            m = re.search(r'\*\*Status:\*\*\s*(.+)', text)
            if not m:
                continue
            status = m.group(1).strip()
            if status not in ('Draft', 'On Hold'):
                continue
            open_q = len(re.findall(r'^- \[ \] .+', text, re.MULTILINE))
            if open_q > 0:
                name = plan_file.stem.replace('-', ' ').title()
                open_plans.append((name, status, open_q))
        except Exception:
            continue
    return open_plans


def cmd_stop_check():
    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        return
    messages = []
    if _stop_has_unsaved(memory_dir):
        messages.append('Memory has unsaved changes. Type "End Session" to save.')
    for name, status, count in _stop_open_plans(memory_dir):
        q = 'question' if count == 1 else 'questions'
        messages.append(f'Open plan: {name} ({status}) \u2014 {count} {q} unresolved.')
    _, pct, _ = _journal_estimate_tokens()
    if pct >= 80:
        messages.append(f'Context at {pct}% — type /compact NOW before it fills up.')
    elif pct >= 60:
        messages.append(f'Context at {pct}% — consider /compact soon.')
    try:
        counter_file = memory_dir / 'tasks' / 'session_edit_count.txt'
        if counter_file.exists():
            edit_count = int(counter_file.read_text(encoding='utf-8').strip() or '0')
            if edit_count >= 3:
                messages.append(f'{edit_count} file saves this session — run "Pre-Ship Check" before shipping.')
            elif edit_count >= 1:
                messages.append(f'{edit_count} file save(s) this session.')
    except Exception:
        pass
    if messages:
        print(json.dumps({'systemMessage': ' | '.join(messages)}))


# ─── SESSION JOURNAL ──────────────────────────────────────────────────────────
# Auto-captures a searchable session summary on every Stop.
# Hook: Stop

def _journal_read_edited_files(draft_path):
    if not draft_path.exists():
        return []
    seen = []
    for line in draft_path.read_text(encoding='utf-8').splitlines():
        m = re.search(r'Edited: (.+)$', line)
        if m:
            f = m.group(1).strip()
            if f not in seen:
                seen.append(f)
    return seen


def _journal_read_phase(status_path):
    if not status_path.exists():
        return ''
    lines = status_path.read_text(encoding='utf-8').splitlines()
    capture_next = False
    for line in lines:
        if capture_next and line.strip():
            phase = re.sub(r'^>\s*', '', line)
            phase = re.sub(r'^\*\*[^*]+\*\*\s*', '', phase)
            return phase[:120]
        if '## Current Phase' in line:
            capture_next = True
    return ''


def _journal_estimate_tokens():
    try:
        project_dir = ROOT / '.claude' / 'projects'
        if not project_dir.exists():
            project_dir = Path.home() / '.claude' / 'projects'
        jsonl_files = list(project_dir.rglob('*.jsonl'))
        if not jsonl_files:
            return 0, 0, ''
        latest = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        tokens = round(latest.stat().st_size / 4)
        pct = round(tokens / 200000 * 100)
        warn = ''
        if pct >= 80:
            warn = f' [!!! {pct}% context - compact soon]'
        elif pct >= 60:
            warn = f' [{pct}% context used]'
        return tokens, pct, warn
    except Exception:
        return 0, 0, ''


def _journal_read_edit_count(mem_dir):
    counter_file = mem_dir / 'tasks' / 'session_edit_count.txt'
    if counter_file.exists():
        try:
            return int(counter_file.read_text(encoding='utf-8').strip())
        except Exception:
            pass
    return 0


def _journal_open_plans(mem_dir):
    plans_dir = mem_dir / 'plans'
    if not plans_dir.exists():
        return []
    open_plans = []
    for plan_file in sorted(plans_dir.glob('*.md')):
        if plan_file.name.startswith('_'):
            continue
        try:
            text = plan_file.read_text(encoding='utf-8')
            m = re.search(r'\*\*Status:\*\*\s*(.+)', text)
            if not m:
                continue
            status = m.group(1).strip()
            if status in ('Draft', 'On Hold'):
                name = plan_file.stem.replace('-', ' ').title()
                open_plans.append(f'{name} ({status})')
        except Exception:
            pass
    return open_plans


def cmd_journal():
    mem_dir = find_memory_dir()
    draft_file = mem_dir / 'tasks' / 'draft-lessons.md'
    status_file = mem_dir / 'STATUS.md'
    journal_file = mem_dir / 'session_journal.md'

    edited_files = _journal_read_edited_files(draft_file)
    phase = _journal_read_phase(status_file)
    edit_count = _journal_read_edit_count(mem_dir)
    open_plans = _journal_open_plans(mem_dir)
    tokens, pct, warn = _journal_estimate_tokens()

    if not edited_files and not phase:
        return

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    files_str = ', '.join(edited_files) if edited_files else 'no files edited'
    edit_str = f'{edit_count} file saves' if edit_count > 0 else '0 file saves'
    token_str = f'~{tokens:,} tokens ({pct}%){warn}' if tokens > 0 else 'unknown'
    plans_str = ', '.join(open_plans) if open_plans else ''

    entry = (
        f'\n## [{now}]\n'
        f'**Files:** {files_str}\n'
        f'**Edits:** {edit_str} | **Tokens:** {token_str}\n'
        f'**What:** {phase}\n'
    )
    if plans_str:
        entry += f'**Open plans:** {plans_str}\n'

    if not journal_file.exists():
        journal_file.write_text(
            '# Session Journal\n'
            'Auto-captured every session. '
            'Search: Grep(pattern=\'keyword\', path=session_journal.md)\n',
            encoding='utf-8'
        )

    with open(journal_file, 'a', encoding='utf-8') as f:
        f.write(entry)

    if draft_file.exists():
        draft_file.write_text(
            '# Draft Lessons (auto-tracked edits)\n'
            '_Run /learn to extract patterns from these._\n',
            encoding='utf-8'
        )

    # Auto-capture prompt: if files were edited, nudge Claude to record a lesson now
    if edit_count and edit_count > 0:
        lessons_path = mem_dir / 'lessons.md'
        lessons_rel = str(lessons_path.relative_to(ROOT)) if ROOT in lessons_path.parents else str(lessons_path)
        assist_path = mem_dir / 'tasks' / 'memory_assist.md'
        assist_rel = str(assist_path.relative_to(ROOT)) if ROOT in assist_path.parents else str(assist_path)
        msg = (
            f'This session had {edit_count} file save(s). '
            f'If you fixed a non-obvious bug, made a key decision, or discovered a pattern worth remembering, '
            f'append one bullet to {lessons_rel} now — before this session ends. '
            f'Format: `- [what happened] — [why it matters]`. '
            f'Skip if nothing notable to record.\n\n'
            f'MEMORY ASSIST LOG: Also append one line to {assist_rel} for each lesson from memory '
            f'that visibly changed your response this session (prevented a mistake, saved a lookup, '
            f'avoided a rejected approach). Format: `- [lesson name or summary] — applied when: [what you were doing]`. '
            f'If memory made no observable difference this session, write: `- (none this session)`. '
            f'This log shows the user proof that memory is compounding.'
        )
        print(json.dumps({'systemMessage': msg}))


# ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
# One-time codebase indexer. Generates quick_index.md.
# Run: python tools/memory.py --bootstrap

_BOOTSTRAP_FILE_TYPES = {
    'Java':       ['.java'],
    'JavaScript': ['.js', '.mjs', '.cjs'],
    'TypeScript': ['.ts', '.tsx'],
    'Python':     ['.py'],
    'HTML':       ['.html', '.htm'],
    'CSS':        ['.css', '.scss', '.less'],
    'JSP':        ['.jsp', '.jspf'],
    'SQL':        ['.sql'],
    'Config':     ['.json', '.yaml', '.yml', '.xml', '.properties', '.env'],
    'Markdown':   ['.md'],
}

_BOOTSTRAP_SKIP = {
    'node_modules', '.git', '__pycache__', '.pytest_cache',
    'dist', 'build', 'out', 'target', '.gradle', '.mvn',
    'venv', '.venv', 'env', '.env', 'coverage', '.nyc_output',
    'files', 'uploads', 'backups', '.claude', '.playwright-mcp',
}

_BOOTSTRAP_MAX_PER_TYPE = 200


def _bootstrap_scan():
    groups = {t: [] for t in _BOOTSTRAP_FILE_TYPES}
    groups['Other'] = []
    ext_to_type = {ext: t for t, exts in _BOOTSTRAP_FILE_TYPES.items() for ext in exts}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _BOOTSTRAP_SKIP]
        for fname in filenames:
            full = Path(dirpath) / fname
            ext = full.suffix.lower()
            rel = full.relative_to(ROOT).as_posix()
            t = ext_to_type.get(ext, 'Other')
            if t == 'Other':
                continue
            if len(groups[t]) < _BOOTSTRAP_MAX_PER_TYPE:
                groups[t].append(rel)
    return {k: sorted(v) for k, v in groups.items() if v}


def cmd_bootstrap():
    mem_dir = find_memory_dir()
    index_file = mem_dir / 'quick_index.md'
    print(f'Scanning project: {ROOT}')
    groups = _bootstrap_scan()
    if not groups:
        print('No source files found.')
        return
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    total = sum(len(v) for v in groups.values())
    counts = ', '.join(f'{len(v)} {t}' for t, v in groups.items())
    lines = [
        '# Quick Index \u2014 Codebase Map',
        f'Auto-generated: {now}',
        f'Project root: {ROOT}',
        f'Total: {total} files ({counts})',
        '',
        'Usage: Grep(pattern=\'filename\', path=quick_index.md) to find any file.',
        '',
    ]
    for type_name, files in groups.items():
        lines.append(f'## {type_name} ({len(files)} files)')
        lines.append('')
        for f in files:
            lines.append(f'- `{f}`')
        lines.append('')
    mem_dir.mkdir(parents=True, exist_ok=True)
    index_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Quick index built: {total} files -> {index_file}')
    for t, files in groups.items():
        print(f'  {t}: {len(files)} files')
    memory_file = mem_dir / 'MEMORY.md'
    if memory_file.exists():
        content = memory_file.read_text(encoding='utf-8')
        if 'quick_index.md' not in content:
            entry = '\n- [Quick Index](quick_index.md) \u2014 All source files grouped by type. Rebuild: `python tools/memory.py --bootstrap`'
            memory_file.write_text(content.rstrip() + entry + '\n', encoding='utf-8')
            print('Registered quick_index.md in MEMORY.md')


# ─── COMPLEXITY SCAN ─────────────────────────────────────────────────────────
# Detects project stack and recommends skills.
# Called automatically by Start Session if no profile exists.

_LANG_EXTENSIONS = {
    'Java':       ['.java'],
    'JavaScript': ['.js', '.mjs', '.cjs'],
    'TypeScript': ['.ts', '.tsx'],
    'Python':     ['.py'],
    'HTML':       ['.html', '.htm'],
    'CSS':        ['.css', '.scss', '.less'],
    'JSP':        ['.jsp', '.jspf'],
    'SQL':        ['.sql'],
    'Go':         ['.go'],
    'Ruby':       ['.rb'],
    'PHP':        ['.php'],
    'Rust':       ['.rs'],
    'C#':         ['.cs'],
}

_SCAN_SKIP = {
    'node_modules', '.git', '__pycache__', '.pytest_cache',
    'dist', 'build', 'out', 'target', '.gradle', '.mvn',
    'venv', '.venv', 'env', '.env', 'coverage', '.nyc_output',
    'files', 'uploads', 'backups', '.claude', '.playwright-mcp',
}

_SKILL_MAP = {
    'Java':            ['java-reviewer', 'debug-resin', 'find-it'],
    'SQL':             ['write-query', 'add-db-column'],
    'db':              ['write-query', 'add-db-column'],
    'tests':           ['test-runner', 'verification-loop', 'smoke-test'],
    'api':             ['new-endpoint', 'search-first'],
    'JavaScript':      ['new-js-function', 'fix-bug'],
    'TypeScript':      ['new-js-function', 'fix-bug'],
    'Python':          ['fix-bug', 'code-review'],
    'high_complexity': ['plan', 'strategic-compact', 'learn'],
    'any':             ['fix-bug', 'code-review', 'learn', 'evolve'],
}

_OPTIONAL_SKILLS = {
    'java-reviewer': 'Java',
    'debug-resin':   'Java/Resin',
    'playwright':    'browser tests',
    'write-query':   'SQL/DB',
    'test-runner':   'test suite',
    'new-endpoint':  'API surface',
}

_PROFILE_MAX_AGE_DAYS = 30


def _scan_files():
    lang_counts = {lang: 0 for lang in _LANG_EXTENSIONS}
    ext_to_lang = {ext: lang for lang, exts in _LANG_EXTENSIONS.items() for ext in exts}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SCAN_SKIP]
        for fname in filenames:
            lang = ext_to_lang.get(Path(fname).suffix.lower())
            if lang:
                lang_counts[lang] += 1
    detected = {lang: count for lang, count in lang_counts.items() if count > 0}
    return detected, sum(detected.values())


def _scan_walk_source(patterns):
    for pattern in patterns:
        for fpath in ROOT.rglob(pattern):
            if any(p in _SCAN_SKIP for p in fpath.parts):
                continue
            try:
                yield fpath, fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                pass


def _scan_signals(detected_langs):
    signals = {'db': False, 'tests': False, 'api': False, 'framework': None}
    if detected_langs.get('SQL', 0) > 0:
        signals['db'] = True
    if not signals['db']:
        orm_re = re.compile(
            r'(import sqlalchemy|from sqlalchemy|require.*sequelize|knex\(|mongoose\.|prisma\.|typeorm)',
            re.IGNORECASE
        )
        for _, text in _scan_walk_source(['*.py', '*.js', '*.ts']):
            if orm_re.search(text):
                signals['db'] = True
                break
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SCAN_SKIP]
        if Path(dirpath).name.lower() in ('tests', 'test', '__tests__', 'spec'):
            signals['tests'] = True
            break
        for fname in filenames:
            if re.search(r'(\.spec\.|\.test\.|_test\.|test_)', fname):
                signals['tests'] = True
                break
        if signals['tests']:
            break
    api_re = re.compile(
        r'(webservice|@app\.route|@router\.|app\.(get|post|put|delete)\s*\(|'
        r'express\(\)|@GetMapping|@PostMapping|@RestController|router\.route)',
        re.IGNORECASE
    )
    for _, text in _scan_walk_source(['*.java', '*.py', '*.js', '*.ts']):
        if api_re.search(text):
            signals['api'] = True
            break
    if (ROOT / 'pom.xml').exists():
        signals['framework'] = 'Java/Maven'
    elif (ROOT / 'build.gradle').exists():
        signals['framework'] = 'Java/Gradle'
    elif (ROOT / 'package.json').exists():
        try:
            pkg = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            if 'react' in deps:     signals['framework'] = 'Node/React'
            elif 'vue' in deps:     signals['framework'] = 'Node/Vue'
            elif 'express' in deps: signals['framework'] = 'Node/Express'
            else:                   signals['framework'] = 'Node'
        except Exception:
            signals['framework'] = 'Node'
    elif (ROOT / 'requirements.txt').exists() or (ROOT / 'pyproject.toml').exists():
        signals['framework'] = 'Python'
    elif 'Java' in detected_langs:
        signals['framework'] = 'Java'
    return signals


def _scan_score(detected_langs, source_count, signals):
    code_langs = len([l for l in detected_langs if l not in ('HTML', 'CSS', 'Markdown')])
    if code_langs >= 3 or source_count >= 100 or (signals['db'] and signals['api'] and signals['tests']):
        return 'High'
    elif code_langs >= 2 or source_count >= 20 or signals['db'] or signals['tests']:
        return 'Medium'
    return 'Low'


def _scan_recommendations(detected_langs, signals, complexity):
    seen, recs = set(), []

    def add(skill, reason):
        if skill not in seen:
            seen.add(skill)
            recs.append((skill, reason))

    for skill in _SKILL_MAP['any']:
        add(skill, 'recommended for any project')
    for lang in detected_langs:
        for skill in _SKILL_MAP.get(lang, []):
            add(skill, f'{lang} detected')
    if signals['db']:
        for skill in _SKILL_MAP['db']:
            add(skill, 'database detected')
    if signals['tests']:
        for skill in _SKILL_MAP['tests']:
            add(skill, 'test suite detected')
    if signals['api']:
        for skill in _SKILL_MAP['api']:
            add(skill, 'API surface detected')
    if complexity == 'High':
        for skill in _SKILL_MAP['high_complexity']:
            add(skill, 'high complexity project')
    return recs


def _scan_profile_is_fresh(mem_dir):
    profile = mem_dir / 'complexity_profile.md'
    if not profile.exists():
        return False
    try:
        text = profile.read_text(encoding='utf-8')
        m = re.search(r'^Generated:\s*(\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
        if not m:
            return False
        generated = datetime.strptime(m.group(1), '%Y-%m-%d')
        return datetime.now() - generated < timedelta(days=_PROFILE_MAX_AGE_DAYS)
    except Exception:
        return False


def cmd_complexity_scan():
    mem_dir = find_memory_dir()
    if not SILENT:
        print(f'Scanning: {ROOT}')
    detected_langs, source_count = _scan_files()
    signals = _scan_signals(detected_langs)
    complexity = _scan_score(detected_langs, source_count, signals)
    recs = _scan_recommendations(detected_langs, signals, complexity)
    skip_list = [(s, f'no {r} detected') for s, r in _OPTIONAL_SKILLS.items()
                 if s not in {r[0] for r in recs}]
    now = datetime.now().strftime('%Y-%m-%d')
    lang_str = ', '.join(sorted(detected_langs.keys()))
    sig_parts = [
        f'DB={"yes" if signals["db"] else "no"}',
        f'Tests={"yes" if signals["tests"] else "no"}',
        f'API={"yes" if signals["api"] else "no"}',
    ]
    if signals['framework']:
        sig_parts.append(f'Framework={signals["framework"]}')
    lines = [
        '# Complexity Profile',
        f'Generated: {now}',
        f'Stack: {lang_str}',
        f'Source files: {source_count}',
        f'Complexity: {complexity}',
        f'Signals: {", ".join(sig_parts)}',
        '',
        '## Recommended Skills',
    ]
    for skill, reason in recs:
        lines.append(f'- {skill} \u2014 {reason}')
    if skip_list:
        lines += ['', '## Skills you can skip']
        for skill, reason in skip_list:
            lines.append(f'- {skill} \u2014 {reason}')
    lines += [
        '',
        '---',
        'Rescan: delete this file and run Start Session, '
        'or run `python tools/memory.py --complexity-scan` directly.',
    ]
    profile_path = mem_dir / 'complexity_profile.md'
    mem_dir.mkdir(parents=True, exist_ok=True)
    profile_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    code_langs = '+'.join(sorted(l for l in detected_langs if l not in ('HTML', 'CSS'))) or 'unknown'
    print(f'Stack={code_langs} | Complexity={complexity} | {len(recs)} skills recommended')
    if not SILENT:
        print(f'Profile: {profile_path}')


# ─── SEARCH ───────────────────────────────────────────────────────────────────
# Full-text search across all .md files in .claude/memory/.
# Usage: python tools/memory.py --search "query" [--top N]

def cmd_search():
    argv = sys.argv[1:]

    # Parse --search <query> and optional --top <n>
    query = None
    top_n = 5
    i = 0
    while i < len(argv):
        if argv[i] == '--search' and i + 1 < len(argv):
            query = argv[i + 1]
            i += 2
        elif argv[i] == '--top' and i + 1 < len(argv):
            try:
                top_n = int(argv[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1

    if not query:
        print('Usage: python tools/memory.py --search "query" [--top N]')
        sys.exit(1)

    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        print('No memory directory found.')
        sys.exit(1)

    query_lower = query.lower()
    tokens = [t for t in query_lower.split() if t]

    results = []
    for md_file in sorted(memory_dir.rglob('*.md')):
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        text_lower = text.lower()
        lines = text.splitlines()

        # Score
        if query_lower in text_lower:
            score = 10
        elif all(t in text_lower for t in tokens):
            score = 5
        else:
            score = sum(1 for t in tokens if t in text_lower)

        if score == 0:
            continue

        # Collect matching lines with ±2 context, deduplicated by line index
        match_blocks = []
        covered = set()
        for idx, line in enumerate(lines):
            if any(t in line.lower() for t in tokens):
                start = max(0, idx - 2)
                end = min(len(lines), idx + 3)
                block_indices = range(start, end)
                if not covered.intersection(block_indices):
                    covered.update(block_indices)
                    match_blocks.append(lines[start:end])

        if match_blocks:
            rel = md_file.relative_to(memory_dir)
            results.append((score, rel, match_blocks))

    if not results:
        print(f'No results for: "{query}"')
        return

    results.sort(key=lambda x: -x[0])
    results = results[:top_n]

    print(f'Search: "{query}" -- {len(results)} file(s) matched\n')
    for score, rel, blocks in results:
        print(f'-- {rel}  (score {score})')
        for block in blocks:
            for line in block:
                print(f'  {line}')
            print()


# ─── SEMANTIC SEARCH ──────────────────────────────────────────────────────────
# Embedding-based search — finds related memories even with different wording.
# Requires: pip install sentence-transformers
# Model: all-MiniLM-L6-v2 (~90MB, local, no API key needed)
# Index: stored as memory_embeddings.pkl in memory directory

def _get_embedder():
    """Try to load sentence-transformers model. Returns model or None if not installed."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        return None


def cmd_build_index():
    """Build semantic embedding index from all .md files in memory directory."""
    import pickle

    embedder = _get_embedder()
    if embedder is None:
        print('sentence-transformers not installed. Run: pip install sentence-transformers')
        sys.exit(1)

    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        print('No memory directory found.')
        sys.exit(1)

    docs = []
    paths = []
    for md_file in sorted(memory_dir.rglob('*.md')):
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore').strip()
            if text:
                docs.append(text)
                paths.append(str(md_file.relative_to(memory_dir)))
        except Exception:
            continue

    if not docs:
        print('No .md files found to index.')
        sys.exit(1)

    if not SILENT:
        print(f'Building embeddings for {len(docs)} files...')
    embeddings = embedder.encode(docs, show_progress_bar=not SILENT)

    index_path = memory_dir / 'memory_embeddings.pkl'
    with open(index_path, 'wb') as f:
        pickle.dump({'paths': paths, 'embeddings': embeddings, 'docs': docs}, f)

    print(f'Index saved: {index_path}  ({len(docs)} files indexed)')


def cmd_search_semantic():
    """Semantic search across memory files using embedding cosine similarity."""
    import pickle

    argv = sys.argv[1:]
    query = None
    top_n = 5
    threshold = 0.25
    i = 0
    while i < len(argv):
        if argv[i] == '--search-semantic' and i + 1 < len(argv):
            query = argv[i + 1]
            i += 2
        elif argv[i] == '--top' and i + 1 < len(argv):
            try:
                top_n = int(argv[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1

    if not query:
        print('Usage: python tools/memory.py --search-semantic "query" [--top N]')
        sys.exit(1)

    memory_dir = find_memory_dir()
    index_path = memory_dir / 'memory_embeddings.pkl'

    def _fallback_keyword():
        sys.argv = [sys.argv[0], '--search', query, '--top', str(top_n)]
        ARGS.discard('--search-semantic')
        ARGS.add('--search')
        cmd_search()

    if not index_path.exists():
        print('No semantic index found. Run: python tools/memory.py --build-index')
        print('Falling back to keyword search...\n')
        _fallback_keyword()
        return

    embedder = _get_embedder()
    if embedder is None:
        print('sentence-transformers not installed. Run: pip install sentence-transformers')
        print('Falling back to keyword search...\n')
        _fallback_keyword()
        return

    with open(index_path, 'rb') as f:
        index = pickle.load(f)

    paths = index['paths']
    stored = index['embeddings']
    docs = index['docs']

    query_vec = embedder.encode([query])[0]

    # Cosine similarity using numpy array methods (numpy bundled with sentence-transformers)
    scored = []
    for idx in range(len(paths)):
        emb = stored[idx]
        dot = float((query_vec * emb).sum())
        norm = float(((query_vec * query_vec).sum() ** 0.5) * ((emb * emb).sum() ** 0.5))
        sim = dot / (norm + 1e-9)
        if sim >= threshold:
            scored.append((sim, paths[idx], docs[idx]))

    scored.sort(key=lambda x: -x[0])
    scored = scored[:top_n]

    if not scored:
        print(f'No semantic matches for: "{query}" (threshold={threshold})')
        print(f'Try: python tools/memory.py --search "{query}" for keyword fallback')
        return

    print(f'Semantic search: "{query}" -- {len(scored)} match(es)\n')
    for sim, path, doc in scored:
        print(f'-- {path}  (similarity {sim:.2f})')
        preview = [ln for ln in doc.splitlines() if ln.strip()][:5]
        for line in preview:
            print(f'  {line}')
        print()


# ─── VERIFY EDIT ──────────────────────────────────────────────────────────────
# Fires after every Edit/Write — reminds Claude to read back the changed lines
# and confirm they match the plan's After block.
# Hook: PostToolUse (Edit|Write)

def cmd_verify_edit():
    file_info = ''
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            tool_input = payload.get('tool_input', {})
            fp = tool_input.get('file_path', '')
            if fp:
                name = fp.replace('\\', '/').split('/')[-1]
                file_info = f' ({name})'
    except Exception:
        pass
    msg = (
        f'Code was edited{file_info}. '
        '(This message is from the plan-verification hook — it fires automatically after every Edit or Write.) '
        'REQUIRED: Read back the changed lines and quote them verbatim to the user. '
        'Not a paraphrase. Not "the code now does X". The actual raw file content, line by line. '
        'Then write: \u2713 Verified [file]:[lines] \u2014 [exact quoted lines] '
        'A summary does NOT count as verification. '
        'Do not write \u2713 Verified unless you have quoted the specific changed lines back. '
        'Do not proceed to the next edit until the user has seen the quoted content.'
    )
    print(json.dumps({'callback': msg}))

    # Increment session edit counter
    try:
        memory_dir = find_memory_dir()
        counter_file = memory_dir / 'tasks' / 'session_edit_count.txt'
        count = 0
        if counter_file.exists():
            try:
                count = int(counter_file.read_text(encoding='utf-8').strip())
            except Exception:
                count = 0
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        counter_file.write_text(str(count + 1), encoding='utf-8')
    except Exception:
        pass


# ─── QUICK LEARN ──────────────────────────────────────────────────────────────
# Fast lesson capture — fires a callback asking Claude to write lessons now.
# Use when /learn is too slow but you want to capture the session's insights.
# Run: python tools/memory.py --quick-learn

def cmd_quick_learn():
    memory_dir = find_memory_dir()
    today = datetime.now().strftime('%Y-%m-%d')
    context_parts = []

    draft_path = memory_dir / 'tasks' / 'draft-lessons.md'

    # Write a timestamped stub FIRST — so there's a record even if session closes before callback
    stub_entry = f'\n- [{today} QUICK-LEARN PENDING] Review session and fill in key lesson here'
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    with open(draft_path, 'a', encoding='utf-8') as f:
        f.write(stub_entry)

    # Surface any draft notes captured this session
    if draft_path.exists():
        draft_text = draft_path.read_text(encoding='utf-8', errors='ignore').strip()
        useful_lines = [l for l in draft_text.splitlines() if l.strip() and not l.startswith('#') and not l.startswith('_')]
        if useful_lines:
            context_parts.append('Draft notes from this session:\n' + '\n'.join(useful_lines))

    # Surface pending corrections queue
    queue_path = memory_dir / 'tasks' / 'corrections_queue.md'
    if queue_path.exists():
        q = queue_path.read_text(encoding='utf-8', errors='ignore')
        entries = re.findall(r'## \d{4}-\d{2}-\d{2} \d{2}:\d{2}\n\*\*Prompt:\*\* ".+?"', q)
        if entries:
            context_parts.append(f'{len(entries)} correction(s) captured:\n' + '\n'.join(entries))

    context_str = ('\n\n' + '\n\n'.join(context_parts)) if context_parts else ''
    msg = (
        f'Quick-learn triggered.{context_str}\n\n'
        f'Write 1-3 concise lessons to tasks/lessons.md right now. '
        f'Format each as: | {today} | short title | what to remember | '
        'No ceremony — just scan this session\'s work, capture the key pattern or gotcha, and done. '
        'Then replace the QUICK-LEARN PENDING stub in draft-lessons.md with what you actually learned, '
        'or delete it if you wrote directly to lessons.md. '
        'Then update STATUS.md session summary if anything changed.'
    )
    print(json.dumps({'callback': msg}))


# ─── KIT HEALTH ───────────────────────────────────────────────────────────────
# Checks that all memory kit components are present and wired correctly.
# Run: python tools/memory.py --kit-health

def cmd_kit_health():
    mem_dir = find_memory_dir()
    checks = []

    # MEMORY.md
    if (mem_dir / 'MEMORY.md').exists():
        checks.append(('PASS', 'MEMORY.md', 'exists'))
    else:
        checks.append(('FAIL', 'MEMORY.md', 'missing — memory index not found'))

    # STATUS.md
    status_md = ROOT / 'STATUS.md'
    if status_md.exists():
        checks.append(('PASS', 'STATUS.md', 'exists'))
    else:
        checks.append(('FAIL', 'STATUS.md', 'missing — session tracking not initialized'))

    # tasks/ directory
    tasks_dir = mem_dir / 'tasks'
    if tasks_dir.exists():
        checks.append(('PASS', 'tasks/', 'directory exists'))
    else:
        checks.append(('FAIL', 'tasks/', 'missing — run Setup Memory'))

    # settings.json hooks
    settings_paths = [
        ROOT / '.claude' / 'settings.json',
        ROOT / '.claude' / 'settings.local.json',
    ]
    settings_found = False
    hooks_wired = {'SessionStart': False, 'Stop': False, 'PostToolUse': False}
    for sp in settings_paths:
        if sp.exists():
            settings_found = True
            try:
                data = json.loads(sp.read_text(encoding='utf-8'))
                for event in hooks_wired:
                    if not hooks_wired[event] and event in data.get('hooks', {}):
                        hooks_wired[event] = True
            except Exception:
                pass
    if not settings_found:
        checks.append(('FAIL', 'settings.json', 'not found in .claude/ — hooks not wired'))
    else:
        for event, wired in hooks_wired.items():
            if wired:
                checks.append(('PASS', f'{event} hook', 'wired'))
            else:
                checks.append(('WARN', f'{event} hook', 'not found in settings.json'))

    # skills
    skills_dir = ROOT / '.claude' / 'skills'
    if skills_dir.exists():
        skill_names = sorted(d.name for d in skills_dir.iterdir() if d.is_dir() and (d / 'SKILL.md').exists())
        if skill_names:
            checks.append(('PASS', 'skills', f'{len(skill_names)} installed: {", ".join(skill_names)}'))
        else:
            checks.append(('WARN', 'skills', 'none installed — run "Generate Skills"'))
    else:
        checks.append(('WARN', 'skills', '.claude/skills/ not found'))

    # complexity profile
    if (mem_dir / 'complexity_profile.md').exists():
        checks.append(('PASS', 'complexity_profile.md', 'exists'))
    else:
        checks.append(('WARN', 'complexity_profile.md', 'missing — run Start Session to generate'))

    # lessons.md
    if (mem_dir / 'tasks' / 'lessons.md').exists():
        checks.append(('PASS', 'lessons.md', 'exists'))
    else:
        checks.append(('WARN', 'lessons.md', 'not yet created — run /learn after first session'))

    pass_count = sum(1 for s, _, _ in checks if s == 'PASS')
    fail_count = sum(1 for s, _, _ in checks if s == 'FAIL')
    warn_count = sum(1 for s, _, _ in checks if s == 'WARN')

    print(f'\nKit Health -- {pass_count} pass, {warn_count} warn, {fail_count} fail\n')
    for status, component, detail in checks:
        icon = '\u2713' if status == 'PASS' else ('!' if status == 'WARN' else 'X')
        print(f'  [{icon}] {component}: {detail}')

    if fail_count > 0:
        print('\nFix FAILs before proceeding -- memory may not load correctly.')
    elif warn_count > 0:
        print('\nWARNs are optional but recommended.')
    else:
        print('\nAll systems healthy.')


# ─── SHARED KEYWORD HELPER ───────────────────────────────────────────────────

_STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'it', 'its', 'be', 'was',
    'are', 'were', 'this', 'that', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
    'i', 'we', 'you', 'he', 'she', 'they', 'my', 'our', 'your', 'how',
    'what', 'when', 'where', 'which', 'who', 'not', 'no', 'so', 'if',
    'then', 'just', 'now', 'use', 'using', 'add', 'get', 'make', 'let',
}


def _extract_keywords(text, min_len=4):
    """Extract meaningful keywords from text, filtering stop words."""
    words = re.findall(r'\b[a-z][a-z0-9_-]{' + str(min_len - 1) + r',}\b', text.lower())
    return {w for w in words if w not in _STOP_WORDS}


def _parse_md_table_rows(text):
    """Yield non-header, non-divider rows from a markdown table as cell lists."""
    for line in text.splitlines():
        if not line.startswith('|') or '---' in line:
            continue
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if cells:
            yield cells


# ─── REGRET GUARD ────────────────────────────────────────────────────────────
# Scans regret.md + decisions.md for entries matching the current prompt.
# Hook: UserPromptSubmit

def _log_guard_fire(memory_dir, guard_name, matches):
    """Mechanically write to memory_assist.md when a guard fires. No Claude involvement."""
    try:
        assist_path = memory_dir / 'tasks' / 'memory_assist.md'
        assist_path.parent.mkdir(parents=True, exist_ok=True)
        if not assist_path.exists():
            assist_path.write_text(
                '# Memory Assist Log\n'
                'Auto-written by guard hooks — ground truth record of when memory prevented a mistake.\n\n',
                encoding='utf-8'
            )
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        first_match = matches[0][:100] if matches else '(unknown)'
        line = f'- [{now}] {guard_name} fired — matched: "{first_match}"\n'
        with open(assist_path, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass


def cmd_regret_guard():
    """Scan regret.md + decisions.md for keyword matches to the current prompt."""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        prompt = data.get('prompt', '').strip()
    except Exception:
        return

    if len(prompt) < 20:
        return

    prompt_keywords = _extract_keywords(prompt)
    if not prompt_keywords:
        return

    memory_dir = find_memory_dir()
    matches = []

    for filename, label in [('tasks/regret.md', 'Rejected'), ('decisions.md', 'Decided')]:
        md_path = memory_dir / filename
        if not md_path.exists():
            continue
        text = md_path.read_text(encoding='utf-8', errors='ignore')
        for cells in _parse_md_table_rows(text):
            # Skip header rows
            if cells[0].lower() in ('approach', 'decision', 'what', 'rule'):
                continue
            entry_text = ' '.join(cells)
            entry_keywords = _extract_keywords(entry_text)
            overlap = prompt_keywords & entry_keywords
            if len(overlap) >= 2:
                approach = cells[0][:80]
                reason = cells[1][:120] if len(cells) > 1 else ''
                matches.append(f'[{label}] {approach} — {reason}')

    if not matches:
        return

    warning = (
        '\u26a0 REGRET GUARD — Past decisions match your current task:\n'
        + '\n'.join(f'  \u2022 {m}' for m in matches[:5])
        + '\nVerify this approach is not already rejected before proceeding.'
    )

    # Ground-truth write — Python writes directly, no Claude involvement
    _log_guard_fire(memory_dir, 'REGRET GUARD', matches)

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': warning
        }
    }
    print(json.dumps(output))


# ─── DECISION GUARD ──────────────────────────────────────────────────────────
# Checks proposed approaches against decisions.md before a plan is shown.
# Hook: UserPromptSubmit (fires when planning language is detected)

_PLANNING_PATTERNS = [
    r'(?i)\bplan\b', r'(?i)\bbuild\b', r'(?i)\bimplement\b',
    r'(?i)\badd\b.{0,30}\bfeature\b', r'(?i)\bcreate\b',
    r'(?i)\brefactor\b', r'(?i)\bchange\b.{0,20}\bto\b',
    r'(?i)\bswitch\b.{0,20}\bto\b', r'(?i)\breplace\b', r'(?i)\bupdate\b',
]


def _is_planning_prompt(prompt):
    return any(re.search(p, prompt) for p in _PLANNING_PATTERNS)


def cmd_decision_guard():
    """Check prompt against decisions.md — warn if it contradicts a settled decision."""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        prompt = data.get('prompt', '').strip()
    except Exception:
        return

    if len(prompt) < 15 or not _is_planning_prompt(prompt):
        return

    prompt_keywords = _extract_keywords(prompt, min_len=3)
    if not prompt_keywords:
        return

    memory_dir = find_memory_dir()
    decisions_path = memory_dir / 'decisions.md'
    if not decisions_path.exists():
        return

    text = decisions_path.read_text(encoding='utf-8', errors='ignore')
    conflicts = []

    for cells in _parse_md_table_rows(text):
        if cells[0].lower() in ('decision', 'approach', 'what', 'rule'):
            continue
        entry_keywords = _extract_keywords(' '.join(cells), min_len=3)
        overlap = prompt_keywords & entry_keywords
        if len(overlap) >= 2:
            decision = cells[0][:80]
            reason = cells[1][:120] if len(cells) > 1 else ''
            conflicts.append(f'{decision} — {reason}')

    if not conflicts:
        return

    warning = (
        'DECISION GUARD — Settled decisions relevant to this task:\n'
        + '\n'.join(f'  \u2022 {c}' for c in conflicts[:4])
        + '\nConfirm this approach does not re-litigate a closed decision.'
    )

    # Ground-truth write — Python writes directly, no Claude involvement
    _log_guard_fire(memory_dir, 'DECISION GUARD', conflicts)

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': warning
        }
    }
    print(json.dumps(output))


# ─── CONTEXT EFFICIENCY SCORE ─────────────────────────────────────────────────
# Scores CLAUDE.md sections by how often their keywords appear in session journals.
# Run: python tools/memory.py --context-score

def cmd_context_score():
    """Score CLAUDE.md sections by usage frequency in session journals."""
    claude_md = ROOT / 'CLAUDE.md'
    if not claude_md.exists():
        print('CLAUDE.md not found.')
        return

    memory_dir = find_memory_dir()
    journal_path = memory_dir / 'session_journal.md'
    journal_text = journal_path.read_text(encoding='utf-8', errors='ignore').lower() if journal_path.exists() else ''

    text = claude_md.read_text(encoding='utf-8', errors='ignore')
    sections = re.findall(r'^## (.+)$', text, re.MULTILINE)

    if not sections:
        print('No ## sections found in CLAUDE.md.')
        return

    if not journal_text:
        print('No session_journal.md found — run a few sessions first to build history.')
        return

    results = []
    for section in sections:
        keywords = _extract_keywords(section, min_len=3) or {section.lower()}
        hits = sum(1 for kw in keywords if kw in journal_text)
        results.append((hits, section))

    results.sort(reverse=True)

    print('\nContext Efficiency Score\n')
    print(f'  {"Section":<42} {"Signal":>8}')
    print('  ' + '-' * 54)
    for score, section in results:
        bar = '#' * min(score, 10) + '.' * max(0, 10 - score)
        tag = '  <- low signal' if score == 0 else ''
        print(f'  {section[:42]:<42} [{bar}]{tag}')

    low = [s for sc, s in results if sc == 0]
    print(f'\n{len(low)} section(s) with zero journal signal.')
    if low:
        print('These may be dead weight in your context:')
        for s in low:
            print(f'  - {s}')


# ─── VELOCITY-HONEST ESTIMATES ────────────────────────────────────────────────
# Reads velocity.md and matches the current task to past entries.
# Run: python tools/memory.py --velocity-estimate "task description"

def cmd_velocity_estimate():
    """Match task description to past velocity entries and report honest estimates."""
    args_list = sys.argv[1:]
    try:
        idx = args_list.index('--velocity-estimate')
        task_desc = ' '.join(args_list[idx + 1:]).strip()
    except (ValueError, IndexError):
        task_desc = ''

    if not task_desc:
        print('Usage: memory.py --velocity-estimate "task description"')
        return

    memory_dir = find_memory_dir()
    velocity_path = memory_dir / 'tasks' / 'velocity.md'
    if not velocity_path.exists():
        print('velocity.md not found — no history yet.')
        return

    text = velocity_path.read_text(encoding='utf-8', errors='ignore')
    task_keywords = _extract_keywords(task_desc, min_len=3)
    entries = []

    for cells in _parse_md_table_rows(text):
        if not cells or cells[0].lower() in ('task', 'feature', 'item'):
            continue
        task_name = cells[0]
        estimated = cells[1] if len(cells) > 1 else '?'
        actual = cells[2] if len(cells) > 2 else '?'
        overlap = task_keywords & _extract_keywords(task_name, min_len=3)
        if overlap:
            entries.append((len(overlap), task_name, estimated, actual))

    if not entries:
        print(f'No past tasks similar to: "{task_desc}"')
        print('Keep logging tasks via /learn to build your velocity history.')
        return

    entries.sort(reverse=True)
    top = entries[:5]

    actuals = []
    for _, _, _, actual in top:
        nums = re.findall(r'\d+', actual)
        if nums:
            actuals.append(int(nums[0]))

    print(f'\nVelocity Estimate — "{task_desc}"\n')
    print(f'  {"Similar past task":<45} {"Est":>5} {"Actual":>8}')
    print('  ' + '-' * 62)
    for _, task, est, actual in top:
        print(f'  {task[:45]:<45} {est:>5} {actual:>8}')

    if actuals:
        avg = sum(actuals) / len(actuals)
        print(f'\nAverage actual: {avg:.1f} sessions')
        print(f'Plan for at least {int(avg) + 1} — history says estimates run short.')
    else:
        print('\nCould not parse session counts from velocity entries.')


# ─── CROSS-SESSION PATTERN MINING ────────────────────────────────────────────
# Clusters lessons.md entries to surface recurring mistakes.
# Run: python tools/memory.py --mine-patterns

def cmd_mine_patterns():
    """Cluster lessons.md entries to surface recurring patterns across sessions."""
    memory_dir = find_memory_dir()
    lessons_path = memory_dir / 'tasks' / 'lessons.md'
    if not lessons_path.exists():
        print('lessons.md not found — run /learn after a few sessions.')
        return

    text = lessons_path.read_text(encoding='utf-8', errors='ignore')
    lessons = []
    for cells in _parse_md_table_rows(text):
        if cells[0].lower() in ('date', 'session', 'when'):
            continue
        lesson_text = ' '.join(cells[1:]) if len(cells) > 1 else cells[0]
        lessons.append(lesson_text)

    if len(lessons) < 5:
        print(f'Only {len(lessons)} lessons so far — need at least 5 to mine patterns. Keep using /learn.')
        return

    # Map keywords to matching lessons
    keyword_to_lessons = {}
    for lesson in lessons:
        for kw in _extract_keywords(lesson, min_len=4):
            keyword_to_lessons.setdefault(kw, []).append(lesson)

    # Keep only keywords appearing in 3+ distinct lessons
    recurring = {kw: ls for kw, ls in keyword_to_lessons.items() if len(ls) >= 3}

    if not recurring:
        print(f'Analyzed {len(lessons)} lessons — no recurring patterns yet (need same topic in 3+ lessons).')
        return

    ranked = sorted(recurring.items(), key=lambda x: -len(x[1]))

    print(f'\nCross-Session Pattern Mining — {len(lessons)} lessons analyzed\n')
    shown = set()
    count = 0
    for kw, matched in ranked[:10]:
        unique = [l for l in matched if l not in shown]
        if not unique:
            continue
        count += 1
        print(f'  Pattern: "{kw}" ({len(matched)} occurrences)')
        for l in unique[:2]:
            print(f'    \u2022 {l[:100]}')
            shown.add(l)
        print()

    if count == 0:
        print('No distinct patterns after deduplication.')
        return

    print('Consider converting top patterns to permanent rules in decisions.md or CLAUDE.md.')


# ─── ERROR LOOKUP ────────────────────────────────────────────────────────────
# Scans error-lookup.md for known errors matching the current debug prompt.
# Hook: UserPromptSubmit

_DEBUG_PATTERNS = [
    r'(?i)\berror\b', r'(?i)\bbug\b', r'(?i)\bbroken\b',
    r"(?i)doesn't work", r'(?i)not working', r'(?i)\bfailing\b',
    r'(?i)\bexception\b', r'(?i)\bcrash\b', r'(?i)\bfix\b',
    r'(?i)\bdebug\b', r'(?i)why is\b', r'(?i)why does\b',
    r'(?i)\b500\b', r'(?i)\b404\b', r"(?i)can't\b",
]


def _is_debug_prompt(prompt):
    return any(re.search(p, prompt) for p in _DEBUG_PATTERNS)


def cmd_error_lookup():
    """Scan error-lookup.md for known entries matching the current debug prompt."""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        prompt = data.get('prompt', '').strip()
    except Exception:
        return

    if len(prompt) < 10 or not _is_debug_prompt(prompt):
        return

    prompt_keywords = _extract_keywords(prompt, min_len=3)
    if not prompt_keywords:
        return

    memory_dir = find_memory_dir()
    lookup_path = memory_dir / 'error-lookup.md'
    if not lookup_path.exists():
        return

    text = lookup_path.read_text(encoding='utf-8', errors='ignore')
    matches = []

    for cells in _parse_md_table_rows(text):
        if cells[0].lower() in ('error message', 'symptom', 'error', 'issue'):
            continue
        entry_text = ' '.join(cells)
        entry_keywords = _extract_keywords(entry_text, min_len=3)
        overlap = prompt_keywords & entry_keywords
        if len(overlap) >= 2:
            error = cells[0][:80]
            fix = cells[2][:120] if len(cells) > 2 else (cells[1][:120] if len(cells) > 1 else '')
            matches.append(f'{error} \u2192 {fix}')

    if not matches:
        return

    hint = (
        '\U0001f4cb ERROR LOOKUP \u2014 Known matches for this error:\n'
        + '\n'.join(f'  \u2022 {m}' for m in matches[:4])
        + '\nCheck error-lookup.md for full cause + fix before investigating from scratch.'
    )

    output = {
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': hint
        }
    }
    print(json.dumps(output))


# ─── GUARD CHECK ─────────────────────────────────────────────────────────────
# Runs all named guards from guard-patterns.md against the codebase.
# Run: python tools/memory.py --guard-check

def cmd_guard_check():
    """Scan codebase against all named guards in .claude/rules/guard-patterns.md."""
    guard_path = ROOT / '.claude' / 'rules' / 'guard-patterns.md'
    if not guard_path.exists():
        print('guard-patterns.md not found in .claude/rules/')
        print('Run "Install Guard Patterns" or create .claude/rules/guard-patterns.md manually.')
        return

    text = guard_path.read_text(encoding='utf-8', errors='ignore')
    guards = re.findall(r'^## (\w+)\n(.*?)(?=^## |\Z)', text, re.MULTILINE | re.DOTALL)

    if not guards:
        print('No guards found in guard-patterns.md.')
        return

    print(f'\nGuard Check \u2014 {len(guards)} guards\n')
    violations = 0

    for guard_id, body in guards:
        grep_match = re.search(r'\*\*How to scan\*\*:\s*(.+?)(?:\n|$)', body)
        files_match = re.search(r'\*\*Files\*\*:\s*(.+?)(?:\n|$)', body)
        check_match = re.search(r'\*\*Check\*\*:\s*(.+?)(?:\n|$)', body)

        if not grep_match:
            print(f'  [SKIP] {guard_id} \u2014 no scan strategy defined')
            continue

        grep_desc = grep_match.group(1).strip()
        files_scope = files_match.group(1).strip() if files_match else 'all files'
        check_desc = check_match.group(1).strip() if check_match else guard_id

        # Extract backtick-wrapped regex from the scan description
        pattern_match = re.search(r'`([^`]+)`', grep_desc)
        if not pattern_match:
            print(f'  [SKIP] {guard_id} \u2014 manual check required: {check_desc}')
            continue

        grep_pattern = pattern_match.group(1)
        exclude_tests = 'exclude test' in files_scope.lower()
        hits = []

        for path in sorted(ROOT.rglob('*')):
            if not path.is_file():
                continue
            if any(ex in path.parts for ex in _EXCLUDE_DIRS):
                continue
            if path.suffix.lower() not in ('.js', '.ts', '.py', '.java', '.go', '.rb', '.cs', '.jsx', '.tsx', '.vue'):
                continue
            if exclude_tests and any(t in path.name.lower() for t in ('test', 'spec')):
                continue
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                for lineno, line in enumerate(content.splitlines(), 1):
                    if re.search(grep_pattern, line, re.IGNORECASE):
                        hits.append(f'{path.relative_to(ROOT)}:{lineno}')
                        break
            except Exception:
                continue

        if hits:
            violations += 1
            print(f'  [FAIL] {guard_id}')
            print(f'         {check_desc}')
            for hit in hits[:5]:
                print(f'         \u2192 {hit}')
            if len(hits) > 5:
                print(f'         ... and {len(hits) - 5} more')
        else:
            print(f'  [PASS] {guard_id}')

    print(f'\n{violations} violation(s) found.')
    if violations:
        print('Fix before committing. Add to error-lookup.md if this was a runtime surprise.')


# ─── SUGGEST GUARDS ──────────────────────────────────────────────────────────
# PostToolUse hook: fires when error-lookup.md is edited.
# Prompts Claude to offer Generate Guards — turns every debug into prevention.
# Hook: PostToolUse (Edit|Write)

def cmd_suggest_guards():
    """PostToolUse: if error-lookup.md was just written, prompt Claude to offer Generate Guards."""
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            fp = payload.get('tool_input', {}).get('file_path', '')
            if 'error-lookup' not in fp.replace('\\', '/').lower():
                return  # Not error-lookup.md — silent exit
    except Exception:
        return

    memory_dir = find_memory_dir()
    error_count = 0
    error_path = memory_dir / 'error-lookup.md'
    if error_path.exists():
        rows = _parse_md_table_rows(error_path.read_text(encoding='utf-8', errors='ignore'))
        error_count = sum(1 for r in rows if r and r[0].lower() not in ('error', 'error message', 'symptom', 'issue'))

    msg = (
        f'error-lookup.md updated ({error_count} known error(s) now logged). '
        'REQUIRED: Offer to run Generate Guards. '
        'Say exactly: "Error logged. Run Generate Guards to turn this into automated prevention? '
        'I can scan your full error history and propose guards in about 30 seconds — '
        'catches this class of mistake before it ships. Say yes to run it now." '
        'Do not skip this offer.'
    )
    print(json.dumps({'callback': msg}))


# ─── PROGRESS REPORT ──────────────────────────────────────────────────────────
# Shows how Claude has improved across sessions.
# Run: python tools/memory.py --progress-report

def cmd_progress_report():
    """Show compounding metrics across all sessions: lessons, errors known, skill accuracy, velocity data."""
    memory_dir = find_memory_dir()

    # Session count + last 3 from session_journal.md
    session_count = 0
    last_sessions = []
    journal_path = memory_dir / 'session_journal.md'
    if journal_path.exists():
        text = journal_path.read_text(encoding='utf-8', errors='ignore')
        entries = re.findall(
            r'## \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\n'
            r'\*\*Files:\*\* .+?\n'
            r'\*\*Edits:\*\* (.+?) \|.+?\n'
            r'\*\*What:\*\* (.+?)(?:\n|$)',
            text
        )
        session_count = len(entries)
        for dt, edits, what in entries[-3:]:
            last_sessions.append((dt, what.strip(), edits.strip()))

    # Lessons count
    lesson_count = 0
    for lpath in [memory_dir / 'tasks' / 'lessons.md', memory_dir / 'lessons.md']:
        if lpath.exists():
            rows = _parse_md_table_rows(lpath.read_text(encoding='utf-8', errors='ignore'))
            lesson_count = sum(1 for r in rows if r and r[0].lower() not in ('date', 'session', 'when', 'title'))
            break

    # Known errors count
    error_count = 0
    error_path = memory_dir / 'error-lookup.md'
    if error_path.exists():
        rows = _parse_md_table_rows(error_path.read_text(encoding='utf-8', errors='ignore'))
        error_count = sum(1 for r in rows if r and r[0].lower() not in ('error', 'error message', 'symptom', 'issue'))

    # Skill accuracy from skill_scores.md
    yes_count = 0
    no_count = 0
    scores_path = memory_dir / 'tasks' / 'skill_scores.md'
    if scores_path.exists():
        text = scores_path.read_text(encoding='utf-8', errors='ignore')
        yes_count = len(re.findall(r'\|\s*[Yy]\s*\|', text))
        no_count = len(re.findall(r'\|\s*[Nn]\s*\|', text))

    # Velocity data points
    velocity_count = 0
    vel_path = memory_dir / 'tasks' / 'velocity.md'
    if vel_path.exists():
        rows = _parse_md_table_rows(vel_path.read_text(encoding='utf-8', errors='ignore'))
        velocity_count = sum(1 for r in rows if r and r[0].lower() not in ('task', 'feature', 'item'))

    # Rejected approaches
    regret_count = 0
    regret_path = memory_dir / 'tasks' / 'regret.md'
    if regret_path.exists():
        rows = _parse_md_table_rows(regret_path.read_text(encoding='utf-8', errors='ignore'))
        regret_count = sum(1 for r in rows if r and r[0].lower() not in ('approach', 'what was tried', 'rejected'))

    print('\n=== Clankbrain Progress Report ===\n')

    if session_count == 0:
        print('  No sessions logged yet.')
        print('  Run /learn after your first session to start tracking.')
        print('  This report fills in as you use Start Session / End Session.\n')
        return

    total_uses = yes_count + no_count
    if total_uses > 0:
        accuracy_str = f'{int(100 * yes_count / total_uses)}%  ({yes_count} correct / {no_count} needed correction)'
    else:
        accuracy_str = 'not yet scored  (run /learn to start scoring skills)'

    print(f'  Sessions logged         {session_count}')
    print(f'  Lessons accumulated     {lesson_count}'
          + ('  ← run /mine-patterns to cluster these' if lesson_count >= 5 else ''))
    print(f'  Known errors logged     {error_count}'
          + ('  ← debug-session stops repeating these' if error_count > 0 else '  ← grows as you use debug-session'))
    print(f'  Rejected approaches     {regret_count}'
          + ('  ← regret-guard blocks re-proposing these' if regret_count > 0 else ''))
    print(f'  Skill accuracy          {accuracy_str}')
    print(f'  Velocity data points    {velocity_count}'
          + ('  ← estimates self-calibrate from these' if velocity_count >= 5 else ''))

    if last_sessions:
        print('\n  Last 3 sessions:')
        for dt, what, edits in last_sessions:
            print(f'    [{dt}]  {what[:55]:<55}  ({edits})')

    print()
    if lesson_count == 0 and error_count == 0 and session_count < 3:
        print('  → Just getting started. The report fills in fast — 3 sessions changes it.')
    elif session_count >= 10:
        print(f'  → {session_count} sessions deep. This is a compounding system now.')
        if no_count > yes_count:
            print('  → Corrections outnumber passes — run /evolve to patch the weak skills.')
    else:
        remaining = max(0, 5 - session_count)
        if remaining > 0:
            print(f'  → {remaining} more session(s) until --mine-patterns has enough signal.')
    print()


# ─── LOG EDIT ─────────────────────────────────────────────────────────────────
# Appends "Edited: <filename>" to draft-lessons.md so the session journal can
# report which files were touched without relying on Claude's memory.
# Hook: PostToolUse (Edit|Write), async

def cmd_log_edit():
    try:
        raw = sys.stdin.read()
        if not raw:
            return
        payload = json.loads(raw)
        tool_input = payload.get('tool_input', {})
        file_path = tool_input.get('file_path', '')
        if not file_path:
            return
        filename = Path(file_path).name
        memory_dir = find_memory_dir()
        draft = memory_dir / 'tasks' / 'draft-lessons.md'
        draft.parent.mkdir(parents=True, exist_ok=True)
        if not draft.exists():
            draft.write_text(
                '# Draft Lessons (auto-tracked edits)\n'
                '_Run /learn to extract patterns from these._\n',
                encoding='utf-8'
            )
        existing = draft.read_text(encoding='utf-8')
        entry = f'- Edited: {filename}\n'
        if entry not in existing:
            with open(draft, 'a', encoding='utf-8') as f:
                f.write(entry)
    except Exception:
        pass


# ─── CHECK EXPIRY ─────────────────────────────────────────────────────────────
# Scans memory files for expires/valid_until/valid_from frontmatter.
# Expired → surface as stale. valid_from in future → surface as not-yet-active.
# Hook: SessionStart (silent)

def cmd_check_expiry():
    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        return
    today = datetime.now().date()
    expired = []
    not_yet_valid = []
    for md_file in sorted(memory_dir.rglob('*.md')):
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            # expires OR valid_until
            m = re.search(r'^(?:expires|valid_until):\s*(\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
            if m:
                exp_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
                if exp_date < today:
                    rel = md_file.relative_to(memory_dir)
                    expired.append((str(rel), m.group(1)))
            # valid_from — memory not yet applicable
            m2 = re.search(r'^valid_from:\s*(\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
            if m2:
                start_date = datetime.strptime(m2.group(1), '%Y-%m-%d').date()
                if start_date > today:
                    rel = md_file.relative_to(memory_dir)
                    not_yet_valid.append((str(rel), m2.group(1)))
        except Exception:
            continue
    msgs = []
    if expired:
        lines = [f'- {f} (expired {d})' for f, d in expired]
        msgs.append('Stale memories — review or remove:\n' + '\n'.join(lines))
    if not_yet_valid:
        lines = [f'- {f} (active from {d})' for f, d in not_yet_valid]
        msgs.append('Memories not yet active — do not apply yet:\n' + '\n'.join(lines))
    if msgs:
        print(json.dumps({'systemMessage': '\n\n'.join(msgs)}))


# ─── PERMISSION DENIED ────────────────────────────────────────────────────────
# Logs denied tool operations so they surface at End Session.
# Hook: PermissionRequest

def cmd_permission_denied():
    memory_dir = find_memory_dir()
    denial_log = memory_dir / 'tasks' / 'permission_denials.md'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    tool_name = ''
    detail = ''
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            tool_name = payload.get('tool_name', payload.get('tool', ''))
            detail = payload.get('reason', payload.get('description', payload.get('input', {}).get('command', '')))
    except Exception:
        pass

    entry = f'- {timestamp} | {tool_name} | {detail}\n'
    try:
        denial_log.parent.mkdir(parents=True, exist_ok=True)
        if not denial_log.exists():
            denial_log.write_text('# Permission Denials\n_Auto-logged by PermissionRequest hook. Review at End Session._\n\n', encoding='utf-8')
        with open(denial_log, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass

    if tool_name and not SILENT:
        print(f'[kit] Permission denied: {tool_name} — logged to tasks/permission_denials.md')


# ─── SESSION TITLE ────────────────────────────────────────────────────────────
# Returns hookSpecificOutput.sessionTitle for the Claude Code status bar.
# Hook: UserPromptSubmit (with refreshInterval: 60)

def cmd_session_title():
    memory_dir = find_memory_dir()
    title = 'Clankbrain'
    status_msg = ''
    try:
        status_file = memory_dir / 'STATUS.md'
        if status_file.exists():
            lines = status_file.read_text(encoding='utf-8').splitlines()
            for line in lines:
                if line.startswith('Session') or 'Session' in line[:20]:
                    title = line.strip()[:50]
                    break
    except Exception:
        pass

    try:
        # Count open plans
        plans_dir = memory_dir / 'plans'
        open_plans = 0
        if plans_dir.exists():
            for f in plans_dir.glob('*.md'):
                if 'archive' in str(f).lower():
                    continue
                text = f.read_text(encoding='utf-8')
                if 'Status: In Progress' in text or 'Status: Draft' in text or 'Status: On Hold' in text:
                    open_plans += 1

        # Count open todos
        open_todos = 0
        todo_file = memory_dir / 'todo.md'
        if todo_file.exists():
            todo_text = todo_file.read_text(encoding='utf-8')
            open_todos = todo_text.count('- [ ]')

        parts = []
        if open_plans:
            parts.append(f'{open_plans} plan{"s" if open_plans != 1 else ""}')
        if open_todos:
            parts.append(f'{open_todos} todo{"s" if open_todos != 1 else ""}')
        status_msg = ' | '.join(parts) if parts else 'All clear'
    except Exception:
        status_msg = ''

    out = {
        'hookSpecificOutput': {'sessionTitle': title},
        'statusMessage': status_msg,
    }
    print(json.dumps(out))


# ─── FILE CHANGED ─────────────────────────────────────────────────────────────
# Alerts when CLAUDE.md or memory files change outside Claude Code.
# Hook: FileChanged

def cmd_file_changed():
    changed_file = ''
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            changed_file = payload.get('file', payload.get('file_path', payload.get('path', '')))
    except Exception:
        pass

    if not changed_file:
        return

    cf = changed_file.replace('\\', '/')
    is_claude_md = cf.endswith('CLAUDE.md')
    is_memory_file = '/memory/' in cf or cf.endswith('/MEMORY.md')

    if not (is_claude_md or is_memory_file):
        return

    if is_claude_md:
        msg = 'CLAUDE.md changed externally — run Check Drift to verify memory is current.'
    else:
        fname = Path(changed_file).name
        msg = f'Memory file changed externally: {fname} — run Check Drift if unexpected.'

    print(json.dumps({'systemMessage': f'[kit] {msg}'}))


# ─── PRE-EDIT GUARD ──────────────────────────────────────────────────────────
# Fires before any Edit/Write — surfaces lessons/regret/decisions for the file.
# Hook: PreToolUse (matcher: Edit|Write)

def _scan_sections(text, stem_lower, label, matches, seen):
    """Scan free-text ## section format — used by lessons.md and decisions.md."""
    current_title = None
    current_body = []
    for line in text.splitlines():
        if line.startswith('## '):
            if current_title and stem_lower in '\n'.join(current_body).lower():
                key = current_title[:60]
                if key not in seen:
                    seen.add(key)
                    matches.append(f'[{label}] {current_title[:100]}')
            current_title = line.lstrip('#').strip()
            current_body = []
        else:
            current_body.append(line)
    # Flush last section
    if current_title and stem_lower in '\n'.join(current_body).lower():
        key = current_title[:60]
        if key not in seen:
            seen.add(key)
            matches.append(f'[{label}] {current_title[:100]}')


def _parse_frontmatter(text):
    """Return dict of frontmatter key: value from a memory file."""
    fm = {}
    if not text.startswith('---'):
        return fm
    end = text.find('\n---', 3)
    if end == -1:
        return fm
    block = text[3:end]
    for line in block.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip()
    return fm


def _follow_related(memory_dir, matched_files, seen_files, matches, seen):
    """Follow related: links one level deep — the Tunnels concept."""
    for md_file in matched_files:
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            fm = _parse_frontmatter(text)
            related_raw = fm.get('related', '')
            if not related_raw:
                continue
            # related: [file1.md, file2.md]  or  related: file1.md
            related_raw = related_raw.strip('[]')
            for rname in related_raw.split(','):
                rname = rname.strip().strip('"\'')
                if not rname:
                    continue
                rpath = memory_dir / rname
                if not rpath.exists() or rpath in seen_files:
                    continue
                seen_files.add(rpath)
                rtext = rpath.read_text(encoding='utf-8', errors='ignore')
                rfm = _parse_frontmatter(rtext)
                rname_val = rfm.get('name', rpath.stem)
                # Surface first non-frontmatter, non-empty line as the snippet
                body_lines = [l for l in rtext.splitlines() if l.strip() and not l.startswith('-') and not l.startswith('#')]
                snippet = body_lines[0][:100] if body_lines else rname_val
                key = snippet[:60]
                if key not in seen:
                    seen.add(key)
                    matches.append(f'[Tunnel→{rname_val}] {snippet}')
        except Exception:
            continue


def cmd_pre_edit():
    """PreToolUse hook: surface relevant memory before editing a file."""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        tool_input = data.get('tool_input', {})
        file_path = tool_input.get('file_path', tool_input.get('path', ''))
    except Exception:
        return

    if not file_path:
        return

    stem = Path(file_path).stem
    if len(stem) < 5:
        return

    stem_lower = stem.lower()
    memory_dir = find_memory_dir()
    matches = []
    seen = set()
    matched_files = []  # track files that matched, for related: tunnel following

    # 1. Scan aggregate memory files (lessons, regret, decisions)
    for filename, label in [
        ('lessons.md',       'Lesson'),
        ('tasks/regret.md',  'Regret'),
        ('decisions.md',     'Decision'),
    ]:
        md_path = memory_dir / filename
        if not md_path.exists():
            continue
        text = md_path.read_text(encoding='utf-8', errors='ignore')

        for cells in _parse_md_table_rows(text):
            if not cells or cells[0].lower() in (
                'approach', 'decision', 'what', 'rule', 'lesson', 'date', 'description'
            ):
                continue
            entry = ' '.join(cells)
            if stem_lower not in entry.lower():
                continue
            key = entry[:60]
            if key in seen:
                continue
            seen.add(key)
            snippet = cells[0][:80]
            detail = cells[1][:90] if len(cells) > 1 else ''
            matches.append(f'[{label}] {snippet}' + (f' — {detail}' if detail else ''))

        _scan_sections(text, stem_lower, label, matches, seen)

    # 2. Scan individual memory files — enables related: tunnel following
    today = datetime.now().date()
    for md_file in sorted(memory_dir.glob('*.md')):
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            if stem_lower not in text.lower():
                continue
            fm = _parse_frontmatter(text)
            # Skip expired or not-yet-valid memories
            valid_until = fm.get('valid_until', fm.get('expires', ''))
            if valid_until:
                try:
                    if datetime.strptime(valid_until, '%Y-%m-%d').date() < today:
                        continue
                except ValueError:
                    pass
            valid_from = fm.get('valid_from', '')
            if valid_from:
                try:
                    if datetime.strptime(valid_from, '%Y-%m-%d').date() > today:
                        continue
                except ValueError:
                    pass
            mtype = fm.get('type', '')
            mname = fm.get('name', md_file.stem)
            label = f'{mtype.capitalize()}' if mtype else 'Memory'
            # Surface first meaningful body line
            body_lines = [l for l in text.splitlines()
                          if l.strip() and not l.startswith('-') and not l.startswith('#') and ':' not in l[:20]]
            snippet = body_lines[0][:100] if body_lines else mname
            key = snippet[:60]
            if key not in seen:
                seen.add(key)
                matches.append(f'[{label}] {snippet}')
                matched_files.append(md_file)
        except Exception:
            continue

    # 3. Follow related: links one level (Tunnels)
    seen_files = set(matched_files)
    _follow_related(memory_dir, matched_files, seen_files, matches, seen)

    # Content-based regret match — mechanical log if proposed edit matches a rejected approach
    try:
        proposed = tool_input.get('new_string', '') + tool_input.get('content', '')
        if proposed and len(proposed) > 20:
            regret_path = memory_dir / 'tasks' / 'regret.md'
            if regret_path.exists():
                regret_text = regret_path.read_text(encoding='utf-8', errors='ignore')
                proposed_kw = _extract_keywords(proposed)
                content_matches = []
                for cells in _parse_md_table_rows(regret_text):
                    if not cells or cells[0].lower() in ('approach', 'rule', 'what'):
                        continue
                    entry_kw = _extract_keywords(' '.join(cells))
                    if len(proposed_kw & entry_kw) >= 2:
                        content_matches.append(cells[0][:80])
                if content_matches:
                    _log_guard_fire(memory_dir, 'PRE-EDIT REGRET MATCH', content_matches)
    except Exception:
        pass

    if not matches:
        return

    fname = Path(file_path).name
    msg = (
        f'Before editing {fname}:\n'
        + '\n'.join(f'  - {m}' for m in matches[:8])
    )
    print(json.dumps({'systemMessage': f'[kit] {msg}'}))


# ─── POST READ — MEMORY FILE CONSULTATION LOGGER ─────────────────────────────
# Fires PostToolUse on Read|Grep. If Claude read a memory file, log it.
# Hook: PostToolUse (Read|Grep)

def cmd_post_read():
    """Log when Claude actively consults a memory file mid-session."""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        tool_input = data.get('tool_input', {})
        file_path = tool_input.get('file_path', tool_input.get('path', ''))
        pattern   = tool_input.get('pattern', '')   # Grep
    except Exception:
        return

    memory_dir = find_memory_dir()
    if not memory_dir:
        return

    _MEMORY_FILES = {
        'lessons.md', 'decisions.md', 'regret.md',
        'session_journal.md', 'complexity_profile.md',
    }

    target = file_path or pattern
    if not target:
        return

    name = Path(target).name if file_path else ''
    # Match if it's a known memory file or lives inside memory_dir
    is_memory = (
        name in _MEMORY_FILES
        or (file_path and str(memory_dir) in file_path.replace('\\', '/'))
    )
    if not is_memory:
        return

    label = f'MEMORY READ ({name or "grep"} consulted mid-session)'
    _log_guard_fire(memory_dir, label, [target])


# ─── MEMPALACE AUDIT ──────────────────────────────────────────────────────────
# Scans memory files and flags: missing ## Source, state-type without valid_until,
# no frontmatter at all. Run manually or wire to a periodic hook.

def cmd_mempalace_audit():
    memory_dir = find_memory_dir()
    if not memory_dir.exists():
        print('No memory directory found.')
        return

    no_source = []
    no_expiry = []
    no_frontmatter = []

    for md_file in sorted(memory_dir.glob('*.md')):
        if md_file.name in ('MEMORY.md', 'STATUS.md', 'lessons.md', 'decisions.md'):
            continue
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            fm = _parse_frontmatter(text)

            if not fm:
                no_frontmatter.append(md_file.name)
                continue

            mtype = fm.get('type', '')

            # Source block check — all memory files should have verbatim context
            if '## Source' not in text and '## source' not in text:
                no_source.append(f'{md_file.name} (type: {mtype or "?"})')

            # Temporal validity check — state/project memories should expire
            if mtype in ('state', 'project') and not fm.get('valid_until') and not fm.get('expires'):
                no_expiry.append(f'{md_file.name} — add valid_until: YYYY-MM-DD')

        except Exception:
            continue

    issues = []
    if no_frontmatter:
        issues.append('No frontmatter (add ---name/type/description---):\n'
                      + '\n'.join(f'  {f}' for f in no_frontmatter))
    if no_source:
        issues.append('Missing ## Source block (add verbatim context for better recall):\n'
                      + '\n'.join(f'  {f}' for f in no_source))
    if no_expiry:
        issues.append('State/project memories without valid_until (will never expire):\n'
                      + '\n'.join(f'  {f}' for f in no_expiry))

    if issues:
        print('=== MemPalace Audit ===')
        for issue in issues:
            print(issue)
        print(f'\n{len(no_frontmatter)} missing frontmatter | {len(no_source)} missing Source | {len(no_expiry)} missing valid_until')
    else:
        print('MemPalace audit: all memory files pass.')


# ─── INIT ─────────────────────────────────────────────────────────────────────

def cmd_init():
    """Interactive setup wizard. Run once in a new project directory."""
    print('Clankbrain setup\n' + '-' * 40)

    # 1. Project name
    project_name = input('Project name (e.g. "My App"): ').strip()
    if not project_name:
        project_name = 'My Project'

    # 2. Primary language
    lang = input('Primary language [python/java/js/other] (default: js): ').strip().lower()
    if lang not in ('python', 'java', 'js', 'other'):
        lang = 'js'

    # 3. Memory sync repo (optional)
    sync_repo = input('GitHub repo for memory sync (blank to skip): ').strip()

    # 4. Confirm
    print(f'\nWill create:')
    print(f'  .claude/memory/          memory directory')
    print(f'  .claude/settings.json    hook configuration')
    print(f'  .claude/memory/MEMORY.md index')
    print(f'  .claude/memory/STATUS.md session log')
    print(f'  .claude/memory/lessons.md, decisions.md, tasks/')
    print(f'  CLAUDE.md                project instructions (if not present)')
    confirm = input('\nProceed? [Y/n]: ').strip().lower()
    if confirm == 'n':
        print('Cancelled.')
        return

    # --- Create directories ---
    memory_dir = ROOT / '.claude' / 'memory'
    tasks_dir  = memory_dir / 'tasks'
    plans_dir  = memory_dir / 'plans'
    rules_dir  = ROOT / '.claude' / 'rules'
    for d in (memory_dir, tasks_dir, plans_dir, rules_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- settings.json ---
    settings_path = ROOT / '.claude' / 'settings.json'
    if not settings_path.exists():
        hook_prefix = 'python tools/memory.py'
        settings = {
            'permissions': {'allow': ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash'], 'deny': []},
            'hooks': {
                'SessionStart': [{'hooks': [
                    {'type': 'command', 'command': f'{hook_prefix} --session-start', 'timeout': 15, 'statusMessage': 'Loading memory...'},
                    {'type': 'command', 'command': f'{hook_prefix} --check-expiry',  'timeout': 5},
                ]}],
                'UserPromptSubmit': [{'hooks': [
                    {'type': 'command', 'command': f'{hook_prefix} --session-title',      'timeout': 8, 'refreshInterval': 60},
                    {'type': 'command', 'command': f'{hook_prefix} --capture-correction', 'timeout': 5},
                    {'type': 'command', 'command': f'{hook_prefix} --regret-guard',       'timeout': 5},
                    {'type': 'command', 'command': f'{hook_prefix} --decision-guard',     'timeout': 5},
                ]}],
                'PreToolUse': [{'matcher': 'Edit|Write', 'hooks': [
                    {'type': 'command', 'command': f'{hook_prefix} --pre-edit', 'timeout': 5},
                ]}],
                'PostToolUse': [
                    {'matcher': 'Edit|Write', 'hooks': [
                        {'type': 'command', 'command': f'{hook_prefix} --log-edit',      'timeout': 5, 'async': True},
                        {'type': 'command', 'command': f'{hook_prefix} --check-drift --silent', 'timeout': 15, 'async': True},
                        {'type': 'command', 'command': f'{hook_prefix} --verify-edit',   'timeout': 5},
                    ]},
                    {'matcher': 'Read|Grep', 'hooks': [
                        {'type': 'command', 'command': f'{hook_prefix} --post-read', 'timeout': 3, 'async': True},
                    ]},
                ],
                'PreCompact':   [{'hooks': [{'type': 'command', 'command': f'{hook_prefix} --precompact',  'timeout': 15, 'statusMessage': 'Preserving memory...'}]}],
                'PostCompact':  [{'hooks': [{'type': 'command', 'command': f'{hook_prefix} --postcompact', 'timeout': 15, 'statusMessage': 'Restoring memory...'}]}],
                'StopFailure':  [{'hooks': [{'type': 'command', 'command': f'{hook_prefix} --stop-failure','timeout': 10}]}],
                'Stop':         [{'hooks': [
                    {'type': 'command', 'command': f'{hook_prefix} --process-corrections', 'timeout': 5},
                    {'type': 'command', 'command': f'{hook_prefix} --journal',             'timeout': 10, 'statusMessage': 'Saving session journal...'},
                    {'type': 'command', 'command': f'{hook_prefix} --stop-check',          'timeout': 5},
                ]}],
                'PermissionDenied': [{'hooks': [{'type': 'command', 'command': f'{hook_prefix} --permission-denied', 'timeout': 8, 'async': True}]}],
            }
        }
        settings_path.write_text(json.dumps(settings, indent=2), encoding='utf-8')
        print('  created .claude/settings.json')
    else:
        print('  skipped .claude/settings.json (already exists)')

    # --- MEMORY.md ---
    memory_md = memory_dir / 'MEMORY.md'
    if not memory_md.exists():
        memory_md.write_text(f'''# Memory Index — {project_name}

- [Lessons learned](lessons.md) — patterns and mistakes from past sessions
- [Decisions](decisions.md) — locked architectural choices
- [Rejected approaches](tasks/regret.md) — what was tried and discarded
- [Active tasks](tasks/todo.md) — current work items
- [Plans](plans/) — feature plans with status tracking

# currentDate
Today is {datetime.now().strftime("%Y-%m-%d")}.
''', encoding='utf-8')
        print('  created .claude/memory/MEMORY.md')

    # --- STATUS.md ---
    status_md = memory_dir / 'STATUS.md'
    if not status_md.exists():
        status_md.write_text(f'''# {project_name} — Session Log

## Current Phase
Session 1 — Project initialized.

## Session History
| # | Date | Summary |
|---|------|---------|
| 1 | {datetime.now().strftime("%Y-%m-%d")} | Init |
''', encoding='utf-8')
        print('  created .claude/memory/STATUS.md')

    # --- Starter memory files ---
    starters = {
        memory_dir / 'lessons.md':       f'# Lessons Learned\n\n_No lessons yet. Run `/learn` at the end of a session._\n',
        memory_dir / 'decisions.md':     f'# Decisions\n\n_No decisions yet._\n',
        tasks_dir  / 'regret.md':        f'# Rejected Approaches\n\n_Approaches tried and discarded — read before proposing solutions._\n\n| Approach | Why Rejected |\n|---|---|\n',
        tasks_dir  / 'todo.md':          f'# Active Tasks\n\n_No active tasks._\n',
        tasks_dir  / 'skill_scores.md':  f'# Skill Scores\n\n_Populated by /evolve after several sessions._\n',
    }
    for path, content in starters.items():
        if not path.exists():
            path.write_text(content, encoding='utf-8')
            print(f'  created {path.relative_to(ROOT)}')

    # --- Pre-populate lessons with user's foundational rules ---
    lessons_file = memory_dir / 'lessons.md'
    print('\nBefore session 1, tell me up to 3 things Claude should never forget about this project.')
    print('(These go directly into lessons.md — Claude sees them from the very first session.)')
    initial_lessons = []
    for i in range(1, 4):
        try:
            lesson = input(f'  Lesson {i} (Enter to skip): ').strip()
        except (EOFError, KeyboardInterrupt):
            lesson = ''
        if lesson:
            initial_lessons.append(lesson)
        else:
            break  # stop asking once user skips
    if initial_lessons:
        content = '# Lessons Learned\n\n'
        for lesson in initial_lessons:
            content += f'- {lesson}\n'
        lessons_file.write_text(content, encoding='utf-8')
        print(f'  written {len(initial_lessons)} starter lesson(s) to lessons.md')

    # --- CLAUDE.md at project root ---
    claude_md = ROOT / 'CLAUDE.md'
    kit_claude = ROOT / 'tools' / '..' / 'CLAUDE.md'  # same as ROOT/CLAUDE.md if kit is at root
    if not claude_md.exists():
        # Write a minimal CLAUDE.md pointing at memory
        claude_md.write_text(f'''# {project_name} — Claude Code Project Context

> Keep this file under 200 lines. Project conventions -> rules/project-context.md.
> Memory -> .claude/memory/. Long sessions -> /learn then /compact.

## Session Commands

| Tier | Commands |
|------|----------|
| **Core** | `Start Session` - `End Session` |
| **On Demand** | `Plan` - `Debug Session` - `/learn` - `Check Drift` - `Guard Check` - `Search Memory` |

### Session Start (Automatic)
Memory loads automatically via the `SessionStart` hook -- no command needed.
On your first message each session, Claude greets you with:
"Ready. [last change]. [memory count]. What are we working on?"

If the hook is not wired, run manually: `python tools/memory.py --session-start`

### `End Session`
1. Run `/learn` -- extract lessons and decisions from this session
2. Update `.claude/memory/STATUS.md` -- increment session number, one-line summary
3. Run `python tools/memory.py --check-drift`
4. Report: "Session complete."

### On-Demand Commands
| Command | Action |
|---------|--------|
| `Check Drift`     | `python tools/memory.py --check-drift` |
| `Guard Check`     | `python tools/memory.py --guard-check` |
| `Search Memory`   | `python tools/memory.py --search "[topic]"` |
| `Memory Audit`    | `python tools/memory.py --mempalace-audit` |
| `Check Expiry`    | `python tools/memory.py --check-expiry` |
| `Kit Health`      | `python tools/memory.py --kit-health` |
| `Progress Report` | `python tools/memory.py --progress-report` |

## Memory File Conventions

Every memory file uses this frontmatter:
```
---
name: short-id
description: one-line hook for MEMORY.md index
type: rule | correction | decision | state | reference | user
valid_until: YYYY-MM-DD   # required for type: state/project
related: [other-memory.md]
---

[Summary]

**Why:** [reason]
**How to apply:** [when]

## Source
> [Verbatim snippet from the session where this was established]
-- Session N
```
''', encoding='utf-8')
        print('  created CLAUDE.md')
    else:
        # Substitute [Project Name] placeholder if present
        text = claude_md.read_text(encoding='utf-8')
        if '[Project Name]' in text:
            claude_md.write_text(text.replace('[Project Name]', project_name), encoding='utf-8')
            print(f'  updated CLAUDE.md -- replaced [Project Name] with "{project_name}"')
        else:
            print('  skipped CLAUDE.md (already configured)')

    # --- project-context.md template ---
    ctx = rules_dir / 'project-context.md'
    if not ctx.exists():
        ctx.write_text(f'''# {project_name} — Project Context

## What This Project Is
[One paragraph: what it does, who uses it, why it exists]

## Tech Stack
- **Language:** {lang}
- **Framework:** [e.g. React, Django, Spring]
- **Database:** [e.g. PostgreSQL]
- **Key files:**
  - `src/` -- [purpose]

## File Paths
| File | Purpose |
|------|---------|
| `src/` | [description] |

## Conventions
[Coding style, naming, patterns specific to this project]

## Gotchas
[Things that caused bugs or confusion — update as discovered]
''', encoding='utf-8')
        print('  created .claude/rules/project-context.md')

    # --- sync config (optional) ---
    if sync_repo:
        sync_cfg = ROOT / '.clankbrain-sync'
        sync_cfg.write_text(f'repo={sync_repo}\n', encoding='utf-8')
        print(f'  created .clankbrain-sync (repo: {sync_repo})')

    print(f'''
Done. {project_name} is ready.

Next steps:
  1. Edit .claude/rules/project-context.md -- add your tech stack and conventions
  2. Open Claude Code -- memory loads automatically on first message (no command needed)
  3. Optional: run `python tools/memory.py --session-start` if the hook is not wired
''')


# ─── DISPATCH ─────────────────────────────────────────────────────────────────

def main():
    if '--session-start' in ARGS:
        cmd_session_start()
    elif '--capture-correction' in ARGS:
        cmd_capture_correction()
    elif '--process-corrections' in ARGS:
        cmd_process_corrections()
    elif '--check-drift' in ARGS:
        cmd_check_drift()
    elif '--precompact' in ARGS:
        cmd_precompact()
    elif '--postcompact' in ARGS:
        cmd_postcompact()
    elif '--stop-failure' in ARGS:
        cmd_stop_failure()
    elif '--stop-check' in ARGS:
        cmd_stop_check()
    elif '--journal' in ARGS:
        cmd_journal()
    elif '--bootstrap' in ARGS:
        cmd_bootstrap()
    elif '--complexity-scan' in ARGS:
        cmd_complexity_scan()
    elif '--search' in ARGS:
        cmd_search()
    elif '--verify-edit' in ARGS:
        cmd_verify_edit()
    elif '--quick-learn' in ARGS:
        cmd_quick_learn()
    elif '--kit-health' in ARGS:
        cmd_kit_health()
    elif '--regret-guard' in ARGS:
        cmd_regret_guard()
    elif '--decision-guard' in ARGS:
        cmd_decision_guard()
    elif '--context-score' in ARGS:
        cmd_context_score()
    elif '--velocity-estimate' in ARGS:
        cmd_velocity_estimate()
    elif '--mine-patterns' in ARGS:
        cmd_mine_patterns()
    elif '--error-lookup' in ARGS:
        cmd_error_lookup()
    elif '--guard-check' in ARGS:
        cmd_guard_check()
    elif '--suggest-guards' in ARGS:
        cmd_suggest_guards()
    elif '--progress-report' in ARGS:
        cmd_progress_report()
    elif '--log-edit' in ARGS:
        cmd_log_edit()
    elif '--check-expiry' in ARGS:
        cmd_check_expiry()
    elif '--build-index' in ARGS:
        cmd_build_index()
    elif '--search-semantic' in ARGS:
        cmd_search_semantic()
    elif '--memory-diff' in ARGS:
        cmd_memory_diff()
    elif '--permission-denied' in ARGS:
        cmd_permission_denied()
    elif '--session-title' in ARGS:
        cmd_session_title()
    elif '--file-changed' in ARGS:
        cmd_file_changed()
    elif '--pre-edit' in ARGS:
        cmd_pre_edit()
    elif '--post-read' in ARGS:
        cmd_post_read()
    elif '--mempalace-audit' in ARGS:
        cmd_mempalace_audit()
    elif '--init' in ARGS:
        cmd_init()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if not SILENT:
            print(f'memory.py error: {e}')
