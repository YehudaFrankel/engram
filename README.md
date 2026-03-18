# Claude Code Memory Starter Kit

![Claude Code Memory Starter Kit](memory-starter-kit.png)

**Claude forgets everything when you close the session. This kit fixes that permanently.**

---

## The Problem

Every time you open Claude Code, you start from zero.

No memory of what you built. No record of why you made a decision. No knowledge of which bugs you already fixed. You spend the first 10 minutes re-explaining your project — every single session.

On a long project with a complex codebase, this compounds fast. Claude re-suggests things you already rejected. It breaks patterns you established three weeks ago. It asks questions you already answered.

This kit eliminates all of that.

---

## How It Works

Three plain-English commands run your entire memory system:

```
Start Session   →  Claude reads everything and picks up where you left off
End Session     →  Claude saves everything and confirms memory is clean
Check Drift     →  Claude compares live code against its memory and fixes gaps
```

Memory travels with your project as markdown files. No cloud sync, no API keys, no dependencies beyond Python.

---

## Real-World Test

This kit was stress-tested on a production Java course delivery platform — not a toy project.

**The codebase:**
- Java backend on Resin 2.1.17 (legacy server with non-standard compiler constraints)
- 5 JS files, 3 CSS files, 100+ documented functions
- Multi-page frontend (dashboard, admin panel, activity feed, catalog)
- Active scheduler, email system, encrypted URL handling

**What actually happened:**

- Sessions crashed mid-task — `Start Session` recovered full context every time, zero re-explanation needed
- A large new feature (~50 functions, ~100 CSS classes) was added across multiple sessions — drift detection caught everything undocumented automatically
- A non-obvious Resin 2.1.17 compiler bug (`$1.class` not generated for anonymous generic inner classes) was discovered, fixed, and permanently logged to `tasks/errors.md` — it will never cost a debugging session again
- A silent SQL apostrophe failure was traced, fixed, and captured — same story
- When a session ran out of context, `Start Session` loaded all lessons, decisions, and known errors in seconds

**The verdict:** The memory system held up across 88 sessions on a real production codebase. Context was never lost. Known bugs stayed known. The same mistake was never made twice.

---

## Quick Start

**Step 1 — Check Python**

```bash
python --version
```

No output? Install from [python.org/downloads](https://python.org/downloads) — check "Add to PATH" during install.

**Step 2 — Open your project in Claude Code**

```bash
cd your-project
claude
```

**Step 3 — Type this in chat**

```
Setup Memory
```

Claude asks a few questions (project name, tech stack, which files to track), then builds everything. Takes 2 minutes.

**From that point on:**

```
Start Session    ←  type this every morning
End Session      ←  type this when you're done
```

That's the entire routine.

---

## Commands

### Daily

| Command | What it does |
|---------|-------------|
| `Start Session` | Reads memory, runs drift check, reports where things stand |
| `End Session` | Saves session log, updates memory files, confirms clean |

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
| `"verify this works"` | Walks through your test checklist layer by layer |
| `"refactor this"` | Plan first, change second — no surprise rewrites |

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

On the production codebase this was tested on, the first drift check found 21 undocumented functions. After a major feed feature was added across multiple sessions, drift detection caught ~50 new functions and ~100 CSS classes before they could cause any inconsistencies.

Run it manually anytime:
```
Check Drift
```

Or let it run silently in the background — `.claude/settings.json` is pre-configured to trigger it after every save.

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
│   └── check_memory.py              ← Drift detector — runs after every file edit
└── .claude/
    ├── settings.json                ← Hooks config
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
        ├── environment-check/
        ├── run-verification/
        └── refactor/
```

Commit `tasks/` and `.claude/memory/` to your repo. Memory travels with the code — pull on a new machine, type `Install Memory`, done.

---

## The Four Task Files

These build up over time and make Claude genuinely smarter about your project:

| File | What it stores | Why it matters |
|------|---------------|----------------|
| `tasks/lessons.md` | Every correction you give Claude | Same mistake never happens twice |
| `tasks/errors.md` | Bugs fixed, root causes, fixes applied | Known bugs stay known forever |
| `tasks/decisions.md` | Architectural choices + reasons | Claude stops re-debating settled questions |
| `tasks/todo.md` | Plans written before any code changes | You always know what Claude is about to do |

Claude reads all four at the start of every session. The longer you use it, the sharper it gets.

---

## Session Crashes

Claude Code sessions die. API timeouts, context overflow, large image pastes — it happens.

When it does:

1. Open a new session
2. Type `Start Session`
3. Claude reads memory and continues where you left off

No re-explanation. No context loss. This was tested repeatedly on the production codebase above — it works exactly as described.

---

## Who This Is For

**Good fit:**
- Projects spanning multiple sessions or weeks
- Codebases with patterns, conventions, or constraints Claude needs to remember
- Anyone who has ever typed "as I mentioned before..." to Claude
- Teams where more than one person works with Claude on the same repo

**Not the right fit:**
- One-off scripts or throwaway projects
- If you only use Claude for isolated questions, not sustained development

---

## Known Limitations

- **No automated sync** — memory drift is caught by the script, but only if the script runs. If you skip `End Session` consistently, files go stale.
- **Combined memory entries break drift detection** — `js_functions.md` requires one function per row. Combined entries like `` `funcA` / `funcB` `` will only match the first one.
- **JS keyword false positives** — the class-method regex can match keywords like `for`, `if`, `switch` as function names. The included `JS_SKIP_NAMES` filter handles the common ones — extend it if you hit others.
- **Manual sync between project bundle and system path** — `End Session` handles this, but mid-session edits need a manual copy if you switch machines before ending the session.
- **Memory is as good as the descriptions** — `Analyze Codebase` documents what it finds, but descriptions are one-liners. For complex logic, write better descriptions manually.

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) installed and authenticated
- Python 3.7+ — [python.org/downloads](https://python.org/downloads)
- Nothing else

---

## No Terminal? Paste Into Chat Instead

Skip `setup.py` entirely — paste one of these directly into Claude Code:

**Claude asks you questions:**
> Set up the Claude memory system for this project. Ask me: project name, tech stack, which JS files to track, which CSS files to track, and CSS class prefix. Then create CLAUDE.md, STATUS.md, and all .claude/memory/ files.

**Tell Claude everything at once:**
> Bootstrap memory for this project. Name: [name]. Stack: [e.g. Node + React]. JS files: [list]. Create all memory files now.

**Claude figures it out automatically:**
> Analyze this codebase and set up the Claude memory system. Scan all JS, CSS, and backend files. Document everything. Create CLAUDE.md, STATUS.md, and .claude/memory/ files pre-filled with what you find.

**Minimal setup:**
> Set up a simple Claude memory system. Create: CLAUDE.md (Start Session, End Session, auto-save rules), STATUS.md (session log), and .claude/memory/notes.md (one file for functions, decisions, gotchas).

---

> Built across 88 real development sessions on a production codebase. The drift detector found 21 undocumented functions the first run. Skills were added after noticing the same prompts typed every day. Everything here came from actual use — nothing hypothetical.

**[YehudaFrankel/Claude-Code-memory-starter-kit](https://github.com/YehudaFrankel/Claude-Code-memory-starter-kit)**
