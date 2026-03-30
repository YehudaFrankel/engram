# Clankbrain — The Living System for Claude Code

<p align="center"><img src="logo.jpeg" alt="Clankbrain" width="160" /></p>

[![v2.0.0](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/releases) [![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue?style=flat-square)](https://python.org/downloads) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code) [![Discussions](https://img.shields.io/badge/community-discussions-purple?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/discussions)

![Session demo](demo.gif?v=2)

**Memory that compounds. Skills that evolve. Sessions that build — not reset.**

Claude Code is stateless. Every session starts from zero — no memory of yesterday's decisions, no record of bugs already fixed, no knowledge of the approach you rejected last week. You re-explain. Claude re-suggests the same things. The same mistake happens twice.

Clankbrain is a living system on top of Claude Code. It doesn't just store context — it grows with your project, improves its own skills from failure data, and runs multi-step workflows without human checkpoints between each step.

No API keys. No background service. No database. Memory stays on your machine by default — nothing is pushed anywhere. Plain markdown files that git already knows how to handle.

**Using Clankbrain on a real project? [Tell us what you're building →](https://github.com/YehudaFrankel/clankbrain/discussions) · If it helped, [⭐ star it](https://github.com/YehudaFrankel/clankbrain) — it helps others find it.**


**[Three Tiers](#three-tiers) · [Quick Start](#quick-start) · [Examples](examples/) · [What Ships](#what-ships-out-of-the-box) · [Optional Skills](#optional-skills----install-when-you-need-them) · [Learning Loop](#skills-fix-their-own-mistakes) · [Autonomous](#workflows-run-themselves) · [Every Command](#every-command) · [Architecture](#architecture) · [Hooks](#lifecycle-hooks) · [Modes](#two-modes) · [File Tree](#what-gets-created) · [Results](#real-results) · [FAQ](#faq)**

---

## Before and After

**Without Clankbrain:**
```
Monday:    explain your project → work → close
Tuesday:   explain your project again → work → close
Wednesday: explain again → re-fix a bug you already fixed → close
```

**With Clankbrain:**
```
Monday:    Start Session → work → End Session
Tuesday:   Start Session → Claude remembers everything → work → End Session
Wednesday: Start Session → lessons from Monday applied automatically → better work
```

---

## Three Tiers

Most Claude setups are Tier 1 — a CLAUDE.md file and nothing else. Clankbrain ships all three.

**Tier 1 — Memory Persistence**
Persistent context across sessions. Codebase knowledge, decisions, known bugs, rejected approaches. Syncs to git. Travels with the code. Applied at every `Start Session` before any code is touched.

**Tier 2 — Skills That Self-Improve**
Auto-triggered workflows from plain English. Each skill scores itself on every use (`skill_scores.md`). `/evolve` reads the scores and patches failing steps — the compound learning loop closes without manual intervention. Skills chain into multi-step workflows via `## Auto-Chain`.

**Tier 3 — Autonomous Operation**
Skill chaining, self-healing, drift detection, and auto end-session run without prompting. Claude works through multi-step tasks without human checkpoints between steps.

---

## Quick Start

**Claude forgets everything when a session closes. Clankbrain fixes that — your codebase, your decisions, your past mistakes, permanent across every session and every IDE.**

**Requires:** [Claude Code](https://claude.ai/claude-code) · Python 3.7+ for Full mode (Lite is zero-Python)

```bash
# Claude Code (default)
npx clankbrain

# Cursor
npx clankbrain --ide cursor

# Windsurf
npx clankbrain --ide windsurf

# All IDEs at once
npx clankbrain --ide all
```

> **Warp and GitHub Copilot** get clankbrain automatically — they both read `CLAUDE.md` natively. No extra flag needed.

```
# Every session, in any IDE:
Start Session    ←  reads memory, applies lessons, picks up where you left off
End Session      ←  extracts lessons, saves memory locally, done
```

<details>
<summary>Other install options</summary>

**Git clone:**
```bash
git clone https://github.com/YehudaFrankel/clankbrain.git
cd clankbrain
python setup.py
```

**Python one-liner (no Node required):**
```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/YehudaFrankel/clankbrain/main/setup.py').read().decode())"
```

**Manual:** Download and run `setup.py` directly from the repo.
</details>

Setup auto-detects your project name and tech stack from the folder — no questions asked.

**New here?** Start with [`examples/first-week.md`](examples/first-week.md) — day-by-day guide showing what changes as the system learns your project. [`examples/session-walkthrough.md`](examples/session-walkthrough.md) shows a full Start → plan → edit → verify → End session in detail.

| | Heavy tools | Clankbrain |
|---|---|---|
| API key | required | none |
| Background service | running | none — plain files |
| Database | setup required | markdown + git |
| Data leaves machine | yes | never — local by default |
| Framework lock-in | yes | any project, any stack |
| Config needed | varies | none — auto-detected from folder |
| GitHub account needed | sometimes | no — sync is optional |
| IDE lock-in | varies | Claude Code, Cursor, Windsurf, Warp, Copilot |
| Setup time | 30–60 min | ~5 minutes |

No terminal? Paste this into Claude Code chat instead:
> Analyze this codebase and set up the Claude memory system. Scan all JS, CSS, and backend files. Create CLAUDE.md, STATUS.md, and .claude/memory/ pre-filled with what you find.

---

## Two Modes

Setup asks which mode fits your project:

| | Full | Lite |
|---|---|---|
| Memory files | 5 separate files (js_functions, html_css, backend, project_status, user_preferences) | 1 notes file |
| Static conventions | Inline in CLAUDE.md | `@rules/` files (stack.md, conventions.md, decisions.md) |
| Drift detection | Automated — runs after every edit via `memory.py` | None — no Python required |
| Session journal | Auto-captured on every Stop | Not included |
| Python required | Yes (3.7+) | **No — zero Python** |
| Best for | Multi-file projects, teams, long-running codebases | Quick experiments, small solo projects |
| Upgrade later? | — | Yes — `python upgrade.py` |

**Not sure?** Start with Lite — it's instant, requires nothing. Upgrade when you need drift detection.

### Upgrade to Full

When you outgrow Lite mode, type this in Claude Code:

```
Upgrade to Full
```

Claude runs `upgrade.py`, which downloads `tools/memory.py`, adds lifecycle hooks to `.claude/settings.json`, and keeps your `@rules/` files in parallel. Restart Claude Code after running.

```bash
python upgrade.py   ←  same thing, from terminal
```

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
| `verification-loop` | "verify this works", "before I ship" | Compile + smoke test + self-check after every change |
| `search-first` | "add new endpoint/feature" | Research before coding — finds existing implementations |
| `strategic-compact` | "should I compact?" | Safe context compaction without losing memory |
| `learn` | `/learn`, "End Session" | Extracts lessons, scores skills, logs velocity |
| `evolve` | `/evolve` | Patches failing skills, clusters patterns into new skills |
| `code-reviewer` | "review this", "check this code" | Reviews code against your project's past lessons, locked decisions, and stack-specific patterns — gets smarter every session |

Type `Generate Skills` and Claude creates additional skills tailored to your exact stack and file structure — fix-bug, code-review, security-check, new-feature, and more, configured for your actual file names and patterns.

### Optional Skills — install when you need them

Skills that ship in the kit but aren't wired up by default. Add any of them with a single command.

| Skill | Install command | What it does |
|-------|----------------|-------------|
| `map-codebase` | `Install the map-codebase skill` | Analyzes your codebase and builds a `code-map.md` organized by feature flow — entry point → JS → endpoint → logic → DB for every major flow. Includes a line-number reference for large files. Run once to bootstrap navigation; re-run after major structural changes. |

**How to install:** Tell Claude `Install the map-codebase skill` and it copies the skill file into your project's `.claude/skills/` folder and optionally wires the output into `CLAUDE.md` as a persistent reference.

### Tools — run silently in the background

One file, `tools/memory.py`, runs all lifecycle behaviors via subcommands:

| Subcommand | When it runs | What it does |
|------------|-------------|-------------|
| `--check-drift` | After every file edit | Drift detector — catches undocumented functions and CSS changes immediately |
| `--verify-edit` | After every Edit or Write | Requires Claude to quote the changed lines verbatim back to you — not a summary, the actual file content |
| `--journal` | After every response | Auto-captures what you worked on — searchable forever, no /learn needed |
| `--stop-check` | After every response | Reminds you to save memory; surfaces open plans and code-review nudge after significant edits |
| `--session-start` | When Claude Code opens | Injects memory into context; runs silent kit health check — flags broken wiring before you start |
| `--quick-learn` | On demand | Fast lesson capture — writes a stub placeholder immediately, then prompts Claude to fill in 1-3 lessons. No /learn ceremony. |
| `--kit-health` | On demand (`Kit Health`) | Checks all kit components: hooks wired, MEMORY.md present, skills installed, complexity profile fresh |
| `--regret-guard` | Before every prompt (UserPromptSubmit) | Scans `regret.md` + `decisions.md` for entries matching the current task — injects relevant warnings before you start. Nobody else does this. |
| `--decision-guard` | Before every planning prompt (UserPromptSubmit) | Detects planning language, cross-checks `decisions.md`, warns if the proposed approach contradicts a settled decision |
| `--context-score` | On demand (`Context Score`) | Scores every `## section` in `CLAUDE.md` by how often it appears in session journals — surfaces dead weight bloating your context |
| `--velocity-estimate "task"` | On demand (`Estimate: [task]`) | Keyword-matches the task against `velocity.md` history, reports what similar tasks actually took vs what was estimated |
| `--mine-patterns` | On demand (`Mine Patterns`) | Clusters all `lessons.md` entries by keyword frequency — surfaces recurring mistakes you haven't noticed yet |
| `--error-lookup` | Before every debug prompt (UserPromptSubmit) | Matches debug-flavored prompts against `error-lookup.md` — injects known cause + fix before you start investigating |
| `--guard-check` | On demand (`Guard Check`) | Runs all named guards from `guard-patterns.md` against the codebase — extracts and executes each guard's grep strategy, reports violations |
| `--bootstrap` | On first setup | Scans your entire codebase and generates a quick index — immediate codebase awareness |
| `--complexity-scan` | First `Start Session` on a new project | Detects stack, DB, tests, API surface — scores complexity Low/Medium/High and recommends which skills to use. Auto-refreshes after 30 days. |
| `--precompact` | Before `/compact` | Reinjects memory into the compacted context — nothing lost through compaction |
| `--search "query"` | On demand | Full-text search across all memory `.md` files — scored results with ±2 lines of context. `--top N` limits results (default 5). |

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
| `error-lookup.md` | Known errors → cause → fix | `--error-lookup` hook surfaces the fix before you start investigating |
| `critical-notes.md` | Non-obvious gotchas about the codebase | Prevents re-discovering the same landmine session after session |
| `agreed-flow.md` | User journeys locked by agreement | Scope anchor — stops "let's change how this works" conversations mid-build |
| `velocity.md` | Estimated vs actual sessions per task | After 20+ entries, estimates reflect real track record |
| `global-lessons.md` | Lessons that apply across all projects | Loaded at Start Session across every project you use |

---

## It Stays Accurate Without Effort

Most memory tools go stale — you document once, code moves on. Clankbrain runs `memory.py --check-drift` after every file edit. It auto-detects all JS and CSS files, compares live code against Claude's memory, and flags undocumented changes:

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

**Starting fresh on an existing project?** Run `python tools/memory.py --bootstrap` once — it scans your entire codebase and generates `quick_index.md`, a grouped map of every source file by type. Gives Claude immediate awareness of a project it's never seen before, without any manual documentation.

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

## Cross-Machine Sync (opt-in, not required)

**Default setup needs no GitHub account, no repo, and no configuration — name and stack are auto-detected from your folder.**

Memory lives in `.claude/memory/` on your machine. Nothing leaves unless you explicitly set this up. Skip this entire section if you work on one machine.

If you work across multiple machines — or want a backup — you can sync memory to your own private GitHub repo. Three commands, two minutes.

### Setup (once)

Create a private repo at github.com/new, then inside Claude Code:

```
Setup Sync: https://github.com/you/my-memory
```

Claude runs `sync.py setup`, initialises git inside `.claude/memory/`, and pushes to your repo. That's it.

Or from terminal:

```bash
python sync.py setup https://github.com/you/my-memory
```

### Day to day

```
Sync Memory      ←  after End Session, pushes memory to your repo
Pull Memory      ←  on a new machine, pulls everything down
Sync Status      ←  check if anything is unpushed
```

Or from terminal: `python sync.py push` / `python sync.py pull`

### On a new machine

```bash
git clone https://github.com/you/your-project
python sync.py pull    ←  pulls memory from your private repo
```

Then open Claude Code and type `Start Session` — fully up to speed.

---

## Why sync is safe

**Your repo, your rules.** Memory goes to a private GitHub repo you create and own. Clankbrain never sees it, never touches it, has no access to it. You can delete the repo at any time.

**Kit code flows one way only.** Updates are pulled from clankbrain to your machine. Nothing ever goes the other direction. `sync.py push` pushes to your repo — not clankbrain's.

**Plain text — fully auditable.** Memory files are markdown. You can read them, diff them, review them in a PR, grep them, and restore any version from git history. Nothing is encoded or opaque.

**What's actually in memory files:**
- Lessons learned from past sessions
- Architectural decisions and why they were made
- Rejected approaches and why
- Function names and what they do
- Project status and what's in progress

No passwords. No customer data. No credentials. If something sensitive accidentally ends up in a memory file, you can see it immediately and delete it — it's just a text file.

**Self-hosted option.** For stricter environments, replace GitHub with GitLab, Bitbucket, or any on-prem git server. The `sync.py` script works with any git remote — just swap the URL.

**Anthropic's role.** Clankbrain memory files are local. Claude Code itself sends your prompts to Anthropic — that's separate from this kit. For regulated industries, use an Anthropic enterprise plan with a signed BAA. Clankbrain adds nothing to that surface.

---

## Every Command

### Daily
| Command | What it does |
|---------|-------------|
| `Start Session` | Reads memory, applies lessons, surfaces open plans, picks up where you left off |
| `End Session` | Runs /learn, updates STATUS.md, scans plans — memory saved locally |
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
| `Kit Health` | Check all kit components are wired and healthy |
| `Context Score` | Score every CLAUDE.md section by journal usage — find dead weight bloating your context |
| `Mine Patterns` | Cluster lessons.md across all sessions — surface recurring mistakes you haven't noticed |
| `Estimate: [task]` | Match task to past velocity history — reports what similar tasks actually took, not what felt right |
| `/check-anthropic` | Fetch Claude Code releases + docs, cross-reference hooks/features in use, report gaps rated High/Medium/Low — run every few weeks |

### Setup and recovery
| Command | What it does |
|---------|-------------|
| `Setup Memory` | First-time setup — creates all memory files for your project |
| `Install Memory` | New machine — copies memory files to Claude's system path |
| `Generate Skills` | Auto-creates skills tailored to your actual stack, file names, and patterns |
| `Update Kit` | Pulls latest kit safely — only the kit commands block in CLAUDE.md is ever touched; your memory, skills, and code are never modified |

### Sync (opt-in)
| Command | What it does |
|---------|-------------|
| `Setup Sync: [repo URL]` | One-time setup — points memory at your private GitHub repo |
| `Sync Memory` | Push memory to your repo after a session |
| `Pull Memory` | Pull memory on a new machine |
| `Sync Status` | Check if anything is unpushed |

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

Eight hooks run automatically — no commands needed, no configuration required. All call `tools/memory.py` with different subcommands.

| Hook | When it fires | What it does |
|------|--------------|-------------|
| `SessionStart` | When a session begins | `memory.py --session-start` — loads MEMORY.md + status into context; surfaces interruption state if last session crashed. |
| `UserPromptSubmit` | Before every prompt | `memory.py --capture-correction` — detects correction language and queues it for `/learn`. |
| `PostToolUse` | After every Edit or Write | `memory.py --check-drift --silent` — catches drift immediately after every file change (runs async, no delay). `memory.py --verify-edit` — requires Claude to quote the changed lines verbatim (not a summary) before proceeding to the next edit. |
| `PreCompact` | Before context compaction | `memory.py --precompact` — surfaces memory checklist before context is compressed. |
| `PostCompact` | After context compaction | `memory.py --postcompact` — re-injects MEMORY.md so session resumes warm, not cold. |
| `Stop` (journal) | After every response | `memory.py --journal` — auto-captures session summary. Searchable forever, no `/learn` needed. |
| `Stop` (reminder) | After every response | `memory.py --stop-check` — reminds you to save memory; surfaces open plans with unresolved questions. |
| `StopFailure` | When session ends via API error | `memory.py --stop-failure` — writes interruption state; surfaced automatically on next session start. |

All hooks call a single script — `tools/memory.py` — cross-platform, no dependencies beyond Python 3.7+.

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
├── CLAUDE.md                        ← Claude's instructions (loads @rules/ on every session)
├── STATUS.md                        ← Full session log — date + what changed
├── update.py                        ← Safe kit updater
├── upgrade.py                       ← Upgrade Lite → Full (adds memory.py + hooks)
├── tools/
│   └── memory.py                    ← All lifecycle hooks in one script
│       ├── --check-drift            ← PostToolUse hook: finds undocumented functions
│       ├── --verify-edit            ← PostToolUse hook: requires verbatim line quote before proceeding
│       ├── --journal                ← Stop hook: auto-captures session journal
│       ├── --stop-check             ← Stop hook: open plan + unsaved change reminders
│       ├── --session-start          ← SessionStart hook: memory + silent kit health check
│       ├── --quick-learn            ← On demand: fast lesson capture, writes stub first
│       ├── --kit-health             ← On demand: checks all kit components are wired
│       ├── --bootstrap              ← Run once: full codebase index on new projects
│       └── --search "query"         ← Search all memory files with scored results
└── .claude/
    ├── settings.json                ← 7 hooks configured
    ├── memory/
    │   ├── MEMORY.md                ← Index — auto-loaded every session
    │   ├── lessons.md               ← Lessons from /learn — applied each session
    │   ├── decisions.md             ← Settled decisions — never re-debated
    │   ├── error-lookup.md          ← Known errors → cause → fix. Never debug the same error twice.
    │   ├── critical-notes.md        ← Non-obvious gotchas that will cost time if unknown
    │   ├── agreed-flow.md           ← User journeys locked by explicit agreement
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
    ├── rules/
    │   ├── plan-before-edit.md      ← Required plan format before any code change
    │   ├── guard-patterns.md        ← Named guards with grep strategies — run with Guard Check
    │   └── update-code-map.md       ← Persistent rule: update memory after every code change
    ├── memory/
    │   └── plans/
    │       └── _template.md         ← Plan template — one file per feature
    └── skills/
        ├── plan/                    ← Structured planning mode
        ├── learn/
        ├── evolve/
        ├── verification-loop/
        ├── strategic-compact/
        ├── search-first/
        └── code-reviewer/          ← reads lessons.md + decisions.md; Generate Skills adds more
```

Commit `.claude/memory/` and `.claude/skills/` to your repo. Memory and skills travel with the code.

---

## Real Results

Tested across **140 real development sessions** on a production codebase — legacy Java backend, 5 JS files, 100+ functions, multi-page frontend with scheduler, email system, and encrypted URL handling. Not a demo project.

- Sessions crashed mid-task — `Start Session` recovered every time, zero re-explanation needed
- Skills patched themselves via `/evolve` — the same skill failure never happened twice
- A compiler bug was discovered, fixed, and logged permanently — it has never cost another debugging session
- 21 undocumented functions caught on the first drift detection run
- `velocity.md` reached 30+ entries — estimates now reflect actual track record instead of guessing

---

## This System Is Only As Good As You Are

Clankbrain is a system, not a plugin. It compounds with use — but only if you use it.

**What the kit does automatically:**
- Drift detection runs after every file edit
- Session journal captures what happened
- Stop hook reminds you when memory has unsaved changes
- PreCompact hook protects memory through context resets

**What requires you:**
- Running `End Session` consistently — skipping it means lessons don't get extracted
- Running `/learn` — the skill scores that power `/evolve` only exist if you log them
- Running `/evolve` every few sessions — skills don't patch themselves without it
- Keeping memory files honest — garbage in, garbage out

**The compound learning loop only compounds if you close it.**

A developer who runs `Start Session` / `End Session` every session and `/evolve` every few weeks will have a Claude that gets measurably better at their specific codebase over time. Someone who uses it sporadically gets marginal gains.

The habit is the product. The kit is just what makes the habit stick.

---

## Roadmap

Five features actively in development — each one closes a gap no other memory tool addresses.

### Regret Guard *(highest value)*
Before every session, auto-scan `regret.md` + `decisions.md` and inject relevant warnings based on what you're about to work on. Not just "here's the full list" — keyword-matched to the current task. If you rejected an approach three sessions ago and are about to propose it again, Claude catches it before the plan is shown.

*Institutional memory that actively changes behavior. Nobody else does this.*

### Context Efficiency Score
Track which parts of `CLAUDE.md` are actually referenced in sessions vs sitting there bloating context silently. After 10+ sessions, surface a report: "These 4 sections were never referenced — remove them or consolidate." Dead context is paid context.

### Velocity-Honest Estimates
When you start a task, pull from `velocity.md` and say: *"Last 3 similar tasks took 2–4 sessions, not 1. Adjust your plan."* Estimates stop being optimistic guesses and start reflecting your actual track record. After 20+ entries, the system has enough signal to be honest.

### Cross-Session Pattern Mining
`/evolve` currently patches individual skills. The next layer: automatically cluster `lessons.md` entries across sessions and surface recurring patterns — *"You make this type of mistake every ~15 sessions"* — and convert them into standing rules automatically. Patterns you don't notice become rules you don't have to remember.

### Decision Guard
Before any plan is shown, auto-check `decisions.md` and warn if the proposed approach contradicts a settled decision. Currently `decisions.md` is passive — you read it if you remember to. Decision Guard makes it active: Claude can't propose the rejected approach without surfacing the reason it was rejected.

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

**What does `--bootstrap` do?**
`python tools/memory.py --bootstrap` scans your entire project and generates `quick_index.md` — a grouped map of every source file by type (Java, JS, CSS, SQL, etc.). Gives Claude immediate codebase awareness without any manual documentation. Run it once on any new project.

**Does this work with Anthropic's native Auto Memory?**
Yes — they solve different problems. Anthropic's Auto Memory captures conversational context within a session. Clankbrain persists project knowledge across sessions: your codebase structure, architectural decisions, lessons from past mistakes, and custom workflows. Auto Memory forgets when the session closes. Clankbrain doesn't. Run both — they complement each other.

**Why markdown files instead of a database?**
Files you can read, diff, commit, and recover without any tooling. Memory stored in a database is opaque — you can't grep it, review it in a PR, or restore a version from last Tuesday. Markdown files travel with your repo, work on any machine with zero setup, and never require an API key or running service. The constraint is the feature.

**Does a big CLAUDE.md actually help?**
No — and the research backs this up. Large monolithic CLAUDE.md files increase token use by ~20% with only a 5% improvement in output quality, and sometimes a negative effect when the content is AI-generated. Clankbrain is built the opposite way: CLAUDE.md stays lean (commands and gotchas only), and project knowledge lives in separate `.claude/memory/` files that load selectively based on what's relevant. That's what the research actually recommends. The CLAUDE.md template that ships with the kit enforces this — the project-specific section is designed to stay under 50 lines.

**Is this safe for business use?**

**What clankbrain does with your data:** Nothing. Memory files stay on your machine. Kit updates are pulled from clankbrain — nothing goes the other direction. No telemetry, no analytics, no servers.

**What Claude Code does with your data:** Sends your prompts to Anthropic. This is separate from clankbrain and true of any Claude Code use. It is the real data consideration for businesses — not this kit. For sensitive workloads, use an Anthropic enterprise plan with a signed BAA.

**GDPR:** Clankbrain itself processes no personal data. Memory files are stored locally and contain code patterns, decisions, and lessons — not personal data. If personal data accidentally ends up in a memory file, you own that file entirely and can delete or edit it. For stricter requirements, keep memory local and off git entirely.

**HIPAA:** Not compliant out of the box. The blocker is Claude Code sending prompts to Anthropic, not clankbrain. Pair with an Anthropic enterprise BAA and keep memory local.

**SOC 2:** Not applicable — clankbrain is a local developer tool, not a service. There are no clankbrain servers to audit.

**Access control (if syncing):** Your private repo controls access. Set it to private and manage collaborators as you would any sensitive codebase. For teams, treat the memory repo like the main repo — same access policies.

**What not to put in memory:** Never put passwords, API keys, customer PII, or regulated data in memory files. Memory is for code patterns, decisions, architecture, and lessons — not data. If something sensitive accidentally lands in a file, delete the entry and purge it from git history with `git filter-repo`.

**For regulated industries:** Keep memory local (skip sync). Use Anthropic enterprise for a BAA. Use self-hosted git if sync is needed. Clankbrain adds nothing to your compliance surface beyond what Claude Code already requires.

**What makes it different from other Claude memory tools?**
Most memory tools are static — you document once and things go stale. Clankbrain is a living system: memory stays accurate via drift detection, skills improve via the compound learning loop, and sessions compound instead of reset. No other tool in this space ships the self-improving skills layer.

**What if I'm on a new computer?**
Pull your project, open Claude Code, type `Install Memory`. Claude is fully up to speed in seconds — all lessons, decisions, and skill improvements carried over.

**Does Update Kit overwrite my customizations?**
Never. It only updates the kit commands block in CLAUDE.md and the tools/ scripts. Your memory files, skills, code, and everything below `## What This Project Is` in CLAUDE.md are never touched.

**Can I customize the skills?**
Yes — every skill is a plain markdown file in `.claude/skills/`. Edit directly, or type `Generate Skills` and Claude creates new ones for your stack. Add `## Auto-Chain` to any skill to connect it into a workflow.

**What's the difference between Full and Lite mode?**
Lite mode is zero-Python: `CLAUDE.md` + `@rules/` files (static conventions) + one notes file. No scripts, no hooks, no Python required. Full mode adds `tools/memory.py` and 8 lifecycle hooks — automated drift detection, session journaling, plan verification, and stop reminders. Upgrade from Lite to Full at any time: `python upgrade.py`.

---

**Requires:** Python 3.7+ · [Claude Code](https://claude.ai/claude-code) · No other dependencies

If Clankbrain saved you from re-explaining your project one more time, **[⭐ star it on GitHub](https://github.com/YehudaFrankel/clankbrain)** — it helps others find it. Using it on a real project? **[Share what you're building →](https://github.com/YehudaFrankel/clankbrain/discussions)**