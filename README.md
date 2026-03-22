# Claude Recall — Persistent Context for Claude Code

[![v1.0.0](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/claude-recall/releases) [![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue?style=flat-square)](https://python.org/downloads) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code)

![Session demo — Start Session, drift detection, End Session](demo.gif)

**Claude starts from zero every session. This kit gives it a memory that compounds over time.**

If you're already using CLAUDE.md — this is the structured system that goes on top of it. If you're not — this sets everything up automatically.

**[The Problem](#the-problem) · [How It Works](#how-it-works) · [Quick Start](#quick-start) · [Commands](#commands) · [Drift Detection](#drift-detection--the-key-feature) · [Lifecycle Hooks](#lifecycle-hooks) · [What Gets Created](#what-gets-created) · [Known Limitations](#known-limitations)**

---

## The Problem

Every time you open Claude Code, you start from zero.

No memory of what you built yesterday. No record of why you made a decision. No knowledge of which bugs you already fixed. You spend the first 10 minutes re-explaining your project — every single session.

On a long project this compounds fast. Claude re-suggests approaches you already rejected. It breaks patterns you established weeks ago. It makes the same mistake twice.

This kit makes Claude do it automatically — every session, two commands, 10 seconds.

---

## How It Works

Two commands run your entire memory system:

```
Start Session   →  Claude reads everything and picks up where you left off
End Session     →  Claude logs what happened and keeps memory current
```

At End Session, Claude writes to four files that accumulate over time:

| File | What gets logged |
|------|-----------------|
| `tasks/lessons.md` | Every correction you gave Claude |
| `tasks/errors.md` | Every bug fixed, root cause, and solution |
| `tasks/decisions.md` | Every architectural choice and why |
| `tasks/todo.md` | Plans written before any code changes |

By session 20, Claude knows your patterns. By session 50, it knows your codebase better than any fresh context ever could. The same mistake never happens twice.

Memory travels with your project as markdown files. No cloud sync, no API keys, no dependencies beyond Python.

---

## Real-World Test

Stress-tested across 100 sessions on a production Java platform — legacy backend, 5 JS files, 100+ functions, multi-page frontend with scheduler, email system, and encrypted URL handling.

**What actually happened:**

- Sessions crashed mid-task — `Start Session` recovered full context every time, zero re-explanation needed
- A large new feature (~50 functions, ~100 CSS classes) was added across multiple sessions — drift detection caught everything undocumented automatically
- A non-obvious Resin 2.1.17 compiler bug (`$1.class` not generated for anonymous generic inner classes) was discovered, fixed, and permanently logged to `tasks/errors.md` — it will never cost a debugging session again
- When a session ran out of context, `Start Session` loaded all lessons, decisions, and known errors in seconds

**The verdict:** Context was never lost. Known bugs stayed known. The same mistake was never made twice.

---

## Quick Start

**Requires:** Python 3.7+ · [Claude Code](https://claude.ai/claude-code)

**Step 1 — Clone the kit**

```bash
git clone https://github.com/YehudaFrankel/claude-recall.git
```

**Step 2 — Run setup in your project**

```bash
cd your-project
python /path/to/claude-recall/setup.py
```

Claude asks a few questions (project name, tech stack, which files to track), then builds everything. Takes 2 minutes.

**Step 3 — Open Claude Code and start working**

```bash
claude
```

Then type:

```
Start Session    ←  type this every morning
End Session      ←  type this when you're done
```

That's the entire routine. Sessions crash? Open a new one, type `Start Session` — Claude reads memory and continues where you left off.

<details>
<summary>▸ No terminal? Paste into chat instead</summary>

> Analyze this codebase and set up the Claude memory system. Scan all JS, CSS, and backend files. Document everything. Create CLAUDE.md, STATUS.md, and .claude/memory/ files pre-filled with what you find.

Or ask Claude to set it up interactively — it will ask you for project name, stack, and which files to track.

</details>

---

## Commands

### Daily

| Command | What it does |
|---------|-------------|
| `Start Session` | Reads memory, runs drift check, reports where things stand |
| `End Session` | Runs `/learn` first, then saves session log, updates memory files, confirms clean |
| `/learn` | Extracts patterns and lessons from current session into `tasks/lessons.md` — run anytime, auto-runs at End Session |
| `/evolve` | Reviews accumulated lessons and clusters repeated patterns into new reusable skills |
| `"Should I compact?"` | Evaluates context length and guides through safe compaction without losing memory |

### Drift & Analysis

| Command | What it does |
|---------|-------------|
| `Check Drift` | Scans live code vs memory — finds undocumented functions, stale entries, new CSS classes |
| `Analyze Codebase` | Full scan of all JS, CSS, and backend files — documents everything it finds |
| `Code Health` | Finds leftover `console.log`, hardcoded values, dead code, missing error handling |

### Setup & Recovery

| Command | What it does |
|---------|-------------|
| `Setup Memory` | First-time setup — creates all memory files |
| `Install Memory` | New machine — copies memory files to Claude's system path |
| `Update Kit` | Pull latest kit updates safely — your memory files are never touched |

### Planning & Debugging

| Command | What it does |
|---------|-------------|
| `Estimate: [task]` | Complexity rating, file list, risk flags, written plan — before any code changes |
| `Debug Session` | Structured diagnosis: reproduce → isolate → hypothesize → fix → verify → log |
| `Handoff` | Generates `HANDOFF.md` — current state, next tasks, key decisions, known bugs |

### Skills (auto-triggered)

Skills fire automatically when you describe a situation. You don't invoke them — Claude recognizes the context.

| What you say | What Claude does |
|-------------|-----------------|
| `"fix the bug where..."` | Root cause first, fix second, log to errors.md |
| `"review this file"` | Dead code, missing error handling, convention violations |
| `"check for security issues"` | SQL injection, missing auth, exposed data |
| `"is this ready for prod"` | Finds hardcoded dev values, runs deploy checklist |
| `"refactor this"` | Plan first, change second — no surprise rewrites |
| `/learn` | Extracts patterns and lessons from current session into lessons.md |
| `/evolve` | Clusters repeated lessons into new reusable skills automatically |
| `"should I compact?"` | Guides safe context compaction without losing memory |

Generate a starter skill set tailored to your stack:
```
Generate Skills
```

---

## Drift Detection — The Key Feature

Most memory systems are static. You document things once and they slowly go stale. You don't find out until Claude confidently suggests something that no longer exists.

This kit runs a drift detector (`check_memory.py`) automatically after every file edit. It compares your live code against Claude's memory files and flags:

- **Functions in code but not in memory** — new code Claude doesn't know about yet
- **Functions in memory but not in code** — deleted code Claude still thinks exists
- **CSS classes added or removed** — caught before they cause confusion

**What drift output looks like** — when Claude sees this, it updates memory immediately before continuing:

```
DRIFT DETECTED
  JS functions not in memory (3):
    - submitForm
    - resetPanel
    - loadUserData
  CSS classes not in memory (1):
    - .card--highlighted
Run 'Analyze Codebase' to update memory.
```

No drift → silent, zero interruption. Run it manually anytime: `Check Drift`

---

## Lifecycle Hooks

Three additional hooks run automatically at key points in every session. No commands needed.

### SessionStart — loads memory automatically
Runs when you open Claude Code. Injects `STATUS.md` and `MEMORY.md` into context before your first message. Claude starts warm without you typing `Start Session`.

### PreCompact — survives `/compact`
Runs before Claude compacts the conversation. Reinjects your memory files into the compacted context. **Best practice:** run `/learn` first to capture session patterns, then `/compact` freely.

### Stop — auto-captures session journal + catches forgotten End Session
Runs when Claude finishes responding. First, `session_journal.py` reads every file you edited this session and the current STATUS.md phase, then writes a timestamped entry to `memory/session_journal.md` — searchable forever, no `/learn` needed. Second, checks whether memory files have unsaved changes. If they do, you see: *"Memory has unsaved changes. Run End Session to push."* Silent otherwise.

All three hooks ship as Python scripts in `tools/` so they work on any OS.

---

## What Gets Created

```
your-project/
├── CLAUDE.md                        ← Claude reads this every session (stack, conventions, patterns)
├── STATUS.md                        ← Full session log — date + what changed each session
├── update.py                        ← Safe kit updater (shows diff, asks before applying)
├── tasks/
│   ├── todo.md                      ← Plans written before touching code
│   ├── lessons.md                   ← Every correction logged — never repeat a mistake
│   ├── decisions.md                 ← Why things were built the way they were
│   └── errors.md                    ← Bugs fixed, root causes, fixes applied
├── tools/
│   ├── check_memory.py              ← Drift detector — runs after every Edit/Write
│   ├── session_start.py             ← Injects memory on SessionStart
│   ├── precompact.py                ← Preserves memory through /compact
│   ├── session_journal.py           ← Auto-captures session summary on every Stop
│   ├── bootstrap.py                 ← Zero-setup codebase indexer — run on any new project
│   └── stop_check.py               ← Reminds you to End Session if unsaved changes
└── .claude/
    ├── settings.json                ← 4 hooks: drift · session start · compact · stop+journal
    ├── memory/
    │   ├── MEMORY.md                ← Index — auto-loaded every session
    │   ├── project_status.md        ← What's built, what's not, key decisions
    │   ├── js_functions.md          ← Every JS function with description
    │   ├── html_css_reference.md    ← Every HTML section and CSS class
    │   ├── backend_reference.md     ← Every API endpoint and DB pattern
    │   └── user_preferences.md      ← How you like Claude to work
    └── skills/
        ├── fix-bug/
        ├── code-review/
        ├── security-check/
        ├── new-feature/
        ├── learn/              ← /learn — extract session patterns to lessons.md
        ├── evolve/             ← /evolve — cluster lessons into new skills
        ├── strategic-compact/  ← guides safe context compaction
        ├── search-first/       ← research before coding — find existing implementations
        ├── verification-loop/  ← compile + smoke test + self-evaluation after changes
        └── java-reviewer/      ← deep Java review against your stack's patterns
```

Commit `tasks/` and `.claude/memory/` to your repo. Memory travels with the code — pull on a new machine, type `Install Memory`, done.

---

## Known Limitations

- **No automated sync** — memory files need `End Session` to be pushed to git. The Stop hook reminds you when there are unsaved changes, but it won't push automatically.
- **Combined memory entries break drift detection** — `js_functions.md` requires one function per row. Combined entries like `` `funcA` / `funcB` `` will only match the first one.
- **JS keyword false positives** — the class-method regex can match keywords like `for`, `if`, `switch` as function names. The included `JS_SKIP_NAMES` filter handles the common ones — extend it if you hit others.
- **Memory is as good as the descriptions** — `Analyze Codebase` documents what it finds, but descriptions are one-liners. For complex logic, write better descriptions manually.

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) installed and authenticated
- Python 3.7+ — [python.org/downloads](https://python.org/downloads)
- Nothing else

---

> Built across 100 real development sessions on a production codebase. The drift detector found 21 undocumented functions the first run. Skills were added after noticing the same prompts typed every day. session_journal.py and bootstrap.py came from comparing workflows and finding what was still missing. Everything here came from actual use — nothing hypothetical.

---

If claude-recall saved you from re-explaining your codebase one more time, **[⭐ star it on GitHub](https://github.com/YehudaFrankel/claude-recall)** — it helps others find it.

**[YehudaFrankel/claude-recall](https://github.com/YehudaFrankel/claude-recall)**
