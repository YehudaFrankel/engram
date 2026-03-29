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
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
ARGS = set(sys.argv[1:])
SILENT = '--silent' in ARGS


# ─── SHARED ───────────────────────────────────────────────────────────────────

def find_memory_dir():
    """Auto-detect the .claude/memory directory."""
    for path in ROOT.rglob('MEMORY.md'):
        if '.claude' in path.parts:
            return path.parent
    return ROOT / '.claude' / 'memory'


# ─── SESSION START ────────────────────────────────────────────────────────────
# Injects MEMORY.md + STATUS.md into context before the first message.
# Hook: SessionStart

def cmd_session_start():
    memory_dir = find_memory_dir()
    parts = []

    memory_md = memory_dir / 'MEMORY.md'
    if memory_md.exists():
        parts.append('# Memory Index\n')
        parts.append(memory_md.read_text(encoding='utf-8', errors='ignore').strip())

    status_md = ROOT / 'STATUS.md'
    if status_md.exists():
        text = status_md.read_text(encoding='utf-8', errors='ignore').strip()
        lines = text.splitlines()
        excerpt = '\n'.join(lines[-30:]) if len(lines) > 30 else text
        parts.append('\n\n# Current Status\n')
        parts.append(excerpt)

    interrupt_path = memory_dir / 'tasks' / 'interruption_state.md'
    if interrupt_path.exists():
        try:
            interrupt_content = interrupt_path.read_text(encoding='utf-8').strip()
            if interrupt_content:
                parts.append(f'\n\n# ⚠ LAST SESSION INTERRUPTED (API ERROR)\n{interrupt_content}')
            interrupt_path.unlink()
        except Exception:
            pass

    queue_file = memory_dir / 'tasks' / 'corrections_queue.md'
    if queue_file.exists():
        q = queue_file.read_text(encoding='utf-8', errors='ignore')
        pending = re.findall(r'## \d{4}-\d{2}-\d{2} \d{2}:\d{2}\n\*\*Prompt:\*\* ".+?"', q)
        if pending:
            parts.append(f'\n\n# Pending Corrections ({len(pending)} — apply this session, will persist at Stop)\n')
            parts.append('\n'.join(pending))

    if not parts:
        return

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
    r'(?i)^no[,!\. ]',
    r"(?i)don't do that",
    r"(?i)don't add ",
    r"(?i)don't use ",
    r"(?i)stop doing",
    r"(?i)that's wrong",
    r"(?i)you're wrong",
    r"(?i)never do ",
    r"(?i)never use ",
    r"(?i)not what i (asked|wanted|meant|said)",
    r"(?i)that's not (right|correct)",
    r"(?i)wrong approach",
]


def _is_correction(prompt):
    for pattern in _CORRECTION_PATTERNS:
        if re.search(pattern, prompt):
            return True
    return False


def cmd_capture_correction():
    try:
        raw = sys.stdin.read()
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
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if not SILENT:
            print(f'memory.py error: {e}')
