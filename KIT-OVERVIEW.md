# Clankbrain — Kit Overview

Quick reference for what ships, what each file does, and how the pieces connect.

---

## What Ships

| File | Purpose |
|------|---------|
| `setup.py` | First-time setup — asks about your stack, creates all files, configures hooks |
| `upgrade.py` | Upgrades Lite → Full (adds `tools/memory.py` + 3 hooks) |
| `update.py` | Pulls latest kit version safely — never touches your memory or skills |
| `install.py` | Minimal bootstrapper — fetched remotely on very first install |
| `tools/memory.py` | All lifecycle behaviors in one script (Full mode only) |
| `sync.py` | Personal + team memory sync in one tool — `push`/`pull` for personal, `setup-team`/`join`/`team-push`/`team-pull` for teams |
| `CLAUDE.md` | Template — kit commands + project-specific sections |
| `KIT-OVERVIEW.md` | This file |

---

## Two Modes

| | Full | Lite |
|---|---|---|
| Memory files | 5 files (js_functions, html_css, backend, project_status, user_preferences) | 1 notes file |
| Conventions | Inline in CLAUDE.md | `@rules/` files (stack.md, conventions.md, decisions.md) |
| Drift detection | Automated — `memory.py --check-drift` after every edit | None |
| Session journal | Auto-captured on every Stop | Not included |
| Python required | Yes | No |
| Upgrade path | — | `python upgrade.py` or type `Upgrade to Full` in Claude Code |

---

## tools/memory.py Subcommands (Full mode)

| Subcommand | When | What |
|------------|------|------|
| `--check-drift` | PostToolUse hook | Finds undocumented JS functions and CSS classes |
| `--journal` | Stop hook | Auto-captures session summary |
| `--stop-check` | Stop hook | Reminds to save memory; surfaces open plans; warns when context is getting long |
| `--session-start` | Start Session | Memory health check |
| `--bootstrap` | Once on new projects | Scans codebase, generates quick_index.md |
| `--complexity-scan` | First Start Session | Detects stack, scores complexity, recommends skills |
| `--precompact` | Before /compact | Reinjects memory into compacted context |

---

## Skills That Ship

| Skill | Trigger |
|-------|---------|
| `plan` | "plan [feature]", "I want to build X" |
| `learn` | `/learn`, End Session |
| `evolve` | `/evolve` |
| `evolve-check` | "evolve check", "skill health" |
| `verification-loop` | "verify this works", "before I ship" |
| `search-first` | "add new endpoint/feature/function" |
| `strategic-compact` | "should I compact?" |
| `java-reviewer` | "review this java" |
| `powershell-safe` | any .ps1 editing task |

`Generate Skills` creates additional skills tailored to your stack (fix-bug, code-review, security-check, new-endpoint, etc.).

---

## Memory Files (Full mode)

All live in `.claude/memory/`:

| File | What it holds |
|------|--------------|
| `MEMORY.md` | Index — auto-loaded every session |
| `lessons.md` | Patterns extracted by /learn — applied each Start Session |
| `decisions.md` | Settled architectural choices — never re-debated |
| `project_status.md` | What's built, what's in progress |
| `js_functions.md` | Every JS function with description |
| `html_css_reference.md` | Every HTML section and CSS class |
| `backend_reference.md` | Every API endpoint and DB pattern |
| `user_preferences.md` | How you like Claude to work |
| `tasks/skill_scores.md` | Step-level failure log per skill (Step N / produced X / needed Y / Severity) — /evolve-check surfaces patterns, /evolve patches them |
| `tasks/regret.md` | Rejected approaches — never re-proposed |
| `tasks/velocity.md` | Estimated vs actual session count per task |
| `plans/_template.md` | Plan template — one file per feature |

---

## Hooks (settings.json)

Three hooks, all calling `tools/memory.py`:

```json
PostToolUse (Edit/Write) → memory.py --check-drift --silent
Stop                     → memory.py --journal
Stop                     → memory.py --stop-check
```

---

## Daily Flow

```
Start Session     →  memory health check, lessons loaded, open plans surfaced
[work]
/evolve-check     →  see which skills need patching (optional, fast)
End Session       →  /learn, STATUS.md updated, memory synced, plans scanned
/evolve           →  patch flagged skills (run when /evolve-check shows 🔴 or 🟡)
```
