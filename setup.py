#!/usr/bin/env python3
"""
Claude Code memory system setup.
Run from your project root: python setup.py

Creates:
  CLAUDE.md, STATUS.md
  .claude/memory/  (MEMORY.md + 5 memory files)
  tools/check_memory.py   (drift detection — PostToolUse hook)
  tools/session_start.py  (memory injection — SessionStart hook)
  tools/precompact.py     (memory preservation — PreCompact hook)
  tools/stop_check.py     (unsaved changes check — Stop hook)
  All 4 scripts are optional — only created when automated drift is chosen.
"""

import re
import sys
import shutil
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()

# Directories and file patterns to skip when scanning
SKIP_DIRS = {'node_modules', 'vendor', 'dist', 'build', '.git', '__pycache__',
             'venv', '.venv', 'bower_components', '.claude', 'tools'}
SKIP_JS  = {'.min.js', '-min.js', '.bundle.js', '.pack.js'}
SKIP_CSS = {'.min.css', '-min.css'}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _copy_update_script():
    """Copy update.py from the kit into the project root."""
    src = HERE / "update.py"
    dst = ROOT / "update.py"
    if src.exists():
        if dst.exists():
            overwrite = input("  update.py already exists. Overwrite? [y/N] ").strip().lower()
            if overwrite != 'y':
                print("  Skipped update.py")
                return
        shutil.copy2(src, dst)
        print("  Created update.py")
    else:
        print("  WARN: update.py not found in kit — skipping")


def _write_gitignore():
    """Add HANDOFF.md to .gitignore — it's a point-in-time snapshot, not a long-lived doc."""
    gitignore = ROOT / ".gitignore"
    entry = "HANDOFF.md\n"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if "HANDOFF.md" in content:
            return  # already there
        gitignore.write_text(content.rstrip("\n") + "\n" + entry, encoding="utf-8")
        print("  Updated .gitignore — added HANDOFF.md")
    else:
        gitignore.write_text(entry, encoding="utf-8")
        print("  Created .gitignore — HANDOFF.md excluded")


def create_task_files():
    """Create tasks/ folder with all four task files and a .gitkeep."""
    write("tasks/todo.md", """\
# TODO

<!-- Claude writes plans here before implementing anything. Updated as tasks complete. -->

## Current Tasks

- [ ] *(Claude will fill this in before starting work)*

## Completed

<!-- Move finished items here -->
""")

    write("tasks/lessons.md", """\
# Lessons Learned

<!-- Claude logs every correction here so the same mistake never happens twice. -->
<!-- Read at every session start. -->

| Date | What went wrong | Rule to prevent it |
|------|----------------|-------------------|
""")

    write("tasks/decisions.md", """\
# Architectural Decisions

<!-- Log decisions here so they don't get re-debated next session. -->
<!-- Read at every session start. -->

| Date | Decision | Why | Alternatives rejected |
|------|----------|-----|----------------------|
""")

    write("tasks/errors.md", """\
# Error Log

<!-- Log runtime errors with their root cause and fix. -->
<!-- Read at every session start. -->

| Date | Error | Root cause | Fix applied |
|------|-------|-----------|-------------|
""")

    # .gitkeep so tasks/ is committed to the repo even before files have content
    gitkeep = ROOT / "tasks" / ".gitkeep"
    gitkeep.parent.mkdir(parents=True, exist_ok=True)
    if not gitkeep.exists():
        gitkeep.touch()

    print("  Created tasks/ (todo.md, lessons.md, decisions.md, errors.md)")


# ─── Auto-detect ─────────────────────────────────────────────────────────────

def scan_js_files():
    found = []
    for path in ROOT.rglob("*.js"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if any(path.name.endswith(p) for p in SKIP_JS):
            continue
        if path.stat().st_size > 500_000:
            print(f"  SKIP (too large >500KB): {path.relative_to(ROOT)}")
            continue
        found.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(found)


def scan_css_files():
    found = []
    for path in ROOT.rglob("*.css"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if any(path.name.endswith(p) for p in SKIP_CSS):
            continue
        if path.stat().st_size > 500_000:
            print(f"  SKIP (too large >500KB): {path.relative_to(ROOT)}")
            continue
        found.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(found)


def detect_css_prefix(css_files):
    counts = Counter()
    pattern = re.compile(r'\.([\w][\w]*)-([\w-]+)\b')
    for f in css_files:
        path = ROOT / f
        if not path.exists():
            continue
        if path.stat().st_size > 500_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in pattern.finditer(text):
            counts[m.group(1)] += 1
    if not counts:
        return ""
    top_prefix, top_count = counts.most_common(1)[0]
    return top_prefix if top_count >= 3 else ""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default

def ask_yn(prompt, default="n"):
    suffix = " [y/N]" if default == "n" else " [Y/n]"
    val = input(f"{prompt}{suffix}: ").strip().lower()
    if not val:
        return default == "y"
    return val == "y"

def ask_list(prompt):
    print(f"{prompt} (one per line, blank to finish):")
    items = []
    while True:
        val = input("  > ").strip()
        if not val:
            break
        items.append(val)
    return items

def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        overwrite = input(f"  {path.relative_to(ROOT)} already exists. Overwrite? [y/N] ").strip().lower()
        if overwrite != 'y':
            print(f"  Skipped {path.relative_to(ROOT)}")
            return
    path.write_text(content, encoding="utf-8")
    print(f"  Created {path.relative_to(ROOT)}")


# ─── CLAUDE.md session-start block ───────────────────────────────────────────

def session_start_block(js_files, automated):
    if automated:
        drift_step = "2. Run `python tools/check_memory.py` — fix any drift found (update memory files + sync to bundle)"
    else:
        js_list = "\n".join(f"   - `{f}`" for f in js_files) if js_files else "   - *(add JS files here)*"
        drift_step = f"""\
2. Read `.claude/memory/js_functions.md`, then read each JS file below and find MISSING functions (in code, not in memory) or STALE entries (in memory, not in code). Fix any found.
{js_list}"""

    return f"""\
## Session Commands

### `Setup Memory`
When the user types **"Setup Memory"**, do the following:
1. Check if `setup.py` exists in the current directory
2. If yes — run it: `python setup.py` (or `python3 setup.py`)
3. If no — tell the user: "Copy setup.py from the starter kit into this folder first, then type Setup Memory again."

### `Start Session`
When the user types **"Start Session"**, do the following:
1. **Check Python** — run `python --version` (or `python3 --version`):
   - Not installed → tell user to download from https://python.org/downloads (check "Add to PATH"), then re-run `Start Session`
   - Installed → proceed
{drift_step}
3. Read `STATUS.md` — find the current session number and last change
4. Read `tasks/lessons.md` — apply all lessons before touching anything
5. Read `tasks/decisions.md` — understand past architectural choices
6. Read `tasks/errors.md` — know which runtime errors have already been seen and solved
7. Read `tasks/todo.md` — understand current state; create it if it doesn't exist
8. Report: "Session N ready. Last change: [X]. Memory: [OK or what was fixed]. [N] lessons loaded. What are we working on?"

### `Check Drift`
When the user types **"Check Drift"**, do the following:
1. Run `python tools/check_memory.py` (or `python3`) — if the script doesn't exist, manually scan JS files and compare against `js_functions.md`
2. Report what's MISSING (in code, not in memory), what's STALE (in memory, not in code), or "OK — no drift detected"
3. Fix any drift found — update memory files, sync to bundle

### `Analyze Codebase`
When the user types **"Analyze Codebase"**, do the following:

1. **Scan JS files** — find all non-minified `.js` files (skip node_modules, vendor, dist); list every top-level function with a one-line description based on what it does
2. **Scan CSS files** — find all non-minified `.css` files; extract all classes with the project prefix; group by feature area
3. **Scan backend** — find Java/Python/Node/Go files; list all public methods and API endpoints
4. **Update memory files** with findings (add MISSING entries only — don't overwrite existing descriptions):
   - `js_functions.md` — new functions found
   - `html_css_reference.md` — new CSS classes found
   - `backend_reference.md` — new endpoints found
5. **Update `tools/check_memory.py`** — if it exists, make sure JS_FILES and CSS_FILES include all discovered files
6. **Report** — "Analyzed: [N] JS functions, [N] CSS classes, [N] endpoints. Memory updated."

### `Generate Skills`
When the user types **"Generate Skills"**, do the following:

1. **Scan the project** — read CLAUDE.md and memory files to understand the stack, file structure, and patterns already in use
2. **Identify what skills would help** — based on what you find:
   - Any project → `fix-bug`, `code-review`, `refactor`, `security-check`
   - Has backend/API → `new-endpoint` or `new-feature`
   - Has a database → `write-query`
   - Has tests → `run-tests`
   - Has a deployment step → `environment-check`
   - Has a manual QA process → `run-verification`
3. **Create each skill** — for each skill identified, create `.claude/skills/<name>/SKILL.md` with:
   - Frontmatter: `name`, `description` (when to trigger), `allowed-tools`
   - Body: step-by-step instructions tailored to this project's actual file names, patterns, and conventions
4. **Report** — list every skill created and the phrase that will trigger it

### `Update Kit`
When the user types **"Update Kit"** (or **"Update Kit from [URL]"**), do the following:
1. Check if `update.py` exists in the project root
2. If yes — run it via the Bash tool:
   - `Update Kit` → `python update.py`
   - `Update Kit from https://github.com/user/repo` → `python update.py https://github.com/user/repo`
3. If no — fetch and run it in one step using the Bash tool:
   python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/YehudaFrankel/Claude-Code-memory-starter-kit/main/update.py').read().decode())"
4. The script previews all changes and asks for confirmation before applying anything

### `Debug Session`
When the user types **"Debug Session"** (or **"Debug Session: [description]"**), do the following:
1. **Reproduce first** — confirm the bug is actually happening; check logs, run the code, see the failure
2. **Isolate** — narrow down exactly where it breaks (which file, which function, which line)
3. **Hypothesize** — state one specific root cause before touching anything: "I think the issue is X because Y"
4. **Test the hypothesis** — prove or disprove it without changing production code yet
5. **Fix only what's confirmed** — change the minimum code needed to fix the confirmed root cause
6. **Verify** — confirm the fix works AND nothing else broke
7. **Log it** — add one line to `tasks/errors.md`: `[date] | error description | root cause | fix applied`
8. Report: "Bug fixed. Root cause was: [X]. Changed: [files]. Verified: [how]."

### `Code Health`
When the user types **"Code Health"**, do the following:
1. **Scan for debug leftovers** — find any `console.log`, `print(`, `debugger`, `TODO`, `FIXME`, `HACK` across all project files
2. **Find hardcoded values** — look for hardcoded URLs, credentials, magic numbers, test IDs
3. **Check error handling** — find functions that could throw but have no try/catch or .catch()
4. **Find dead code** — functions defined but never called; variables declared but never used
5. **Check large files** — flag any file over 500 lines as a refactor candidate
6. **Report findings** in a clean table — file, line number, issue type, severity (low/medium/high)
7. Ask: "Fix any of these now, or just flag for later?"

### `Handoff`
When the user types **"Handoff"**, do the following:
1. Read `STATUS.md`, `tasks/todo.md`, `tasks/decisions.md`, `tasks/errors.md`, and `.claude/memory/project_status.md`
2. Generate a `HANDOFF.md` in the project root with:
   - **Current state** — what's working, what's not, what's in progress
   - **What to do next** — top 3 tasks in priority order from `todo.md`
   - **Key decisions already made** — pulled from `decisions.md` (don't re-debate these)
   - **Known errors and fixes** — pulled from `errors.md`
   - **Gotchas** — non-obvious things that would trip up someone new
   - **How to start** — exact command to run to get context (`Start Session`)
3. Report: "HANDOFF.md created. Share this file with anyone picking up the project."

### `Estimate`
When the user types **"Estimate: [task description]"**, do the following:
1. **Read the relevant files** — scan whichever files the task would touch
2. **Estimate complexity** — Small (< 1 hour), Medium (1-4 hours), Large (4+ hours)
3. **List files that will change** — every file that will need to be edited
4. **Flag risks** — anything that could go wrong, dependencies that are unclear, assumptions being made
5. **Ask one question** — if anything is ambiguous, ask the single most important clarifying question before starting
6. **Write the plan** to `tasks/todo.md` if the user confirms they want to proceed
7. Report: "Complexity: [size]. Files: [list]. Risks: [list]. Ready to start?"

### `Install Memory`
When the user types **"Install Memory"**, do the following:

1. **Analyze the codebase** — scan all JS, CSS, and backend files to understand what's here:
   - Find all top-level JS functions across all JS files
   - Find all CSS classes (with project prefix) across all CSS files
   - Find all API endpoints / backend methods
2. **Copy bundle to system path** — copy all `.claude/memory/*.md` files to the system memory path:
   - **Mac/Linux:** `~/.claude/projects/[encoded]/memory/`
   - **Windows:** `%USERPROFILE%\.claude\projects\[encoded]\memory\`
   - **How to encode:** replace every `/`, `\\`, and `:` with `-`
   - Example: `/home/user/myproject` → `home-user-myproject`
   - Example: `D:\\projects\\myapp` → `D--projects-myapp`
3. **Fill any gaps** — if `js_functions.md`, `html_css_reference.md`, or `backend_reference.md` are missing entries found in step 1, add them now
4. **Report** — "Memory installed. [N] JS functions, [N] CSS classes documented. Ready."

### `End Session`
When the user types **"End Session"**, do the following:
> **Tip:** If this session ran long, type `/compact` first to summarize the conversation before ending.
1. Update `STATUS.md` — increment session number, add one-line entry: date + what changed
2. Update all relevant memory files in `.claude/memory/` for anything changed this session:
   - JS changed → update `js_functions.md`
   - HTML/CSS changed → update `html_css_reference.md`
   - Backend/API changed → update `backend_reference.md`
   - Phase or architecture change → update `project_status.md`
   - New rules or gotchas → update `user_preferences.md`
   - Update `currentDate` in `.claude/memory/MEMORY.md` to today's date
3. Sync memory files to any project bundle (`.claude/memory/` in repo if present)
4. Run drift check to confirm everything is clean
5. Report: "Session N complete. Updated: [list]. Memory clean."

---

## Auto-Save Rule

After **any code change** this session, immediately update the relevant memory file — don't wait for `End Session`:

| What changed | Update this file |
|---|---|
| JavaScript function added or changed | `js_functions.md` |
| HTML element or CSS class added or changed | `html_css_reference.md` |
| Endpoint or backend method added or changed | `backend_reference.md` |
| Architecture decision or non-obvious gotcha | `project_status.md` |
| Chose approach A over B for a reason | `tasks/decisions.md` |
| Fixed a runtime error / bug | `tasks/errors.md` |

`End Session` handles `STATUS.md`, the full drift check, and confirms everything is clean.

---

## Workflow

### Session Start
1. Read `tasks/lessons.md` — apply all lessons before touching anything
2. Read `tasks/decisions.md` — know the architectural choices already made
3. Read `tasks/errors.md` — know which bugs have already been solved
4. Read `tasks/todo.md` — understand current state
5. If any of these don't exist, create them before starting

---

### 1. Plan First
- Before starting any non-trivial task, run `Estimate: [task]` — flag complexity and risks upfront
- Enter plan mode for any non-trivial task (3+ steps)
- Write plan to `tasks/todo.md` before implementing
- If something goes wrong, STOP and re-plan — never push through

### 2. Subagent Strategy
- Use subagents to keep main context clean
- One task per subagent
- Throw more compute at hard problems

### 3. Self-Improvement Loop
- After any correction: update `tasks/lessons.md`
- Format: `[date] | what went wrong | rule to prevent it`
- Review lessons at every session start

### 4. Verification Standard
- Never mark complete without proving it works
- Run tests, check logs, diff behavior
- Ask: "Would a staff engineer approve this?"

### 5. Demand Elegance
- For non-trivial changes: is there a more elegant solution?
- If a fix feels hacky: rebuild it properly
- Don't over-engineer simple things

### 6. Autonomous Bug Fixing
- When given a bug: just fix it
- Go to logs, find root cause, resolve it
- No hand-holding needed

---

### Core Principles
- **Simplicity First** — touch minimal code
- **No Laziness** — root causes only, no temp fixes
- **Never Assume** — verify paths, APIs, variables before using
- **Ask Once** — one question upfront if unclear, never interrupt mid-task

---

### Task Management
1. **Estimate** → flag complexity and risks before starting
2. **Plan** → `tasks/todo.md`
3. **Verify** → confirm before implementing
4. **Track** → mark complete as you go
5. **Explain** → high-level summary each step
6. **Learn** → `tasks/lessons.md` after corrections
7. **Decide** → `tasks/decisions.md` after architectural choices
8. **Log errors** → `tasks/errors.md` after every bug fix
"""


# ─── Lite mode ───────────────────────────────────────────────────────────────

def _generate_lite(name, tech):
    """Generate minimal memory system for small projects."""

    write("CLAUDE.md", f"""# {name} — Claude Code Project Context

## Session Commands

### `Setup Memory`
When the user types **"Setup Memory"**, do the following:
1. Check if `setup.py` exists in the current directory
2. If yes — run it: `python setup.py` (or `python3 setup.py`)
3. If no — tell the user: "Copy setup.py from the starter kit into this folder first, then type Setup Memory again."

### `Start Session`
When the user types **"Start Session"**, do the following:
1. Read `STATUS.md` — find the current session number and last change
2. Read `.claude/memory/notes.md` — review current project notes
3. Report: "Session N ready. Last change: [X]. What are we working on?"

### `End Session`
When the user types **"End Session"**, do the following:
> **Tip:** If this session ran long, type `/compact` first to summarize the conversation before ending.
1. Update `STATUS.md` — increment session number, add one-line entry: date + what changed
2. Update `.claude/memory/notes.md` — add anything new: functions, decisions, gotchas
3. Report: "Session N complete. Notes updated."

### `Generate Skills`
When the user types **"Generate Skills"**, do the following:
1. Read CLAUDE.md and `.claude/memory/notes.md` to understand the stack and patterns
2. Create useful skills for this project — at minimum `fix-bug` and `code-review`; add more based on what you find (e.g. `new-feature`, `write-query`, `run-tests`)
3. For each skill, create `.claude/skills/<name>/SKILL.md` with frontmatter (`name`, `description`, `allowed-tools`) and step-by-step instructions tailored to this project
4. Report what was created and what phrase triggers each skill

---

## Auto-Save Rule

After **any code change**, immediately add a note to `.claude/memory/notes.md` — don't wait for `End Session`.

---

## What This Project Is
<!-- One paragraph: what it does, who uses it, what problem it solves -->

---

## Tech Stack
{tech if tech else "<!-- Fill in -->"}

---

## Notes / Gotchas
<!-- Non-obvious decisions, things that would trip up a new dev -->

---

## Session Starter Prompt
> "Read CLAUDE.md and STATUS.md. We're continuing {name}. Check what was last changed and let's pick up where we left off."
""")

    write("STATUS.md", f"""# {name} — Status

## Current Session: 1

## Session Log

- Session 1: Initial project setup
""")

    write(".claude/memory/MEMORY.md", f"""# Memory Index

- [Project notes](notes.md) — Functions, decisions, gotchas, recent changes

# currentDate
<!-- Update this each session -->
Today's date is [YYYY-MM-DD].
""")

    write(".claude/memory/notes.md", f"""---
name: {name} notes
description: Running notes — functions, decisions, gotchas, recent changes
type: project
---

## Key Functions

| Function | What it does |
|----------|-------------|

---

## Decisions & Gotchas

<!-- Non-obvious choices, things to remember next session -->

---

## Recent Changes

<!-- Quick log: what changed and why -->
""")

    if ask_yn("Generate skill files? (code-review, fix-bug — auto-invoked)", "y"):
        generate_skills(name, tech)

    write(".claude/settings.json", '''{
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "deny": []
  }
}''')

    # tasks/ files
    create_task_files()

    # Copy update.py from kit into project
    _copy_update_script()

    # .gitignore — HANDOFF.md is point-in-time, never commit it
    _write_gitignore()

    print(f"""
Done. Lite memory system created in: {ROOT}

Files created:
  CLAUDE.md              ← Claude's instructions
  STATUS.md              ← Session log
  .claude/memory/
    MEMORY.md            ← Auto-loaded index
    notes.md             ← Your one-stop notes file
  tasks/                 ← Task files (commit these)
  .claude/skills/        ← Auto-invoked prompt packs (if generated)

Next steps:
  1. Open Claude Code and type: Start Session
  2. Work on your project — Claude updates notes.md after each change
  3. Type: End Session when done
""")


# ─── Skills ──────────────────────────────────────────────────────────────────

def generate_skills(name, tech):
    """Generate .claude/skills/ files — auto-invoked prompt packs."""

    write(".claude/skills/code-review/SKILL.md", f"""\
---
name: code-review
description: Review code for quality issues, dead code, missing error handling, and patterns that deviate from this project's conventions. Use when the user asks to review, audit, or check a file.
allowed tools: Read, Grep, Glob
---

# Code Review for {name}

Review the file(s) for the following — report findings before fixing anything:

1. **Dead code** — unused functions, variables, commented-out blocks
2. **Repeated logic** — similar blocks that could share a helper
3. **Missing error handling** — unguarded calls that could throw silently
4. **Hardcoded values** — magic strings/numbers that should be constants
5. **Console.log / debug output** left in
6. **Project convention violations** — anything that deviates from the patterns in CLAUDE.md

Format findings as a numbered list. Ask before making any changes.
""")

    write(".claude/skills/security-check/SKILL.md", f"""\
---
name: security-check
description: Check code for security vulnerabilities — SQL injection, missing auth, sensitive data exposure. Use when the user asks for a security check, audit, or before shipping.
allowed tools: Read, Grep, Glob
---

# Security Check for {name}

Scan the file(s) for:

1. **SQL injection** — values concatenated into queries without escaping/parameterization
2. **Missing auth checks** — endpoints or routes that should require login but don't
3. **Sensitive data exposure** — passwords, tokens, or private fields returned to the client
4. **XSS vectors** — user input rendered as HTML without escaping
5. **Insecure defaults** — debug flags, open CORS, permissive error messages in production paths

Report every finding with file + line reference. Suggest the fix but don't apply it until confirmed.
""")

    write(".claude/skills/fix-bug/SKILL.md", f"""\
---
name: fix-bug
description: Structured approach to diagnosing and fixing a bug. Use when the user describes something broken or asks to fix an issue.
allowed tools: Read, Grep, Glob, Bash
---

# Bug Fix for {name}

Follow this process:

1. **Locate** — find the relevant file(s) using the description. Check both frontend and backend if the bug could be in either.
2. **Read** — read the relevant function(s) in full before forming a theory.
3. **Diagnose** — state the root cause clearly before touching anything.
4. **Show the fix** — present the exact change (old vs new) and explain why it works.
5. **Wait for confirmation** — don't apply the fix until the user says yes.
6. **Update memory** — after applying, update the relevant memory file if the fix reveals a non-obvious pattern or gotcha.
""")

    write(".claude/skills/new-feature/SKILL.md", f"""\
---
name: new-feature
description: Structured approach to adding a new feature. Use when the user asks to add, build, or implement something new.
allowed tools: Read, Grep, Glob, Write, Edit, Bash
---

# New Feature for {name}

Follow this process:

1. **Understand** — restate what the feature should do and what triggers it (user action, API call, schedule, etc.)
2. **Find the right files** — identify which existing files need to change vs. what needs to be created new
3. **Plan** — outline the change (2–5 bullet points) before writing any code. Wait for confirmation.
4. **Implement** — make the changes following the existing patterns in this project (see CLAUDE.md conventions)
5. **Update memory** — after implementing, update the relevant memory file:
   - New JS function → `js_functions.md`
   - New endpoint → `backend_reference.md`
   - New CSS class → `html_css_reference.md`
   - Architectural decision → `project_status.md`
""")

    write(".claude/skills/environment-check/SKILL.md", f"""\
---
name: environment-check
description: Check if code is ready for production, verify environment-specific config, or switch environments. Use when the user says "ready for prod", "before deploy", "update URLs", or "is this prod-ready".
allowed-tools: Read, Grep, Glob, Edit
---

# Environment Check for {name}

Reference: `ENVIRONMENT-MATRIX.md` in this folder for project-specific values.

1. **Read `ENVIRONMENT-MATRIX.md`** — understand what differs between environments

2. **Scan for hardcoded environment-specific values:**
   - Grep for `localhost`, `127.0.0.1`, dev-only URLs, test credentials
   - Check any config constants file for values that need to change per environment

3. **Walk through the pre-deploy checklist** in `ENVIRONMENT-MATRIX.md` — mark each item DONE / PENDING

4. **Report:** "Environment: [local/prod]. Issues found: [list or none]. Ready to deploy: [yes/no]."

5. If changes are needed: show exactly what to change and ask for confirmation before editing.
""")

    write(".claude/skills/environment-check/ENVIRONMENT-MATRIX.md", f"""\
# Environment Matrix — {name}

## Environments

| Setting | Local Dev | Production |
|---------|-----------|-----------|
| Base URL | `http://localhost:____` | `https://[live-domain]` |
| Database | Local / dev DB | Production DB |
| Email sending | [test mode?] | Real SMTP |
| External services | [sandbox?] | Real |

> Fill in the actual values for this project.

## Where Config Lives
> Document where environment-specific values are stored (constants file, .env, server config, etc.)

## Pre-Deploy Checklist

- [ ] All URL/host constants updated from dev to production values
- [ ] Database connection pointing to production
- [ ] Any test/debug mode flags turned off
- [ ] Smoke test with a real account on production

## Things That Commonly Break on Deploy
> Add project-specific gotchas here.
""")

    write(".claude/skills/run-verification/SKILL.md", f"""\
---
name: run-verification
description: Verify a feature works end-to-end after making changes, or before shipping. Use when the user says "verify this works", "test this", "does this work", "run the checklist", or "before I ship".
allowed-tools: Read, Grep, Glob, Bash
---

# Verification for {name}

Reference: `TEST-STRATEGY.md` in this folder for project-specific checklists.

1. **Identify what changed** — ask which layer was modified (frontend, API, data, email, scheduler, etc.)

2. **Check for pre-test blockers:**
   - Any build/compile step needed after the change?
   - Any server restart or cache clear required?
   - Any DB migration that needs to run first?

3. **Pick the relevant layer** from `TEST-STRATEGY.md` and walk through its checklist

4. **Report each item:** PASS / FAIL / UNTESTED

5. **For any FAIL** — state the exact symptom and most likely cause

6. **Report:** "Verification: [N] pass, [N] fail, [N] untested. Ready to ship: [yes/no]."
""")

    write(".claude/skills/run-verification/TEST-STRATEGY.md", f"""\
# Test Strategy — {name}

## Testing Approach
> Describe the testing approach: unit tests, integration tests, manual only, etc.

---

## Layer 1 — Frontend

| Test | How to verify | Pass condition |
|------|--------------|---------------|
| Page loads without errors | Open in browser, check console | No JS errors |
| Core user flow | [describe main flow] | [expected result] |
| Form submission | Fill and submit | Success state shown |
| Error states | Submit invalid data | Error message shown |

---

## Layer 2 — API / Backend

| Endpoint / Method | Input | Expected output |
|------------------|-------|----------------|
| [add endpoints here] | | |

**Common failure modes:**
- Returns 200 but with empty data
- Auth failure returning wrong status code
- Silent insert/write failure (no error returned)

---

## Layer 3 — Data

| Check | How |
|-------|-----|
| Record created after action | Query DB directly |
| Record updated correctly | Check specific fields |

---

## Full Flow Smoke Test
> Describe the end-to-end happy path to verify after any significant change.

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Known Fragile Areas
> List things that have broken before or need extra care when testing.
""")

    write(".claude/skills/refactor/SKILL.md", f"""\
---
name: refactor
description: Clean up, simplify, or restructure existing code without changing behavior. Use when the user says "refactor", "clean up", "simplify this", "this is getting messy", "too long", or "extract this".
allowed-tools: Read, Edit, Grep, Glob
---

# Refactor for {name}

Reference: `ANTI-PATTERNS.md` in this folder.

1. **Read the target file fully** — understand what it does before touching anything

2. **Check `ANTI-PATTERNS.md`** — does the code contain any listed anti-patterns?

3. **Identify the refactor type:**
   - Duplicated logic → extract shared helper
   - Method doing too many things → split by responsibility
   - Deep nesting → early return / guard clause
   - Magic numbers/strings → named constants

4. **State the plan first:**
   > "I'll refactor X by doing Y. This changes structure but not behavior. Files affected: [list]."

5. **Wait for user confirmation** before changing anything

6. **One change at a time** — each step leaves code in a working state

7. **Do NOT while refactoring:**
   - Add new features or change behavior
   - Introduce new dependencies or libraries
   - "Fix" things that weren't asked about
""")

    write(".claude/skills/refactor/ANTI-PATTERNS.md", f"""\
# Anti-Patterns — {name}

Things to flag when found in this codebase.

---

## General Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Magic numbers | `if (status == 3)` — what is 3? | Named constant |
| Deep nesting (3+ levels) | Hard to read, easy to miss edge cases | Early return / guard clauses |
| Long functions (50+ lines) | Doing too many things | Split by responsibility |
| Copy-paste code | Two copies diverge, bugs fixed in one place | Extract shared helper |
| Dead code | Unreachable branches, unused variables | Delete it — git has history |

---

## JavaScript Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| DOM query inside loop | Repeated expensive lookups | Cache element reference outside loop |
| `innerHTML =` with user data | XSS risk | `textContent` or sanitize first |
| Missing `.catch()` on promises | Silent failures | Always handle rejections |
| `console.log` left in | Debug noise in production | Remove before shipping |

---

## Project-Specific Anti-Patterns
> Add patterns specific to this codebase that should always be flagged.
""")

    print("  Created .claude/skills/ (code-review, security-check, fix-bug, new-feature, environment-check, run-verification, refactor)")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Claude Code Memory System Setup ===\n")

    name = ask("Project name", ROOT.name)
    tech = ask("Tech stack (e.g. Java + Vanilla JS + SQL Server)", "")

    # ── Project size ──
    print()
    print("Project size:")
    print("  1. Full  — complex project (multiple JS/CSS files, backend, drift detection)")
    print("  2. Lite  — small project (one notes file, no drift script, 2-minute setup)")
    size = ask("Choose [1/2]", "1")

    if size.strip() == "2":
        _generate_lite(name, tech)
        return

    # ── File detection mode ──
    print()
    print("How should I find your JS and CSS files?")
    print("  1. Auto-detect — scan this folder and figure it out (recommended)")
    print("  2. Manual      — I'll tell you which files to track")
    mode = ask("Choose [1/2]", "1")

    if mode.strip() == "1":
        print("\nScanning project...")
        js_files  = scan_js_files()
        css_files = scan_css_files()
        css_prefix = detect_css_prefix(css_files)

        if js_files:
            print(f"\nFound {len(js_files)} JS file(s):")
            for f in js_files[:8]:
                print(f"  {f}")
            if len(js_files) > 8:
                print(f"  ... and {len(js_files) - 8} more")
        else:
            print("\nNo JS files found.")

        if css_files:
            print(f"\nFound {len(css_files)} CSS file(s):")
            for f in css_files[:5]:
                print(f"  {f}")

        if css_prefix:
            print(f"\nDetected CSS class prefix: {css_prefix}-")
        else:
            print("\nCouldn't detect CSS prefix automatically.")
            css_prefix = ask("CSS class prefix (e.g. ttw, app, my) — or press Enter to skip", "")

        print()
        if not ask_yn("Use these files?", "y"):
            print("Switching to manual entry...")
            js_files   = ask_list("JS files to track (relative to project root, e.g. js/MyFunctions.js)")
            css_files  = ask_list("CSS files to track (e.g. css/MyStyle.css)")
            css_prefix = ask("CSS class prefix (e.g. ttw, app, my) — leave blank to skip CSS drift", "")
    else:
        js_files   = ask_list("JS files to track (relative to project root, e.g. js/MyFunctions.js)")
        css_files  = ask_list("CSS files to track (e.g. css/MyStyle.css)")
        css_prefix = ask("CSS class prefix (e.g. ttw, app, my) — leave blank to skip CSS drift", "")

    print()
    print("Drift detection mode:")
    print("  1. Script  — check_memory.py runs automatically after every file edit (recommended)")
    print("  2. Manual  — Claude reads your JS files directly on session start (no dependencies)")
    drift_choice = ask("Choose [1/2]", "1")
    automated = drift_choice.strip() != "2"

    print()

    # ── CLAUDE.md ──
    write("CLAUDE.md", f"""# {name} — Claude Code Project Context

{session_start_block(js_files, automated).strip()}

---

## What This Project Is
<!-- One paragraph: what it does, who uses it, what problem it solves -->

---

## Tech Stack
{tech if tech else "<!-- Fill in -->"}

---

## File Paths

| File | Purpose |
|------|---------|
| *(add key files here)* | |

---

## Coding Conventions

### Adding an Endpoint / Route
<!-- Step-by-step: where to register, where to implement, how to read params -->

### DB Patterns
<!-- How to query, insert, update — framework-specific helpers, what to avoid -->

### Frontend API Calls
<!-- How JS calls the backend — fetch wrapper, promise pattern, etc. -->

---

## Design System

### Colors
```css
/* Paste your CSS variables here */
```

### Principles
<!-- Mobile-first? No external deps? Specific component patterns? -->

---

## Files Claude Should Never Touch

> List files that must not be restructured or reformatted — only surgical edits allowed.

| File | Why |
|------|-----|
| *(e.g. routing/dispatch file)* | Order-sensitive — restructuring breaks all routing |
| *(e.g. install/migration SQL)* | Idempotent script — structure must be preserved |
| *(e.g. shared library files)* | Not owned by this project |

**Rule:** If a task requires changes to these files, read the full file first, change only the minimum lines needed, and confirm with the user before applying.

---

## Headless Mode — For Big Tasks

Run Claude in the background for large refactors, boilerplate generation, or multi-file changes:

```bash
claude --headless "your full task description here"
```

Best used for: generating scaffolding, large refactors where the goal is clear, multi-file changes you don't need to watch step-by-step. For debugging or design decisions — use normal interactive mode.

---

## Notes / Gotchas
<!-- Non-obvious decisions, things that would trip up a new dev -->

---

## Verification Checklist
- [ ] *(add smoke tests here)*

---

## Session Starter Prompt
> "Read CLAUDE.md and STATUS.md. We're continuing {name}. Check which phases are complete and let's pick up where we left off."
""")

    # ── STATUS.md ──
    write("STATUS.md", f"""# {name} — Status

## Current Session: 1

## Session Log

- Session 1: Initial project setup
""")

    # ── tasks/ ──
    create_task_files()

    # ── .gitignore ──
    _write_gitignore()

    # ── MEMORY.md ──
    write(".claude/memory/MEMORY.md", f"""# Memory Index

- [User preferences and working style](user_preferences.md) — Communication style, things to avoid, update rules
- [Project status](project_status.md) — Completed phases, key decisions, current session number
- [JS functions reference](js_functions.md) — All functions across all JS files with descriptions
- [HTML & CSS reference](html_css_reference.md) — Page section IDs, component IDs, CSS classes
- [Backend reference](backend_reference.md) — API endpoints, DB patterns, utility methods

# currentDate
<!-- Update this each session -->
Today's date is [YYYY-MM-DD].
""")

    # ── project_status.md ──
    write(".claude/memory/project_status.md", f"""---
name: {name} project status
description: Current build status, completed phases, and key architectural decisions
type: project
---

## Current Session: 1

### Completed Phases
- Session 1: Initial project setup

### Key Architectural Notes
-

### File Paths
-
""")

    # ── js_functions.md ──
    js_section = "\n\n".join(
        f"## {Path(f).name}\n\n| Function | Purpose |\n|----------|---------|"
        for f in js_files
    ) if js_files else "## (add JS files here)\n\n| Function | Purpose |\n|----------|---------|"

    write(".claude/memory/js_functions.md", f"""---
name: {name} JS functions
description: All JS functions across all JS files with one-line descriptions
type: reference
---

<!-- Format: | `functionName` | Purpose | -->
<!-- Claude will flag functions missing from this file on session start. -->

{js_section}
""")

    # ── html_css_reference.md ──
    write(".claude/memory/html_css_reference.md", f"""---
name: {name} HTML structure and CSS classes
description: All HTML page sections/IDs and CSS classes
type: reference
---

## CSS Variables
```css
/* Paste your :root variables here */
```

---

## Page Sections

| ID | Purpose |
|----|---------|
| `loadingOverlay` | Full-screen loading spinner |

---

## Key CSS Classes

| Class | Purpose |
|-------|---------|
""")

    # ── user_preferences.md ──
    write(".claude/memory/user_preferences.md", """---
name: User preferences and working style
description: How the user wants Claude to communicate and behave
type: user
---

- Keep responses short and direct — no preamble, no summaries after edits
- Always update CLAUDE.md and STATUS.md after every code change
- Don't add comments or docstrings to code that wasn't changed
- Don't over-engineer — simplest solution that works
""")

    # ── backend_reference.md ──
    write(".claude/memory/backend_reference.md", f"""---
name: {name} backend reference
description: All API endpoints, DB patterns, and utility methods
type: reference
---

## API Endpoints

| Endpoint | Auth? | Purpose |
|----------|-------|---------|

---

## DB Patterns

<!-- Safe query/insert/update patterns for this project -->

---

## Key Utility Methods

| Method | Purpose |
|--------|---------|
""")

    # ── Skills ──
    if ask_yn("Generate skill files? (auto-invoked prompts for code review, security, bug fixing)", "y"):
        generate_skills(name, tech)

    # ── update.py ──
    _copy_update_script()

    # ── .claude/settings.json (always) ──
    if automated:
        settings_content = '''{
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "deny": []
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{ "type": "command", "command": "python tools/session_start.py", "timeout": 10, "statusMessage": "Loading memory..." }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "python tools/check_memory.py --silent" }]
      }
    ],
    "PreCompact": [
      {
        "hooks": [{ "type": "command", "command": "python tools/precompact.py", "timeout": 10, "statusMessage": "Preserving memory..." }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "python tools/stop_check.py", "timeout": 5 }]
      }
    ]
  }
}'''
    else:
        settings_content = '''{
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "deny": []
  }
}'''
    write(".claude/settings.json", settings_content)

    # ── tools/check_memory.py (only if automated) ──
    if automated:
        js_file_lines  = "\n".join(f'    ROOT / "{f}",' for f in js_files) or '    # ROOT / "js/YourFunctions.js",'
        css_file_lines = "\n".join(f'    ROOT / "{f}",' for f in css_files) or '    # ROOT / "css/YourStyle.css",'
        css_pattern    = rf'r"\.({css_prefix}-[\w-]+)"' if css_prefix else r'r"\.(your-prefix-[\w-]+)"'

        write("tools/check_memory.py", f'''#!/usr/bin/env python3
"""
Claude Code memory drift checker for {name}.
Usage: python tools/check_memory.py
Run from the project root (or any subdirectory).
"""

import re
import sys
from pathlib import Path

SILENT = "--silent" in sys.argv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

JS_FILES = [
{js_file_lines}
]

CSS_FILES = [
{css_file_lines}
]

CSS_CLASS_PATTERN = {css_pattern}

MODIFIER_SUFFIXES = (
    \'-active\', \'-open\', \'-disabled\', \'-locked\', \'-empty\', \'-success\',
    \'-error\', \'-loading\', \'-collapsed\', \'-dirty\', \'-sm\', \'-lg\', \'-xs\',
    \'-full\', \'-inline\', \'-new\', \'-replied\', \'-flush\',
)

MEMORY_DIR = ROOT / ".claude/memory"
JS_MEMORY  = MEMORY_DIR / "js_functions.md"
CSS_MEMORY = MEMORY_DIR / "html_css_reference.md"


FUNC_PATTERNS = [
    re.compile(r\'^function\\s+(\\w+)\\s*\\(\', re.MULTILINE),
    re.compile(r\'^async\\s+function\\s+(\\w+)\\s*\\(\', re.MULTILINE),
    re.compile(r\'^(?:const|let|var)\\s+(\\w+)\\s*=\\s*(?:async\\s+)?function\\s*\\(\', re.MULTILINE),
    re.compile(r\'^(?:const|let|var)\\s+(\\w+)\\s*=\\s*(?:async\\s*)?\\([^)]*\\)\\s*=>\', re.MULTILINE),
    re.compile(r\'^(?:const|let|var)\\s+(\\w+)\\s*=\\s*(?:async\\s+)?\\w+\\s*=>\', re.MULTILINE),
    re.compile(r\'^\\s{{2,}}(\\w+)\\s*\\([^)]*\\)\\s*\\{{\', re.MULTILINE),
    re.compile(r\'^\\s+(\\w+)\\s*:\\s*(?:async\\s+)?function\', re.MULTILINE),
]


def extract_js_functions(paths):
    found = {{}}
    for path in paths:
        if not path.exists():
            if not SILENT:
                print(f"  WARN: JS file not found: {{path}}")
            continue
        if path.stat().st_size > 500_000:
            if not SILENT:
                print(f"  WARN: Skipping {{path.name}} — file exceeds 500KB (likely bundled/minified)")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FUNC_PATTERNS:
            for m in pattern.finditer(text):
                name = m.group(1)
                if name not in found:
                    found[name] = path.name
    return found


def extract_memory_functions(md_path):
    if not md_path.exists():
        if not SILENT:
            print(f"  WARN: memory file not found: {{md_path}}")
        return set()
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r\'\\|\\s*`(\\w+)(?:\\([^)]*\\))?`\\s*\\|\')
    return set(m.group(1) for m in pattern.finditer(text))


def extract_css_classes(paths):
    found = set()
    pattern = re.compile(CSS_CLASS_PATTERN)
    for path in paths:
        if not path.exists():
            if not SILENT:
                print(f"  WARN: CSS file not found: {{path}}")
            continue
        if path.stat().st_size > 500_000:
            if not SILENT:
                print(f"  WARN: Skipping {{path.name}} — file exceeds 500KB (likely bundled/minified)")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in pattern.finditer(text):
            found.add(m.group(1))
    return found


def extract_memory_css_classes(md_path):
    if not md_path.exists():
        return set()
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(CSS_CLASS_PATTERN)
    return set(m.group(1) for m in pattern.finditer(text))


def main():
    drift = False

    if JS_FILES:
        code_fns = extract_js_functions(JS_FILES)
        mem_fns  = extract_memory_functions(JS_MEMORY)
        missing  = set(code_fns) - mem_fns
        stale    = mem_fns - set(code_fns)
        if missing:
            drift = True
            print("MISSING from js_functions.md (exist in code):")
            for fn in sorted(missing):
                print(f"  + {{fn}}  [{{code_fns[fn]}}]")
        if stale:
            drift = True
            print("STALE in js_functions.md (no longer in code):")
            for fn in sorted(stale):
                print(f"  - {{fn}}")

    if CSS_FILES and "your-prefix" not in CSS_CLASS_PATTERN:
        code_cls  = extract_css_classes(CSS_FILES)
        mem_cls   = extract_memory_css_classes(CSS_MEMORY)
        stale_css = mem_cls - code_cls
        if stale_css:
            drift = True
            print("STALE in html_css_reference.md (no longer in CSS):")
            for cls in sorted(stale_css):
                print(f"  - .{{cls}}")
        significant = {{c for c in code_cls - mem_cls if not any(c.endswith(s) for s in MODIFIER_SUFFIXES)}}
        if significant:
            drift = True
            print("NEW CSS classes not in html_css_reference.md:")
            for cls in sorted(significant):
                print(f"  + .{{cls}}")

    if not drift:
        if not SILENT:
            print("OK — no drift detected")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
''')

    # ── Copy lifecycle hook scripts (only if automated) ──
    if automated:
        for script_name in ("session_start.py", "precompact.py", "stop_check.py"):
            src = HERE / "tools" / script_name
            dst = ROOT / "tools" / script_name
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    overwrite = input(f"  tools/{script_name} already exists. Overwrite? [y/N] ").strip().lower()
                    if overwrite != 'y':
                        print(f"  Skipped tools/{script_name}")
                        continue
                shutil.copy2(src, dst)
                print(f"  Created tools/{script_name}")
            else:
                print(f"  WARN: tools/{script_name} not found in kit — skipping")

    # ── Done ──
    drift_note = (
        "  4 hooks installed: SessionStart, PostToolUse, PreCompact, Stop\n"
        "  Run manually: python tools/check_memory.py"
        if automated else
        "  Claude will manually diff JS functions on Start Session — no script needed"
    )
    print(f"""
Done. Memory system created in: {ROOT}

Next steps:
  1. Fill in CLAUDE.md — tech stack, file paths, coding conventions
  2. Open Claude Code and type: Start Session
  3. Claude will check memory, run drift detection, and report status

Drift detection:
{drift_note}

Task files (commit these to your repo):
  tasks/todo.md       — Claude writes plans here before touching code
  tasks/lessons.md    — corrections logged here, read every session start
  tasks/decisions.md  — architectural choices and why
  tasks/errors.md     — runtime errors, root causes, fixes

.gitignore:
  HANDOFF.md excluded — it's a point-in-time snapshot, not a long-lived doc

Skills (auto-invoked prompts):
  code-review/        — "review this file"
  security-check/     — "check for security issues"
  fix-bug/            — "fix the bug where..."
  new-feature/        — "add a feature that..."
  environment-check/  — "ready for prod", "before deploy"
  run-verification/   — "verify this works", "before I ship"
  refactor/           — "refactor", "clean up", "simplify this"
""")


if __name__ == "__main__":
    main()
