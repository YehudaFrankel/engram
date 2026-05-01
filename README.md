# Clankbrain

<p align="center"><img src="logo.jpeg" alt="Clankbrain" width="160" /></p>

[![v2.11.0](https://img.shields.io/badge/version-2.11.0-blue?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/releases) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code + Codex](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code) [![Discussions](https://img.shields.io/badge/community-discussions-purple?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/discussions)

![Session demo](demo.gif)

Every session, your coding agent wakes up a stranger.

You re-explain the stack. Re-describe what you were building. Re-establish why certain approaches won't work here. Then it fumbles through the same debug flow, the same code review, the same refactor — because it has no structured way to do any of it.

Clankbrain fixes both. It gives Claude Code a **living memory** — decisions, mistakes, patterns, lessons that compound across sessions — and **20+ built-in workflows** for every development task: debugging, code review, refactoring, frontend design, security audits, and more.

Session 1: the agent learns your stack.
Session 10: it knows every mistake you've made, every approach you've rejected, every shortcut that works in your codebase.
Session 20: you stop explaining. You just build.

Two commands. That's the whole interface.

```
Start Session   ->  reads memory, applies past lessons, picks up where you left off
[work]
End Session     ->  extracts lessons, saves everything to memory
```

**New here?** After install, type `tour` for a 5-minute interactive walkthrough. Or open [CHEATSHEET.md](docs/CHEATSHEET.md) — the whole kit fits on one page.

---

## Install

```bash
npx clankbrain
```

Or if you cloned the repo directly:

```bash
python tools/memory.py --init
```

Five questions. Creates your memory directory, hooks config, and starter files. Done in 30 seconds.

If anything goes wrong, the installer tells you exactly what's broken and how to fix it (no Python tracebacks).

No API keys. No background service. No database. Zero pip dependencies — stdlib Python only. **Requires:** [Claude Code](https://claude.ai/claude-code) or Codex + Python 3.7+

> Semantic search (`/recall`) optionally uses `sentence-transformers` for meaning-based matching. Without it, `/recall` falls back to keyword grep — still works, just less fuzzy.

> Used by 600+ developers in its first two weeks. If it helps, [star it ★](https://github.com/YehudaFrankel/clankbrain)

---

## First 10 minutes

Right after install, type these in order:

```
kit-health     → confirms install worked (green checks for memory, skills, hooks)
tour           → 5-minute interactive walkthrough — see the magic by doing it
Start Session  → begin real work
```

The whole kit fits on one page: **[CHEATSHEET.md](docs/CHEATSHEET.md)** — print it, screenshot it, keep it open. 5 commands, that's the whole interface.

Want depth? **[QUICKSTART.md](docs/QUICKSTART.md)** walks through your first 3 sessions in detail.

---

## What it feels like

After `Start Session`, the agent doesn't wait for you to re-explain anything:

```
Start Session

Ready. Last change: Session 42 — Dashboard pagination fix (page state lost
on filter change, debounce added, loading spinner missing on slow queries).

What are we working on?
```

You describe a bug. Claude presents a plan before touching anything:

```
Plan

Problem
submitForm() calls validateUser() before the session token is set,
so the auth check always fails on the first submit after page load.

All Related Functions
- submitForm    — src/js/auth.js:84
- validateUser  — src/js/auth.js:112

Before:
  validateUser(token);
  token = getSessionToken();

After:
  token = getSessionToken();
  validateUser(token);

Why this will work
getSessionToken() reads from localStorage — it must run first or
validateUser receives undefined and rejects every request.

Scope / Blast Radius
- Files touched: src/js/auth.js
- Lines changed: 2 reordered
- Type: Bug fix
- Affected at runtime: login flow only — no other callers

Proceed?
```

You type `yes`. Claude applies the edit, reads back the changed lines, and confirms:

```
✓ Verified auth.js:84-86 — getSessionToken() now runs before validateUser().
Token is defined before the auth check. All other functions unaffected.

Done. First submit after page load will now pass validation correctly.
```

No code changes happen without your approval. Every edit is verified against what was planned.

After `End Session`, lessons are extracted automatically:

```
End Session

/learn

Extracted 3 lessons:

1. Rich-text editor duplicates when the instance variable is nulled before the
   re-init guard — keep the instance alive, update content only

2. Debounce must wrap the filter handler, not the fetch call — wrapping fetch
   leaves rapid keystrokes queued, debounce on the handler cancels them

3. Page state (current page, sort column) must be reset on filter change —
   otherwise stale offset returns an empty result set silently

Memory saved this session:
  lessons.md +18  ("- Debounce must wrap the filter handler, not the fetch call")
  tasks/skill_scores.md +2  ("| code-review | Y |")
  STATUS.md +1  ("Session 42 — Dashboard pagination fix")

Session complete.
```

Next session, Claude loads these lessons automatically — before you write a single prompt.

---

## After 8 sessions

```
=== Clankbrain Progress Report ===

  Sessions logged         8
  Lessons accumulated     14
  Known errors logged     6    <- never debugged twice
  Rejected approaches     9    <- never re-proposed
  Skill accuracy          78%

  -> 8 sessions in. Compounding is happening.
```

From a real project — 160 sessions on a production Java/SQL Server codebase, not a demo.

---

## Is this for you?

- You use **Claude Code + Codex** on a real, ongoing project — not just experimenting
- You've felt the pain of re-explaining your codebase every session
- You're willing to run two commands: `Start Session` and `End Session`

The value compounds with consistency. The more sessions you log, the smarter Claude gets about your specific codebase.

---

## What you get

### Memory layer
- **Skills that self-improve** — each skill scores itself on every use; `/evolve` reads the scores and patches the steps that keep failing. After 50 sessions, every skill has been refined by 50 real feedback loops. Nothing else does this.
- **Regret guard** — every prompt is silently scanned against past rejected approaches before Claude responds. Approaches you discarded stay discarded — permanently, across every future session.
- **Typed memory files** — decisions, errors, lessons, and rejected approaches each live in a dedicated file. Not a single dump file — purpose-built stores that load selectively and stay readable.
- **MemPalace-inspired memory format** — every memory file stores a verbatim `## Source` block alongside its summary (shown to raise recall accuracy from ~84% to ~97%). Files carry temporal frontmatter (`valid_from:`, `valid_until:`) so expired or not-yet-active memories surface automatically. `related:` links connect memories across files (Tunnels); the `--pre-edit` hook follows them one level deep before any code change. Six precise types (`rule`, `correction`, `decision`, `state`, `reference`, `user`) replace a flat note dump.
- **Semantic memory search** — `/recall` finds related memories by meaning, not keywords. Local model (~90MB, no API key, fully offline).
- **Team sync** — share what you learn with your whole team. Manager runs `Setup Team` once, teammates run `Join Team` once, every Start Session pulls the latest silently. Personal memory stays local.
- **Drift detection** — catches undocumented changes after every file edit (Full mode).
- **Progress reports** — real numbers built from your actual session history.

### Workflow layer (20+ built-in skills)

Every development activity has a structured skill — not just memory, but a repeatable way to do the work right:

| Category | Skills |
|---|---|
| **Debug** | `fix-bug` — structured root-cause flow; `guard` — scans for known error patterns |
| **Code quality** | `code-review` — antipattern checklist; `07-refactoring` — safe restructure flow; `03-security` — auth/injection/secrets audit |
| **Frontend** | `frontend-design` — full design system from archetype; `refactoring-ui` — tactical visual fixes; `ux-heuristics` — Nielsen + Krug audit |
| **Verification** | `06-testing` — layer-by-layer checklist; `04-environments` — env config sweep |
| **Session** | `smart-resume` — reads STATUS + todo, proposes exact next step; `shadow-code` — you write first, Claude reviews gap |
| **Meta** | `skill-creator` — build new skills; `product-risk` — validate before building |

Skills compound with memory: `fix-bug` auto-runs `guard`, which extracts the root cause as a new permanent rule. Every bug fixed once becomes impossible to ship twice.

---

## vs. other tools

Claude ships built-in Auto Memory since v2.1.59, and dozens of community tools exist — MCP servers, SQLite stores, single-file notes, cloud services.

Every one of them remembers. None of them learn.

| | Auto Memory | MemPalace | Clankbrain |
|---|---|---|---|
| Remembers context across sessions | ✓ | ✓ | ✓ |
| Verbatim source storage (~97% recall accuracy) | ✗ | ✓ | ✓ |
| Temporal memory validity (auto-surfaces stale memories) | ✗ | ✓ | ✓ |
| Cross-linked memories followed before every edit (Tunnels) | ✗ | ✓ | ✓ |
| Skills that self-improve from feedback | ✗ | ✗ | ✓ |
| Permanently blocks rejected approaches | ✗ | ✗ | ✓ |
| Semantic memory search (offline, no API) | ✗ | ✓ | ✓ |
| Team sync with personal memory kept local | ✗ | ✗ | ✓ |
| Pure markdown — no database or vector store required | ✓ | ✗ | ✓ |
| Works without API keys or cloud | ✓ | ✓ | ✓ |

MemPalace ([github.com/milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace)) achieves 96.6% recall on LongMemEval using ChromaDB + SQLite. Clankbrain borrows its three best ideas — verbatim source blocks, temporal validity, and Tunnels — and implements them in pure markdown with no new dependencies. The things MemPalace doesn't have (skill self-improvement, regret guard, team sync) are Clankbrain's original contributions.

The gap is small at session 5. By session 50 it's measurable.

→ [Does this work with Auto Memory? How does it compare to other kits?](docs/faq.md)

---

## Lite or Full?

Setup asks which mode fits your project.

| | Lite | Full |
|---|---|---|
| Setup | Python 3.7+ | Python 3.7+ |
| Memory | 3 typed memory files | 5 typed memory files |
| Drift detection | None | Automated after every edit |
| Session journal | Manual (End Session) | Auto-captured on every Stop |
| Best for | Any project | Complex, long-running codebases |

Not sure? Start with Lite. `Upgrade to Full` adds everything any time.

→ [Full comparison and upgrade steps](docs/architecture.md#full-vs-lite)

---

## How automation works (Full mode)

Full setup wires Claude Code lifecycle hooks into `.claude/settings.json`. Codex still benefits from the shared memory plus `AGENTS.md`, but Claude Code remains the richer automation environment. They fire automatically — nothing to remember, nothing to run manually.

| Hook | Fires when | What it does |
|------|-----------|-------------|
| `UserPromptSubmit` | Every prompt you send | Queues corrections; regret guard checks past rejected approaches; refreshes session title bar every 60 s (session N \| open plans \| open todos) |
| `PostToolUse` | After every Edit or Write | Drift detection, plan verification, edit logging; suggest-guards scoped to error-lookup.md edits only |
| `Stop` | Claude ends a response | Writes session journal; reminds you to End Session if memory has changed |
| `SessionStart` | Session begins | Loads memory, checks for interruptions, pulls team memory if configured |
| `PermissionRequest` | Claude requests a permission | Pre-flight check before permission is granted or denied |
| `PermissionDenied` | A tool use is denied | Logs the tool name and reason to `tasks/permission_denials.md` for review |
| `FileChanged` | A file changes outside Claude | Alerts when `CLAUDE.md` or memory files are edited externally |

Lite mode has none of these — memory updates only when you run `End Session` manually.

> **`disableSkillShellExecution`** — Claude Code + Codex v2.1.91 setting that prevents skills from running inline shell commands. Add `"disableSkillShellExecution": true` to your `.claude/settings.json` if you want to restrict this.

→ [Full hook reference](docs/hooks.md)

---

## Memory file format

Every memory file uses a common template:

```markdown
---
name: short-id
description: one-line hook for MEMORY.md index
type: rule | correction | decision | state | reference | user
valid_from: YYYY-MM-DD        # optional — memory inactive before this date
valid_until: YYYY-MM-DD       # required for type: state/project — flags when stale
related: [other-memory.md]    # optional — links followed by --pre-edit hook (Tunnels)
---

[Summary — the rule, fact, or decision in plain English]

**Why:** [reason this matters]
**How to apply:** [when to use it]

## Source
> [Verbatim snippet from the conversation where this was established]
— Session N
```

**Why `## Source`?** Storing the raw exchange alongside the summary is the single highest-impact change. MemPalace research shows recall accuracy rises from ~84% to ~97% when the verbatim source is present — the model can reason from the original context rather than a summary of it.

**Types:** `rule` (permanent coding rule), `correction` (one-time fix to prevent recurrence), `decision` (locked architectural choice), `state` (current phase — always set `valid_until`), `reference` (external URL/Jira/Slack pointer), `user` (who the user is and how to work with them).

**Temporal validity:** `valid_until` marks state/project memories with an expiry date. `valid_from` prevents a memory from activating too early. Run `Check Memory Expiry` to surface stale entries.

**Tunnels:** `related:` lists files that share context with this memory. The `--pre-edit` hook follows them one level deep before any code change — so editing `auth.js` automatically surfaces `session_bug_auth.md` *and* the `decisions.md` entry it links to.

Run `Memory Audit` to find files missing `## Source` blocks, missing `valid_until` on state types, or missing frontmatter entirely.

---

## What /recall looks like

Six months in, you hit an auth error. Type `/recall auth error`:

```
/recall auth error

Found 3 related memories:

  lessons.md [score: 0.91]
  "JWT token must be set before validateUser() is called — reading from
   localStorage after the call means the first request always fails."

  error-lookup.md [score: 0.87]
  "401 on first request after login → token not yet in localStorage when
   auth check runs. Fix: await setSessionToken() before any API call."

  decisions.md [score: 0.74]
  "Settled: always initialise token before route guards fire. Confirmed
   session 12 — async init was the root cause, not the guard logic."
```

Root cause, known fix, and settled decision — across three files, by meaning not keyword.

→ [Setup and commands](docs/commands.md#memory)

---

## global-lessons.md

One file, loaded at `Start Session` on every project. Good for things that are true everywhere:

```
- Always check .env before debugging auth issues
- Read the error message before searching Stack Overflow
- Never force-push to main — find the root cause instead
```

Lives at `~/.claude/global-lessons.md`. Clankbrain creates it on first install. Shared project memory still lives in `.claude/memory/`; the kit now writes both `CLAUDE.md` and `AGENTS.md` so Claude and Codex can point at the same memory.

---

## Agents — multi-skill orchestrators

Skills handle one step. Agents chain several into a complete workflow with explicit **BREAKPOINT** markers at every decision point.

| Agent | Steps |
|-------|-------|
| `feature-build` | search-first → plan → implement → code-reviewer → verification-loop → /learn |
| `bug-fix` | reproduce → isolate → fix → verify → log+learn |
| `end-session` | /learn → update memory → drift check → STATUS.md → evolve → sync |

Claude stops at every `BREAKPOINT` and waits for your explicit "continue". Add your own in `.claude/agents/`.

→ [Full agent reference and breakpoint patterns](docs/agents.md)

---

## The habit is the product

Clankbrain compounds with use — but only if you use it. Run `Start Session` / `End Session` every session, `/evolve` every few weeks, and Claude gets measurably better at your specific codebase over time.

Tested across 160 real sessions on a production codebase. Not a demo project.

---

## Blank conversation? (Start Session shows nothing)

Open a fresh conversation and type `Update Kit`. This re-downloads and repairs all hook files automatically. After it completes, type `Start Session`.

---

## Changelog

| Version | What changed |
|---------|-------------|
| v2.11.0 | `rules/regret.md` added — 7 rejected approaches ship with the kit and load on every session (`alwaysApply: true`). `NESTED_ASYNC_CALLBACKS` guard added to `guard-patterns.md`. HTML builder pattern added to `work-rules.md`. Three rules distilled from 225 real sessions on a production codebase. |
| v2.10.0 | Karpathy principles rule added (`rules/karpathy-principles.md`) — 4 behavioral guidelines from Andrej Karpathy's LLM coding insights: think before coding, simplicity first, surgical changes, goal-driven execution. Ships as an always-load rule. |
| v2.9.0 | Workflow layer: 13 generic skills added (fix-bug, guard, code-review, 07-refactoring, 03-security, 04-environments, 06-testing, frontend-design, refactoring-ui, ux-heuristics, shadow-code, skill-creator, smart-resume) + protected-files rule. New positioning: memory foundation + workflow superstructure. README and site updated to reflect expanded scope. |
| v2.8.0 | Onboarding pass: `kit-health` skill (post-install verification), `tour` skill (5-min interactive walkthrough), `CHEATSHEET.md` (one-page reference), `setup.py` preflight checks + actionable error messages |
| v2.7.0 | Build to Learn vs Build to Earn: `rules/build-mode.md` (declare discovery vs delivery at session start), `prototype-hypothesis` skill (4-question gate before any prototype iteration), `parallel-prototypes` skill (run 2-3 variants instead of sequential), velocity tracker split into discovery + delivery units. MemPalace-inspired memory format: `## Source` verbatim blocks (~84%→~97% recall), temporal validity (`valid_from`/`valid_until`), Tunnels (`related:` frontmatter + `--pre-edit` hook follows links), 6 precise memory types |
| v2.6.4 | Fix blank conversation on Mac/Linux (python vs python3) + Windows (missing tools/memory.py); 22 new tests for update.py |
| v2.6.1 | skill_scores.md 9-column schema; `sync.py migrate-scores` auto-migration; starter lessons in session 1 |
| v2.6 | Content-aware memory diff; guided first-run; 69 automated tests; telemetry (opt-out: `CLANKBRAIN_NO_TELEMETRY=1`) |
| v2.5 | CHANGELOG + `sync.py migrate`; starter content in Lite; CI workflow; Python version check |
| v2.4 | Dependency detection; End Session memory diff; `upgrade.py --dry-run` |

→ [Full changelog](CHANGELOG.md)

---

## Product Risk — validate before you build

Most tools help you build faster. This one stops you from building the wrong thing.

`/product-risk` runs the Four Big Risks framework (Value, Usability, Feasibility, Viability) in two modes:

**Evaluate mode** — score an existing product:

```
/product-risk evaluate

Which product? > Clankbrain

Value (Will they buy?)      Green — 600 installs in 2 weeks, active discussions
Usability (Can they use?)   Yellow — requires Git + Python + manual push/pull
Feasibility (Can we build?) Green — already built and shipping
Viability (Should we do?)   Green — MIT license, no infra costs, compounds with use

Biggest risk: Usability — setup friction kills adoption.
Next action: Build the onboarding wizard to cut setup from 30 min to 5 min.
```

**Create mode** — validate an idea, then generate working prototypes:

```
/product-risk create

What problem are you solving? > Community engagement for small organizations
Who has this problem? > Synagogue administrators managing 200 families

[walks through 4 risks — kills bad ideas before a line of code is written]

Risk gate passed. Generating:
  - 4 interactive HTML prototypes (member app, admin dashboard, onboarding, signup)
  - Plan file with full technical spec
  - Decisions logged to memory
  - Project scaffolding ready for next session
```

The kill gate is the key: if 2+ risks are red, it refuses to build prototypes and tells you what to validate first. The skill's job is to prevent building things nobody wants.

---

## Which skill do I use?

| I want to... | Use |
|---|---|
| Start working (new session) | `Start Session` |
| Pick up where I left off | `/smart-resume` |
| Plan a feature or change | `/plan` |
| Find where something lives in code | `/search-first` |
| Fix a logic bug | `/fix-bug` |
| Review code for issues | `code-review` |
| Refactor without changing behavior | `07-refactoring` |
| Audit for security issues | `03-security` |
| Check environment before deploying | `04-environments` |
| Design a UI from scratch | `frontend-design` |
| Polish an existing UI | `refactoring-ui` |
| Audit usability | `ux-heuristics` |
| Verify a feature works end-to-end | `06-testing` |
| Validate a product idea before building | `/product-risk create` |
| Score an existing product's risks | `/product-risk evaluate` |
| Write first, have Claude review gap | `/shadow-code` |
| Create a new reusable skill | `/skill-creator` |
| Check nothing broke after changes | smoke-test (stack-specific) |
| Extract lessons from this session | `/learn` |
| See which skills need improvement | `/evolve-check` |
| Patch a skill based on failure data | `/evolve` |
| Search past decisions and lessons | `/recall [topic]` |
| End the session and save memory | `End Session` |

→ [Detailed first-session guide with what to expect](QUICKSTART.md)

---

## Go deeper

- [Every command](docs/commands.md)
- [Cross-machine sync and team sync](docs/sync.md)
- [Skills and the learning loop](docs/skills.md)
- [The loop in practice — a real case study](docs/loop-proof.md)
- [Agents and breakpoint patterns](docs/agents.md)
- [Rules — always-load vs. path-scoped](docs/rules.md)
- [Extending Clankbrain — skills, agents, rules](docs/extending.md)
- [Architecture, modes, and file tree](docs/architecture.md)
- [Lifecycle hooks](docs/hooks.md)
- [Other IDEs and install options](docs/other-ides.md) — Cursor, Windsurf, Warp, GitHub Copilot
- [FAQ](docs/faq.md)
- [Example memory files](examples/)

---

## Repo layout — do not move these files

The following files at repo root serve [clankbrain.com](https://clankbrain.com) directly via GitHub Pages (main branch root). **Do not move them to subfolders** — doing so breaks the live site:
- `index.html` — site homepage
- `googleb8fe14024404ae1c.html` — Google Search Console verification
- `sitemap.xml`, `robots.txt` — SEO
- `logo.jpeg`, `memory-starter-kit.png`, `demo.gif` — images referenced by site + README

If you want to split the marketing site from the kit cleanly, migrate Pages to a `gh-pages` branch or a separate `clankbrain-site` repo first; then these files can move. Don't "clean them up" without doing that step.

---

**Built by [Yehuda Frankel](https://github.com/YehudaFrankel).** Using it on a real project? [Tell us what you're building →](https://github.com/YehudaFrankel/clankbrain/discussions)

> Anonymous usage stats collected on setup (mode, platform, Python version — no project data). Opt out: `CLANKBRAIN_NO_TELEMETRY=1`



