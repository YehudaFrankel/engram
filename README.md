# Clankbrain

<p align="center"><img src="logo.jpeg" alt="Clankbrain" width="160" /></p>

[![v2.0.0](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/releases) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code) [![Discussions](https://img.shields.io/badge/community-discussions-purple?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/discussions)

**Claude Code forgets everything every session. Clankbrain makes it remember — and get better over time.**

Two commands. Everything else is automatic.

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

---

## What changes after a few sessions

```
Start Session

Pulling from GitHub...
Already up to date.

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
| Setup | Zero dependencies | Python 3.7+ |
| Memory | 1 notes file | 5 typed memory files |
| Drift detection | None | Automated after every edit |
| Session journal | Not included | Auto-captured on every Stop |
| Best for | Quick experiments | Long-running codebases |

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
openCoursePage nulls courseDescEditor, defeating the if (!courseDescEditor)
guard and causing a new Quill instance (+ toolbar) to be appended to the
DOM on every course open.

All Related Functions
- openCoursePage — mobile/js/AdminFunctions.js:1738

Before:
  courseDescEditor  = null;
  sessionEditors    = {};

After:
  sessionEditors    = {};

Why this will work
The detailCourseDescEditor DOM element is static HTML — it persists across
course opens. Keeping the Quill instance alive and just updating
courseDescEditor.root.innerHTML is correct. sessionEditors / fullContentEditors
/ reminderEditors still reset because those are tied to dynamically-rendered
session HTML.

Scope / Blast Radius
- Files touched: mobile/js/AdminFunctions.js
- Lines changed: 1 removed
- Type: Bug fix
- Affected at runtime: Course description editor only — no behavior change,
  just stops toolbar duplication

Proceed?
```

You type `yes`. Claude applies the edit, reads back the changed lines, and confirms:

```
✓ Verified AdminFunctions.js:1736-1743 — courseDescEditor = null removed.
sessionEditors = {} is now the first reset line. All diagnostics pre-existing.

Done. Opening a second or third course will reuse the existing Quill instance
instead of creating new ones — one toolbar only.
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

Found 4 related memories:

  lessons.md [score: 0.91]
  "Admin endpoints return stat=fail when SessionID is missing —
   IGPlugin injects lowercase sessionid but isAdminSession() reads
   uppercase SessionID. Always pass it explicitly."

  error-lookup.md [score: 0.87]
  "stat=fail + 'Request failed' → missing SessionID in appAdmin* call.
   Fix: add SessionID: sessionStorage.getItem('adminSession') to every
   admin call."

  decisions.md [score: 0.74]
  "Settled: always pass SessionID explicitly. IGPlugin auto-injection
   does not satisfy the admin auth check — confirmed session 12."
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
