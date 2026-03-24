# Claude Recall — The Living System for Claude Code

[![v2.0.0](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/claude-recall/releases) [![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue?style=flat-square)](https://python.org/downloads) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code)

![Session demo](demo.gif)

**Memory that syncs. Skills that evolve. Sessions that compound — not reset.**

Claude Code is stateless. Every session starts from zero — no memory of yesterday's decisions, no record of bugs already fixed, no knowledge of the approach you rejected last week. You re-explain. Claude re-suggests the same things. The same mistake happens twice.

Claude Recall is a living system on top of Claude Code. It doesn't just store context — it grows with your project, improves its own skills from failure data, and runs multi-step workflows without human checkpoints between each step.

No API keys. No background service. No database. Plain markdown files that git already knows how to handle.

**[Three Tiers](#three-tiers) · [Quick Start](#quick-start) · [What Ships](#what-ships-out-of-the-box) · [Learning Loop](#skills-fix-their-own-mistakes) · [Autonomous](#workflows-run-themselves) · [Every Command](#every-command) · [Architecture](#architecture) · [Hooks](#lifecycle-hooks) · [Modes](#two-modes) · [File Tree](#what-gets-created) · [Results](#real-results) · [FAQ](#faq)**

---

## Before and After

**Without Claude Recall:**
```
Monday:    explain your project → work → close
Tuesday:   explain your project again → work → close
Wednesday: explain again → re-fix a bug you already fixed → close
```

**With Claude Recall:**
```
Monday:    Start Session → work → End Session
Tuesday:   Start Session → Claude remembers everything → work → End Session
Wednesday: Start Session → lessons from Monday applied automatically → better work
```

---

## Three Tiers

Most Claude setups are Tier 1 — a CLAUDE.md file and nothing else. Claude Recall ships all three.

**Tier 1 — Memory Persistence**
Persistent context across sessions. Codebase knowledge, decisions, known bugs, rejected approaches. Syncs to git. Travels with the code. Applied at every `Start Session` before any code is touched.

**Tier 2 — Skills That Self-Improve**
Auto-triggered workflows from plain English. Each skill scores itself on every use (`skill_scores.md`). `/evolve` reads the scores and patches failing steps — the compound learning loop closes without manual intervention. Skills chain into multi-step workflows via `## Auto-Chain`.

**Tier 3 — Autonomous Operation**
Skill chaining, self-healing, drift detection, and auto end-session run without prompting. Claude works through multi-step tasks without human checkpoints between steps.

---

## Quick Start

**Requires:** Python 3.7+ · [Claude Code](https://claude.ai/claude-code)

```bash
# 1. Clone once
git clone https://github.com/YehudaFrankel/claude-recall.git

# 2. Run setup in your project (~2 minutes)
cd your-project
python /path/to/claude-recall/setup.py

# 3. Inside Claude Code — every session from here on:
Start Session    ←  reads memory, applies lessons, picks up where you left off
End Session      ←  extracts lessons, syncs memory, done
```

Setup asks about your stack, configures itself, and builds everything automatically.

| | Heavy tools | Claude Recall |
|---|---|---|
| API key | required | none |
| Background service | running | none — plain files |
| Database | setup required | markdown + git |
| Framework lock-in | yes | any project, any stack |
| Setup time | 30–60 min | ~5 minutes |

No terminal? Paste this into Claude Code chat instead:
> Analyze this codebase and set up the Claude memory system. Scan all JS, CSS, and backend files. Create CLAUDE.md, STATUS.md, and .claude/memory/ pre-filled with what you find.

---

## Your Daily Routine

```
Morning:   "Start Session"
           → reads all memory, applies lessons from past sessions,
             runs drift check, picks up exactly where you left off

[work on your project — describe what you need in plain English]

Evening:   "End Session"
           → runs /learn, logs what changed, saves everything to memory
```

Two commands. Everything else is automatic.

---

## What Ships Out of the Box

### Skills — fire automatically from plain English

| Skill | What triggers it | What it does |
|-------|-----------------|-------------|
| `plan` | "plan [feature]", "I want to build X" | Structured planning — options with ratings, decision logged live, full plan auto-displayed after every update |
| `fix-bug` | "fix the bug where..." | Root cause first, fix second, logs so it never happens again |
| `code-review` | "review this file" | Dead code, missing error handling, convention violations |
| `security-check` | "check for security issues" | SQL injection, missing auth, exposed sensitive data |
| `new-feature` | "add a new..." | Searches existing patterns first, then builds — no duplicate code |
| `verification-loop` | "verify this works", "before I ship" | Compile + smoke test + self-check after every change |
| `search-first` | "add new endpoint/feature" | Research before coding — finds existing implementations |
| `strategic-compact` | "should I compact?" | Safe context compaction without losing memory |
| `learn` | `/learn`, "End Session" | Extracts lessons, scores skills, logs velocity |
| `evolve` | `/evolve` | Patches failing skills, clusters patterns into new skills |
| `java-reviewer` | "review this java" | Deep Java review against your stack's specific patterns |

Type `Generate Skills` and Claude creates additional skills tailored to your exact stack and file structure.

### Tools — run silently in the background

| Tool | When it runs | What it does |
|------|-------------|-------------|
| `check_memory.py` | After every file edit | Drift detector — catches undocumented functions and CSS changes immediately |
| `session_journal.py` | After every response | Auto-captures what you worked on — searchable forever, no /learn needed |
| `stop_check.py` | After every response | Reminds you to save memory when unsaved changes detected; surfaces open plans with unresolved questions |
| `bootstrap.py` | On first setup | Scans your entire codebase and generates a quick index — immediate codebase awareness |
| `session_start.py` | When Claude Code opens | Injects memory into context before your first message — Claude starts warm |
| `precompact.py` | Before `/compact` | Reinjects memory into the compacted context — nothing lost through compaction |

---

## Skills Fix Their Own Mistakes

When a built-in skill gets something wrong and you correct it, that correction gets logged. Run `/evolve` every few sessions and it rewrites the exact failing step using your failure data.

This is the **compound learning loop** — an agentic feedback cycle where skills score themselves, failures get logged with precision, and `/evolve` closes the loop by patching the right step:

```
session work
     ↓
/learn  →  lessons.md       (what was learned this session)
        →  decisions.md     (what was settled — never re-debated)
        →  skill_scores.md  (Y = needed correction, N = worked first time)
        →  velocity.md      (estimated vs actual — self-calibrating estimates)
                ↓
         /evolve  →  finds skills where Correction = Y, Improvement = pending
                  →  reads "What Failed" column → patches the exact step
                  →  clusters repeated lessons into new reusable skills
                  →  logs every change to skill_improvements.md
                ↓
         better skills next session — automatically
```

Run `/learn` before `End Session`. Run `/evolve` every 3–5 sessions. The same mistake is architecturally impossible after `/evolve` runs.

### What gets smarter over time

| File | What it tracks | Effect |
|------|---------------|--------|
| `lessons.md` | Every pattern + fix extracted by /learn | Applied before any code is touched each session |
| `decisions.md` | Settled architectural choices | Claude never re-debates what's already decided |
| `skill_scores.md` | Binary pass/fail per skill per session | /evolve uses this to patch failing steps |
| `regret.md` | Approaches tried and rejected | Never re-proposed — saves re-litigating bad ideas |
| `velocity.md` | Estimated vs actual sessions per task | After 20+ entries, estimates reflect real track record |
| `global-lessons.md` | Lessons that apply across all projects | Loaded at Start Session across every project you use |

---

## It Stays Accurate Without Effort

Most memory tools go stale — you document once, code moves on. Claude Recall runs `check_memory.py` after every file edit. It compares live code against Claude's memory and flags undocumented changes:

```
DRIFT DETECTED
  JS functions not in memory (2):
    - submitForm
    - resetPanel
  CSS classes not in memory (1):
    - .card--highlighted
→ memory updated automatically
```

Silent when clean. No manual updates needed.

**Starting fresh on an existing project?** Run `bootstrap.py` once — it scans your entire codebase and generates `quick_index.md`, a grouped map of every source file by type. Gives Claude immediate awareness of a project it's never seen before, without any manual documentation.

---

## Workflows Run Themselves

Three autonomous behaviors ship out of the box — no commands needed:

**Skill chaining** — add `## Auto-Chain` to any skill and it triggers the next step automatically:
```
fix-bug → verification-loop → smoke-test
               ↓ if fail
           debug-topic → smoke-test
```
No human steps between. Claude reads the chain and runs it. Build your own chains by adding one section to any skill file.

**Self-healing** — when a verify step fails, Claude attempts the minimal fix and retries once before escalating. Add a `## Recovery` section to define what "minimal fix" means for that skill.

**Unsaved memory reminder** — the stop hook monitors every response. When memory has unsaved changes, it surfaces a reminder to run `End Session`. Also surfaces any open plans with unresolved questions. Works with or without git.

---

## It Works on Any Machine

Memory is stored as plain markdown files, synced to git. Pull your project on a new machine and Claude is fully up to speed:

```bash
git pull
Install Memory    ←  inside Claude Code — copies memory to Claude's system path
Start Session     ←  Claude knows everything: all lessons, decisions, skills
```

---

## Every Command

### Daily
| Command | What it does |
|---------|-------------|
| `Start Session` | Reads memory, applies lessons, surfaces open plans, picks up where you left off |
| `End Session` | Runs /learn, updates STATUS.md, scans plans, syncs all memory files |
| `Plan [feature]` | Structured planning — options with ratings, decision logged live, full plan auto-displayed |
| `Show Plan` | Display full current plan file — no summary, always the complete document |
| `/learn` | Extracts lessons, scores skills (Y/N), logs velocity — auto-runs at End Session |
| `/evolve` | Patches failing skills, clusters repeated patterns into new reusable skills |
| `Should I compact?` | Guides safe context compaction without losing memory |

### Analysis
| Command | What it does |
|---------|-------------|
| `Check Drift` | Manually run the drift detector — find undocumented functions and stale entries |
| `Analyze Codebase` | Full scan of all JS, CSS, and backend — documents every function, class, and endpoint |
| `Code Health` | Finds leftover `console.log`, hardcoded values, dead code, missing error handling — reports file + line |

### Setup and recovery
| Command | What it does |
|---------|-------------|
| `Setup Memory` | First-time setup — creates all memory files for your project |
| `Install Memory` | New machine — copies memory files to Claude's system path |
| `Generate Skills` | Auto-creates skills tailored to your actual stack, file names, and patterns |
| `Update Kit` | Pulls latest kit safely — only the kit commands block in CLAUDE.md is ever touched; your memory, skills, and code are never modified |

### Planning
| Command | What it does |
|---------|-------------|
| `Estimate: [task]` | Complexity rating, list of files that will change, risk flags, written plan — before any code |
| `Debug Session` | Structured diagnosis: reproduce → isolate → hypothesize → fix → verify → log to regret.md |
| `Handoff` | Generates `HANDOFF.md` — current state, next 3 tasks, key decisions, known bugs, how to start |

---

## Architecture

Three tiers — most memory tools ship only the first.

**Tier 1 — Memory**
Persistent context across sessions. Codebase knowledge, decisions, known bugs, rejected approaches. Syncs to git. Travels with the code. Applied at every `Start Session` before any code is touched.

**Tier 2 — Skills**
Auto-triggered workflows from natural language. Each skill scores itself on every use (`skill_scores.md`). `/evolve` reads the scores and patches failing steps — the compound learning loop closes without manual intervention. Skills can chain into multi-step workflows via `## Auto-Chain`.

**Tier 3 — Autonomous**
Skill chaining, self-healing, drift detection, and auto end session run without prompting. Claude works through multi-step tasks without human checkpoints between steps.

---

## Lifecycle Hooks

Four hooks run automatically — no commands needed, no configuration required.

| Hook | When it fires | What it does |
|------|--------------|-------------|
| `SessionStart` | Every time Claude Code opens | Runs `session_start.py` — injects STATUS.md and MEMORY.md into context before your first message. Claude starts warm without typing `Start Session`. |
| `PostToolUse` | After every Edit or Write | Runs `check_memory.py --silent` — catches drift immediately after every file change, not just at End Session. |
| `PreCompact` | Before Claude compacts the conversation | Runs `precompact.py` — reinjects memory files into the compacted context. Run `/learn` first to capture session patterns, then `/compact` freely. |
| `Stop` | After every response | Runs `session_journal.py` (auto-captures session summary) then `stop_check.py` (reminds you to save memory; surfaces open plans with unresolved questions). |

All hooks are Python scripts in `tools/` — cross-platform, no dependencies beyond Python.

---

## Two Modes

Setup offers two modes based on your project size:

| | Full | Lite |
|---|---|---|
| Memory files | 5 separate files (js_functions, html_css, backend, project_status, user_preferences) | 1 notes file |
| Drift detection | Automated — runs after every edit | Manual — run `Check Drift` yourself |
| Session journal | Auto-captured on every Stop | Not included |
| Best for | Multi-file projects, teams, long-running codebases | Quick experiments, small solo projects |
| Upgrade later? | — | Yes — one command |

You can always upgrade from Lite to Full later by running `Setup Memory` again.

---

## Update Kit

`Update Kit` pulls the latest version safely. It shows you exactly what will change and asks for confirmation before applying anything.

**What it never touches:**
- Your memory files (`.claude/memory/`)
- Your skills (`.claude/skills/`)
- Your code
- Everything below `## What This Project Is` in CLAUDE.md — your project-specific content

**What it updates:**
- The kit commands block in CLAUDE.md (Start Session, End Session, etc.)
- The `tools/` scripts (bug fixes, new features)
- Kit-level settings in `settings.json`

```bash
Update Kit                                    ←  pull from default GitHub repo
Update Kit from https://github.com/user/repo  ←  pull from a fork or branch
python update.py                              ←  same thing, from terminal
```

---

## What Gets Created

```
your-project/
├── CLAUDE.md                        ← Claude's instructions for this project
├── STATUS.md                        ← Full session log — date + what changed
├── update.py                        ← Safe kit updater
├── tools/
│   ├── check_memory.py              ← Drift detector — PostToolUse hook
│   ├── session_start.py             ← Memory injector — SessionStart hook
│   ├── precompact.py                ← Memory preserver — PreCompact hook
│   ├── session_journal.py           ← Session auto-capture — Stop hook
│   ├── stop_check.py               ← Unsaved changes + open plan reminders — Stop hook
│   └── bootstrap.py                ← Codebase indexer — run once on new projects
└── .claude/
    ├── settings.json                ← 4 hooks configured
    ├── memory/
    │   ├── MEMORY.md                ← Index — auto-loaded every session
    │   ├── lessons.md               ← Lessons from /learn — applied each session
    │   ├── decisions.md             ← Settled decisions — never re-debated
    │   ├── project_status.md        ← What's built, what's in progress
    │   ├── js_functions.md          ← Every JS function with description
    │   ├── html_css_reference.md    ← Every HTML section and CSS class
    │   ├── backend_reference.md     ← Every API endpoint and DB pattern
    │   ├── user_preferences.md      ← How you like Claude to work — tone, rules, style
    │   └── tasks/
    │       ├── skill_scores.md      ← Skill report card — /evolve reads this
    │       ├── skill_improvements.md← What /evolve patched and why
    │       ├── regret.md            ← Rejected approaches — never re-proposed
    │       └── velocity.md          ← Estimated vs actual — self-calibrating
    ├── memory/
    │   └── plans/
    │       └── _template.md         ← Plan template — one file per feature
    └── skills/
        ├── plan/                    ← Structured planning mode
        ├── learn/
        ├── evolve/
        ├── fix-bug/
        ├── code-review/
        ├── security-check/
        ├── new-feature/
        ├── verification-loop/
        ├── strategic-compact/
        ├── search-first/
        └── java-reviewer/
```

Commit `.claude/memory/` and `.claude/skills/` to your repo. Memory and skills travel with the code.

---

## Real Results

Tested across **112 real development sessions** on a production codebase — legacy Java backend, 5 JS files, 100+ functions, multi-page frontend with scheduler, email system, and encrypted URL handling. Not a demo project.

- Sessions crashed mid-task — `Start Session` recovered every time, zero re-explanation needed
- Skills patched themselves via `/evolve` — the same skill failure never happened twice
- A compiler bug was discovered, fixed, and logged permanently — it has never cost another debugging session
- 21 undocumented functions caught on the first drift detection run
- `velocity.md` reached 30+ entries — estimates now reflect actual track record instead of guessing

---

## FAQ

**What Claude plan do I need?**
Any paid plan that includes Claude Code. The kit itself has no plan requirements — it's plain markdown files and Python scripts. Longer sessions may benefit from Max due to context limits, but the PreCompact hook and `Start Session` recovery are specifically designed to handle those limits gracefully on any plan.

**Do I need to understand how it all works to use it?**
No. `Start Session` and `End Session` are the whole daily interface. Everything else runs automatically or responds to plain English descriptions.

**Does it work with any language or framework?**
Yes. Setup asks about your stack and configures drift detection, skills, and memory for what you're actually using. Java, Python, Node, Go, Ruby — any language with source files.

**What is user_preferences.md for?**
It's where Claude learns how you personally like to work — your communication style, things you never want it to do, coding conventions specific to you. It loads at every Start Session. Add anything to it: "always ask before refactoring", "never use semicolons", "I prefer short responses".

**What is global-lessons.md for?**
Lessons that aren't project-specific — things that apply to everything you build. Stored at `~/.claude/global-lessons.md` and loaded at Start Session on every project. Example: "always check .env before debugging auth issues."

**What does session_journal.md give me?**
A searchable history of every session — what files were edited, what the current phase was, timestamped automatically. You never manually write to it. Search it anytime: `Grep for "auth"` in session_journal.md to find every session where you worked on auth.

**What does bootstrap.py do?**
Scans your entire project on first run and generates `quick_index.md` — a grouped map of every source file by type (Java, JS, CSS, SQL, etc.). Gives Claude immediate codebase awareness without any manual documentation. Run it once on any new project.

**Does this work with Anthropic's native Auto Memory?**
Yes — they solve different problems. Anthropic's Auto Memory captures conversational context within a session. Claude Recall persists project knowledge across sessions: your codebase structure, architectural decisions, lessons from past mistakes, and custom workflows. Auto Memory forgets when the session closes. Claude Recall doesn't. Run both — they complement each other.

**Why markdown files instead of a database?**
Files you can read, diff, commit, and recover without any tooling. Memory stored in a database is opaque — you can't grep it, review it in a PR, or restore a version from last Tuesday. Markdown files travel with your repo, work on any machine with zero setup, and never require an API key or running service. The constraint is the feature.

**What makes it different from other Claude memory tools?**
Most memory tools are static — you document once and things go stale. Claude Recall is a living system: memory stays accurate via drift detection, skills improve via the compound learning loop, and sessions compound instead of reset. No other tool in this space ships the self-improving skills layer.

**What if I'm on a new computer?**
Pull your project, open Claude Code, type `Install Memory`. Claude is fully up to speed in seconds — all lessons, decisions, and skill improvements carried over.

**Does Update Kit overwrite my customizations?**
Never. It only updates the kit commands block in CLAUDE.md and the tools/ scripts. Your memory files, skills, code, and everything below `## What This Project Is` in CLAUDE.md are never touched.

**Can I customize the skills?**
Yes — every skill is a plain markdown file in `.claude/skills/`. Edit directly, or type `Generate Skills` and Claude creates new ones for your stack. Add `## Auto-Chain` to any skill to connect it into a workflow.

**What's the difference between Full and Lite mode?**
Full mode has 5 separate memory files and automated drift detection — best for multi-file projects. Lite mode has one notes file and manual drift checks — best for quick experiments. You can upgrade from Lite to Full at any time.

---

**Requires:** Python 3.7+ · [Claude Code](https://claude.ai/claude-code) · No other dependencies

If Claude Recall saved you from re-explaining your project one more time, **[⭐ star it on GitHub](https://github.com/YehudaFrankel/claude-recall)** — it helps others find it.
