# Clankbrain

<p align="center"><img src="logo.jpeg" alt="Clankbrain" width="160" /></p>

[![v2.0.0](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/releases) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code) [![Discussions](https://img.shields.io/badge/community-discussions-purple?style=flat-square)](https://github.com/YehudaFrankel/clankbrain/discussions)

![Session demo](demo.gif?v=2)

**Your project knowledge compounds and learns across sessions.**

Claude Code is stateless. Every session starts from zero — no memory of yesterday's decisions, no record of bugs already fixed, no knowledge of what you tried and rejected last week. You re-explain. Claude re-suggests the same things. The same mistake happens twice.

Clankbrain fixes that. It gives Claude Code a living memory that grows with your project — capturing decisions, lessons, and patterns every session, so each session starts smarter than the last.

---

## Is this for you?

- You use **Claude Code** daily on a real, ongoing project
- You've already felt the pain of re-explaining your codebase every session
- You're disciplined enough to run two commands: `Start Session` and `End Session`

If you're just experimenting with Claude Code, come back when it's your primary tool.

---

## What compounding looks like

After 8 sessions, type `Progress Report`:

```
=== Clankbrain Progress Report ===

  Sessions logged         8
  Lessons accumulated     14
  Known errors logged     6    <- never debugged twice
  Rejected approaches     9    <- never re-proposed
  Skill accuracy          78%

  Last 3 sessions:
    [2025-05-12]  Email throttle + scheduler fix      (4 file saves)
    [2025-05-14]  Dashboard accordion redesign         (7 file saves)
    [2025-05-15]  Fixed IDENTITY column error          (2 file saves)

  -> 8 sessions in. Compounding is happening.
```

Session 1 starts blank. By session 8, Claude knows your patterns, your mistakes, and your decisions — and applies them automatically.

---

## Install

```bash
npx clankbrain
```

Setup auto-detects your project name and tech stack. No API keys. No background service. No database. Python 3.7+ required.

**Requires:** [Claude Code](https://claude.ai/claude-code)

---

## Your daily routine

```
Start Session   ->  reads memory, applies past lessons, picks up where you left off
[work]
End Session     ->  extracts lessons, saves everything to memory
```

Two commands. Everything else runs automatically.

---

## What Start Session looks like

One command pulls everything Claude needs from GitHub and picks up exactly where you left off:

```
Start Session

Pulling from GitHub...
Already up to date.
Done - memory, settings and skills ready.

Ready. Last change: Session 42 — Dashboard pagination fix (page state lost
on filter change, debounce added, loading spinner missing on slow queries).

What are we working on?
```

Claude already knows what changed last session, what was deferred, and what patterns to apply — before you type a word.

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

At the end of every session, Claude extracts lessons, updates memory, and pushes everything to GitHub:

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

Updated:
- lessons.md         +18 lines
- tasks/skill_scores.md  +2 lines
- STATUS.md          session 42 summary added
- MEMORY.md          session count updated: 41 -> 42

Pushing to GitHub...

  4 files changed, 23 insertions(+), 1 deletion(-)
  To https://github.com/your-username/your-memory-repo.git

Session complete. Memory pushed to GitHub.
```

Next session, Claude loads these lessons automatically — before you write a single prompt.

---

## What you get

- **Persistent memory** — decisions, bugs fixed, rejected approaches, codebase knowledge
- **Skills that self-improve** — each skill scores itself; `/evolve` patches the ones that keep failing
- **Drift detection** — catches undocumented changes after every file edit
- **Regret guard** — scans past rejected approaches before every prompt, blocks re-proposing them
- **Progress reports** — real numbers built from your actual session history

---

## The habit is the product

Clankbrain compounds with use — but only if you use it. A developer who runs `Start Session` / `End Session` every session and `/evolve` every few weeks will have a Claude that gets measurably better at their specific codebase over time. Someone who uses it sporadically gets marginal gains.

Tested across 140 real sessions on a production codebase. Not a demo project.

---

## Go deeper

- [Skills and the learning loop](docs/skills.md)
- [Lifecycle hooks](docs/hooks.md)
- [Every command](docs/commands.md)
- [Architecture, modes, and file tree](docs/architecture.md)
- [Cross-machine sync and team sync](docs/sync.md)
- [Other IDEs and install options](docs/other-ides.md) — Cursor, Windsurf, Warp, GitHub Copilot
- [FAQ](docs/faq.md)

---

**Built by [Yehuda Frankel](https://github.com/YehudaFrankel).** Using it on a real project? [Tell us what you're building ->](https://github.com/YehudaFrankel/clankbrain/discussions) - If it helped, [star it](https://github.com/YehudaFrankel/clankbrain) — it helps others find the original.
