# Clankbrain

<p align="center"><img src="logo.jpeg" alt="Clankbrain" width="160" /></p>

[![v2.6.0](https://img.shields.io/badge/version-2.6.0-blue?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/releases) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code) [![Discussions](https://img.shields.io/badge/community-discussions-purple?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/discussions)

![Session demo](demo.gif)

Every session, Claude wakes up a stranger.

You re-explain the stack. Re-describe what you were building. Re-establish why certain approaches won't work here. Every day, for a tool that spent yesterday learning all of it.

Clankbrain ends that. It gives Claude a memory that compounds — decisions, mistakes, patterns, lessons — loaded automatically at the start of every session, updated automatically at the end.

Session 1: Claude learns your stack.
Session 10: it knows every mistake you've made, every approach you've rejected, every shortcut that works in your codebase.
Session 20: you stop explaining. You just build.

Two commands. That's the whole interface.

```
Start Session   ->  reads memory, applies past lessons, picks up where you left off
[work]
End Session     ->  extracts lessons, saves everything to memory
```

---

## Install

```bash
npx clankbrain
```

No API keys. No background service. No database. **Requires:** [Claude Code](https://claude.ai/claude-code)

> Anonymous usage stats are collected on setup and session start (mode, platform, Python version — no project data). Opt out: `CLANKBRAIN_NO_TELEMETRY=1`.

---

## What changes after a few sessions

```
Start Session

Ready. Last change: Session 42 — Dashboard pagination fix (page state lost
on filter change, debounce added, loading spinner missing on slow queries).

What are we working on?
```

Claude already knows what changed last session, what was deferred, and what patterns to apply — before you type a word.

After 8 sessions:

```
=== Clankbrain Progress Report ===

  Sessions logged         8
  Lessons accumulated     14
  Known errors logged     6    <- never debugged twice
  Rejected approaches     9    <- never re-proposed
  Skill accuracy          78%

  -> 8 sessions in. Compounding is happening.
```

---

## Is this for you?

- You use **Claude Code** daily on a real, ongoing project
- You've felt the pain of re-explaining your codebase every session
- You're disciplined enough to run two commands: `Start Session` and `End Session`

If you're just experimenting with Claude Code, come back when it's your primary tool.

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

Full setup wires 4 Claude Code lifecycle hooks into `.claude/settings.json`. They fire automatically — nothing to remember, nothing to run manually.

| Hook | Fires when | What it does |
|------|-----------|-------------|
| `UserPromptSubmit` | Every prompt you send | Queues corrections; regret guard checks past rejected approaches |
| `PostToolUse` | After every Edit or Write | Drift detection — flags undocumented JS/CSS changes |
| `Stop` | Claude ends a response | Writes session journal; reminds you to End Session if memory has changed |
| `SessionStart` | Session begins | Loads memory, checks for interruptions, pulls team memory if configured |

Lite mode has none of these — memory updates only when you run `End Session` manually.

→ [Full hook reference](docs/hooks.md)

---

## What a session looks like

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

---

## What End Session looks like

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

No skills needed correction this session. Now updating STATUS.md and
MEMORY.md, then pushing.

Memory saved this session:
  lessons.md +18  ("- Debounce must wrap the filter handler, not the fetch call")
  tasks/skill_scores.md +2  ("| code-review | Y |")
  STATUS.md +1  ("Session 42 — Dashboard pagination fix")

Pushing to GitHub...

  4 files changed, 23 insertions(+), 1 deletion(-)
  To https://github.com/your-username/your-memory-repo.git

Session complete. Memory pushed to GitHub.
```

Next session, Claude loads these lessons automatically — before you write a single prompt.

---

## What you get

- **Persistent memory** — decisions, bugs fixed, rejected approaches, codebase knowledge
- **Semantic memory search** — `/recall` finds related memories by meaning, not just keywords. Local model (~90MB, no API key, fully offline)
- **Skills that self-improve** — each skill scores itself; `/evolve` patches the ones that keep failing
- **Drift detection** — catches undocumented changes after every file edit
- **Regret guard** — scans past rejected approaches before every prompt, blocks re-proposing them
- **Progress reports** — real numbers built from your actual session history
- **Team sync** — share what you learn with your whole team. Manager runs `Setup Team` once, teammates run `Join Team` once, every Start Session pulls the latest silently. Personal memory stays local.

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

Lives at `~/.claude/global-lessons.md`. Clankbrain creates it on first install.

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

## Changelog

| Version | What changed |
|---------|-------------|
| v2.6 | Content-aware memory diff shows last line saved; guided first-run box; 69 automated tests |
| v2.5 | CHANGELOG + `sync.py migrate`; starter content in Lite typed files; CI workflow; Python version check |
| v2.4 | Dependency detection with platform hints; End Session memory diff; `upgrade.py --dry-run` |
| v2.3 | 3 typed files in Lite mode; `sync diagnose`; memory.py refactored into single-purpose helpers |
| v2.2 | Team sync merged into sync.py — one tool, one config; `join` command; health checks; 16 automated tests |
| v2.1 | Markdown agents with BREAKPOINT markers; path-scoped rule frontmatter; CLAUDE.md trimmed to <150 lines with Skill Map |
| v2.0 | Semantic memory search (`/recall`); compound learning (velocity tracker, skill scores); guard patterns; complexity scanner |
| v1.0 | Initial release — persistent memory, skills, lifecycle hooks, cross-machine sync |

---

## Go deeper

- [Every command](docs/commands.md)
- [Cross-machine sync and team sync](docs/sync.md)
- [Skills and the learning loop](docs/skills.md)
- [Agents and breakpoint patterns](docs/agents.md)
- [Rules — always-load vs. path-scoped](docs/rules.md)
- [Extending Clankbrain — skills, agents, rules](docs/extending.md)
- [Architecture, modes, and file tree](docs/architecture.md)
- [Lifecycle hooks](docs/hooks.md)
- [Other IDEs and install options](docs/other-ides.md) — Cursor, Windsurf, Warp, GitHub Copilot
- [FAQ](docs/faq.md)
- [Example memory files](examples/)

---

**Built by [Yehuda Frankel](https://github.com/YehudaFrankel).** Using it on a real project? [Tell us what you're building →](https://github.com/YehudaFrankel/clankbrain/discussions) — If it helped, [star it](https://github.com/YehudaFrankel/clankbrain).
