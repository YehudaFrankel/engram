# Architecture, Modes, and File Tree

---

## Three tiers

Most memory tools ship only the first.

**Tier 1 — Memory**
Persistent context across sessions. Codebase knowledge, decisions, known bugs, rejected approaches. Syncs to git. Travels with the code. Applied at every `Start Session` before any code is touched.

**Tier 2 — Skills**
Auto-triggered workflows from plain English. Each skill scores itself on every use (`skill_scores.md`). `/evolve` reads the scores and patches failing steps. Skills chain into multi-step workflows via `## Auto-Chain`. See [skills.md](skills.md) for the full learning loop.

**Tier 3 — Autonomous**
Skill chaining, self-healing, drift detection, and session journaling run without prompting. Claude works through multi-step tasks without human checkpoints between steps.

---

## Full vs Lite

Setup asks which mode fits your project.

| | Full | Lite |
|---|---|---|
| Memory files | 5 typed memory files (lessons, decisions, error-lookup, critical-notes, project_status) | 3 typed memory files (notes, lessons, decisions) |
| Static conventions | `@rules/` files (stack.md, conventions.md, decisions.md) | Inline in CLAUDE.md |
| Drift detection | Automated — runs after every edit via `memory.py` | None |
| Session journal | Auto-captured on every Stop | Manual (End Session) |
| Python required | Yes (3.7+) | Yes (3.7+) |
| Best for | Complex, long-running codebases, teams | Any project |
| Upgrade later? | — | Yes — `Upgrade to Full` |

**Not sure?** Start with Lite. `Upgrade to Full` adds everything any time.

### Upgrading from Lite to Full

```
Upgrade to Full
```

Or from terminal: `python upgrade.py`

The upgrade downloads `tools/memory.py`, wires lifecycle hooks into `.claude/settings.json`, and keeps your existing `@rules/` files. Restart Claude Code after running.

---

## File tree

```
your-project/
+-- CLAUDE.md                         <- Claude's instructions (loads @rules/ every session)
+-- STATUS.md                         <- Full session log — date + what changed
+-- update.py                         <- Safe kit updater
+-- upgrade.py                        <- Upgrade Lite to Full
+-- tools/
|   +-- memory.py                     <- All lifecycle behaviors in one script
+-- .claude/
    +-- settings.json                 <- 8 hooks wired
    +-- memory/
    |   +-- MEMORY.md                 <- Index — auto-loaded every session
    |   +-- memory_embeddings.pkl     <- Semantic search index (optional — built by --build-index)
    |   +-- lessons.md                <- Lessons from /learn — applied each session
    |   +-- decisions.md              <- Settled decisions — never re-debated
    |   +-- error-lookup.md           <- Known errors -> cause -> fix
    |   +-- critical-notes.md         <- Non-obvious gotchas that will cost time
    |   +-- agreed-flow.md            <- User journeys locked by agreement
    |   +-- project_status.md         <- What's built, what's in progress
    |   +-- js_functions.md           <- Every JS function with description
    |   +-- html_css_reference.md     <- Every HTML section and CSS class
    |   +-- backend_reference.md      <- Every API endpoint and DB pattern
    |   +-- user_preferences.md       <- How you like Claude to work
    |   +-- tasks/
    |       +-- skill_scores.md       <- Step-level failure log (Step N / produced X / needed Y / Severity) — /evolve-check + /evolve read this
    |       +-- skill_improvements.md <- What /evolve patched and why
    |       +-- regret.md             <- Rejected approaches — never re-proposed
    |       +-- velocity.md           <- Estimated vs actual — self-calibrating
    |       +-- todo.md               <- Current tasks in priority order
    +-- rules/
    |   +-- plan-before-edit.md       <- Required plan format before any code change
    |   +-- guard-patterns.md         <- Named guards with grep strategies
    |   +-- update-code-map.md        <- Update memory after every code change
    |   +-- work-rules.md             <- Behavioral guardrails
    |   +-- token-rules.md            <- Context management rules
    +-- memory/
    |   +-- plans/
    |       +-- _template.md          <- Plan template — one file per feature
    |       +-- archive/              <- Completed plans
    +-- skills/
        +-- plan/
        +-- learn/
        +-- evolve/
        +-- evolve-check/             <- Read-only skill health analysis — no patching
        +-- verification-loop/
        +-- strategic-compact/
        +-- search-first/
        +-- code-reviewer/
```

Commit `.claude/memory/` and `.claude/skills/` to your repo — memory and skills travel with the code.

---

## Update Kit

`Update Kit` pulls the latest version safely. It shows exactly what will change and asks for confirmation before applying anything.

**What it never touches:**
- Your memory files (`.claude/memory/`)
- Your skills (`.claude/skills/`)
- Your code
- Everything below `## What This Project Is` in CLAUDE.md — your project-specific content

**What it updates:**
- The kit commands block in CLAUDE.md
- The `tools/` scripts (bug fixes, new subcommands)
- Kit-level settings in `settings.json`

```bash
Update Kit                                    <-  pull from GitHub
Update Kit from https://github.com/user/repo  <-  pull from a fork or branch
python update.py                              <-  same thing, from terminal
```
