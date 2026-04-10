# The Clankbrain Kit — Plain English Guide

---

## What is this kit?

It's a memory and automation system for Claude Code. Without it, Claude starts fresh every session — no memory of your codebase, your preferences, your past decisions, or your mistakes. With the kit, Claude remembers everything and gets better over time automatically.

Think of it like hiring a contractor vs a full-time employee. A contractor needs to be briefed every visit. A full-time employee builds up context, learns your preferences, and stops making the same mistakes. The kit turns Claude from a contractor into something closer to a full-time employee.

---

## The 7 pieces of the kit

---

### 1. Memory Files

**What they are:** Plain text files that Claude reads at the start of every session.

**Four types:**

| Type | What it stores | Example |
|------|----------------|---------|
| `user` | Who you are, your role, your expertise | "Senior Java dev, new to React" |
| `feedback` | How you want Claude to behave | "Never summarize at the end of a response" |
| `project` | What's happening right now | "Freeze on merges after Thursday, mobile release" |
| `reference` | Where to find things | "Bugs tracked in Linear project INGEST" |

**How it works:** There's an index file called `MEMORY.md` that lists all memory files with one-line descriptions. Claude reads the index first, then decides which files to open. It doesn't read everything — just what's relevant to the current task.

**Why it matters:** Without this, you repeat yourself every session. With it, Claude already knows your team's rules, your codebase quirks, and your preferences before you type a word.

---

### 2. Hooks

**What they are:** Automatic scripts that run when certain things happen — before Claude edits a file, at the start of a session, when Claude stops, etc.

**Think of hooks like:** A checklist that runs itself. You don't have to remember to do it — the system does it automatically.

**The hooks in this kit:**

| Hook | When it fires | What it does |
|------|---------------|--------------|
| `SessionStart` | When you open Claude | Pulls latest memory from GitHub, loads context, shows status |
| `PreToolUse` (Edit) | Before Claude edits any file | Finds relevant memory for that file, injects it |
| `PostToolUse` (Edit) | After Claude edits a file | Updates indexes, logs what changed, rebuilds docs |
| `PostToolUse` (Read) | After Claude reads a file | Logs if it was a memory file (tracks self-consultation) |
| `Stop` | When Claude finishes a session | Pushes memory to GitHub so next session picks it up |
| `StopFailure` | If Claude crashes mid-session | Saves what was happening so you don't lose context |
| `PreCompact` / `PostCompact` | Around context compression | Preserves memory through the compression |

**Why it matters:** All the good behavior happens automatically. Claude doesn't have to remember to save its memory — the Stop hook does it. Claude doesn't have to know your codebase context — the PreToolUse hook injects it right before each edit.

---

### 3. Skills

**What they are:** Custom slash commands that trigger specific workflows.

**Think of them like:** Macros. Instead of explaining a 10-step process every time, you type `/learn` and it runs.

**The key skills in this kit:**

| Skill | What it does |
|-------|-------------|
| `/learn` | Extracts lessons from the current session into permanent memory |
| `/evolve` | Rewrites weak skills based on their failure history |
| `/evolve-check` | Reports which skills are working and which need fixing |
| `/guard` | Checks code for known dangerous patterns before you commit |
| `/search-first` | Forces a codebase search before writing any new code |
| `/plan` | Creates a structured implementation plan |
| `/smoke-test` | Runs end-to-end tests on what you just built |
| `/act` | Reads open plans and proposes the single best next action |

**Why it matters:** Skills turn Claude's best behaviors into one-word commands. The system improves itself — `/evolve` rewrites skills that keep failing, automatically.

---

### 4. Agents

**What they are:** Multi-step orchestration flows that run an entire workflow from start to finish, with human checkpoints.

**Think of them like:** A project manager who knows exactly what order to do things in and stops to check with you at the right moments.

**The agents in this kit:**

| Agent | What it does |
|-------|-------------|
| `feature-build` | search → plan → implement → review → test → learn. Won't start coding until you've approved the plan. |
| `bug-fix` | reproduce → isolate → fix → verify → log. Won't apply the fix until you've confirmed it reproduces. |
| `end-session` | learn → update memory → check guards → push to GitHub. |

**Why it matters:** Without agents, you have to orchestrate the sequence yourself and remember all the steps. With agents, the entire workflow runs in the right order.

---

### 5. Plans

**What they are:** Structured documents that describe what you're about to build, stored in a `plans/` folder.

**Think of them like:** A contract between you and Claude. Before any code gets written, Claude writes out exactly what it's going to do, which files it'll touch, and what the rollback is if it goes wrong. You approve it, then it executes.

**The plan format:**
- **Problem/Feature** — one sentence
- **All related functions** — with exact file and line numbers, verified against the codebase
- **Before code / After code** — exactly what changes
- **Why this will work** — the mechanism, not just "this fixes it"
- **Scope and blast radius** — what breaks if this goes wrong
- **Rollback steps** — exactly how to undo it

**Why it matters:** This is what prevents Claude from quietly making the wrong change. The plan forces it to verify its assumptions before touching code.

---

### 6. Guard Patterns

**What they are:** A file of named checks that Claude runs against code to catch known dangerous patterns.

**Think of them like:** Lint rules — but for business logic and architectural mistakes, not just syntax.

**How a guard works:**
1. Something goes wrong in a session
2. The mistake gets documented in the guard file with a name and a grep strategy
3. On every future edit, Claude checks new code against the guard list
4. If a match is found, it stops and flags it before the mistake happens again

**Why it matters:** Guards catch the same mistake from happening twice. Once a mistake is documented, Claude checks for it automatically on every future edit. The guard list grows over time and the system gets safer.

---

### 7. The Python Tools

**What they are:** Two Python scripts that run behind the scenes, called automatically by the hooks.

**`tools/memory.py`** — The single kit tool. All lifecycle behaviors in one script:

| Feature | What it does |
|---------|-------------|
| Drift detection | Checks if your documentation matches your actual code — catches stale line numbers, missing functions |
| Session journal | Auto-captures a summary at the end of every session |
| Stop check | Reminds you to save memory; surfaces open plans; warns when context is getting long |
| Session start | Memory health check at the beginning of each session |
| Bootstrap | Scans codebase, generates quick_index.md for new projects |
| Complexity scan | Detects stack, scores complexity, recommends skills |
| Pre-compact | Reinjects memory into context before /compact |

**Why it matters:** These run automatically through hooks. You never call them directly — they fire and keep everything in sync without any manual steps.

---

## How it all connects

```
Session opens
  → SessionStart hook fires
  → Pulls memory from GitHub
  → Loads MEMORY.md + STATUS.md into context
  → Claude knows what happened last session

You ask Claude to edit a file
  → PreToolUse hook fires
  → Finds relevant memory for that specific file
  → Claude sees lessons, decisions, guard patterns for that exact context
  → Claude writes a plan and waits for approval

You approve the plan
  → Claude edits the file
  → PostToolUse hook fires
  → Indexes rebuild automatically
  → Draft lessons get logged
  → Regret match runs against the change

Session ends
  → Stop hook fires
  → /learn extracts patterns into permanent memory
  → Memory pushed to GitHub
  → Next session starts with everything intact
```

---

## What makes this different from just using Claude normally

| Without the kit | With the kit |
|-----------------|--------------|
| Claude starts fresh every session | Claude has full project history |
| You repeat the same instructions every time | Rules are in memory, auto-loaded |
| Claude makes the same mistakes twice | Guard patterns catch repeated mistakes |
| No record of past decisions | `decisions.md` and `regret.md` capture everything |
| You have to remember to save | Stop hook pushes to GitHub automatically |
| Skill quality is random | `/evolve` rewrites weak skills automatically |
| Plans happen in Claude's head | Plans are written, approved, then executed |
| Context is lost if Claude crashes | StopFailure hook saves the state |

---

## The compound effect

The first session with the kit feels about the same as without it. By week 4, Claude stops making mistakes specific to your project. By month 3, you've stopped explaining the same things twice entirely. By month 6, the memory system has absorbed enough of your project's patterns that Claude's output fits your codebase on the first try most of the time.

The kit doesn't make Claude smarter. It makes your project's knowledge persistent — so every session builds on the last instead of starting over.
