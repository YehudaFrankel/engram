# Claude Recall — The Living System for Claude Code

[![v2.0.0](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/YehudaFrankel/claude-recall/releases) [![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue?style=flat-square)](https://python.org/downloads) [![MIT License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude-Code-orange?style=flat-square)](https://claude.ai/claude-code)

![Session demo](demo.gif)

**Claude Code forgets everything when you close it. Claude Recall fixes that — permanently.**

Every session, Claude starts fresh. No memory of yesterday's decisions. No record of bugs you already fixed. No knowledge of the approach you tried and rejected. You spend the first 10 minutes re-explaining your project — every single time.

Claude Recall gives Claude a memory that grows with your project. The longer you use it, the smarter it gets.

---

## Before and After

**Without Claude Recall:**
```
Monday:   explain your project → work → close
Tuesday:  explain your project again → work → close
Wednesday: explain your project again → fix a bug you already fixed → close
```

**With Claude Recall:**
```
Monday:   Start Session → work → End Session
Tuesday:  Start Session → Claude remembers everything → work → End Session
Wednesday: Start Session → Claude applies Monday's lessons → even better work → End Session
```

Two words to start. Two words to finish. Claude does the rest.

---

## Quick Start

**You need:** Python 3.7+ and [Claude Code](https://claude.ai/claude-code)

**Step 1 — Get the kit**
```bash
git clone https://github.com/YehudaFrankel/claude-recall.git
```

**Step 2 — Set it up in your project** (takes about 2 minutes)
```bash
cd your-project
python /path/to/claude-recall/setup.py
```
Claude asks a few questions about your project — name, what language you use, which files to watch. Then it builds everything automatically.

**Step 3 — Open Claude Code and type:**
```
Start Session
```

That's it. From now on, every session picks up exactly where the last one left off.

---

## What It Actually Does

### It remembers your project
Every decision you make, every bug you fix, every approach you try — Claude writes it down. Next session, it reads everything back before touching any code. The same mistake never happens twice.

### It watches for changes automatically
After every file you edit, Claude checks whether its memory is still accurate. If you added a new function it doesn't know about — it catches it automatically, no manual update needed.

### Skills fix their own mistakes
When Claude uses a built-in skill (like "fix a bug") and gets it wrong, you correct it. That correction gets logged. Run `/evolve` every few sessions and Claude rewrites the skill so it doesn't make the same mistake again. Skills literally improve over time.

### It runs itself in the background
After 9pm with unsaved changes, Claude automatically saves everything to git — so your memory is never lost even if you forget to say "End Session". Drift detection runs after every file edit. The session journal captures what you worked on, automatically.

### It works on any machine
Memory is stored as plain text files in your project, synced to git. Pull your project on a new computer, run `Install Memory`, and Claude picks up right where you left off.

---

## Your Daily Routine

```
Morning:   type "Start Session"
           → Claude reads all memory, applies lessons from past sessions,
             picks up exactly where you left off

[work on your project]

Evening:   type "End Session"
           → Claude logs what changed, extracts lessons,
             saves everything to memory
```

**That's the entire routine.** Two commands. Everything else is automatic.

---

## What You Can Say

You don't invoke most features — just describe what you need in plain English:

| What you say | What happens |
|-------------|-------------|
| `"fix the bug where..."` | Claude finds the root cause, fixes it, logs it so it never happens again |
| `"review this file"` | Claude checks for problems — dead code, missing error handling, security issues |
| `"is this ready for production"` | Claude runs a checklist — catches hardcoded test values, missing checks |
| `"refactor this"` | Claude makes a plan first, then changes — no surprise rewrites |
| `"Start Session"` | Load memory, pick up where you left off |
| `"End Session"` | Save everything, extract lessons, done |
| `/learn` | Extract patterns and lessons from this session right now |
| `/evolve` | Improve skills based on what went wrong in past sessions |

---

## The Learning Loop

The longer you use Claude Recall, the better it gets. Here's why:

1. **You work** — Claude uses its skills (fix-bug, code-review, etc.)
2. **End Session** — `/learn` runs and scores each skill: did it work? Y or N?
3. **Every few sessions** — run `/evolve`. It reads the scores, finds the skills that needed correction, and rewrites the exact step that failed
4. **Next session** — that skill works better, because it learned from its own mistake

By session 20, Claude knows your patterns. By session 50, it knows your codebase better than any fresh context ever could.

---

## What Gets Created in Your Project

```
your-project/
├── CLAUDE.md                    ← Claude's instructions for your project
├── STATUS.md                    ← Log of every session — date + what changed
├── tools/                       ← Automation (runs silently in the background)
└── .claude/
    ├── memory/
    │   ├── lessons.md           ← Every lesson Claude has learned
    │   ├── decisions.md         ← Every decision made and why
    │   └── tasks/
    │       ├── skill_scores.md  ← Skill report card — what worked, what didn't
    │       └── regret.md        ← Approaches that were tried and rejected
    └── skills/
        ├── fix-bug/             ← How to diagnose and fix bugs in your project
        ├── code-review/         ← How to review code in your project
        └── ...                  ← More skills, tailored to your stack
```

All of this travels with your project. Commit it to git — pull on any machine and Claude is fully up to speed instantly.

---

## Three Things That Make It Different

**1. It's a living system, not a snapshot.**
Other memory tools have you document things once, then they go stale. Claude Recall stays accurate automatically — drift detection catches changes, `/learn` extracts lessons, skills self-improve. It grows with your project.

**2. It works across machines.**
Memory syncs to git. Pull your project on a new computer, type `Install Memory`, and Claude picks up exactly where you left off. No setup, no re-explaining.

**3. Skills get smarter over time.**
Every time a skill needed a correction, that gets logged. `/evolve` reads the log and patches the failing step. The same mistake is architecturally impossible after `/evolve` runs.

---

## Real Results

Tested across **112 real development sessions** on a production codebase — a legacy Java backend with 100+ functions, a multi-page frontend, an email system, and encrypted URL handling. Not a demo project.

- Every session crash recovered in seconds with `Start Session` — zero re-explanation ever needed
- A compiler bug was found, fixed, and logged permanently — it has never cost another debugging session
- Skills patched themselves via `/evolve` — the same skill failure never happened twice
- 21 undocumented functions were caught on the first drift detection run

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) — Anthropic's CLI for coding with Claude
- Python 3.7+ — free at [python.org/downloads](https://python.org/downloads)
- That's it — no databases, no API keys, no cloud services

---

## Common Questions

**Do I need to understand how it works to use it?**
No. Two commands per day is the entire interface. The rest is automatic.

**Does it work with any project?**
Yes — setup asks about your stack and configures itself. Works with any language or framework.

**What if I'm on a new computer?**
Pull your project, open Claude Code, type `Install Memory`. Claude is fully up to speed.

**Does it slow down Claude?**
No. Memory files load in under a second. Drift detection runs silently in the background.

**Can I customize it?**
Yes. Every skill is a plain text file you can edit. Every memory file is readable markdown. Type `Generate Skills` and Claude creates skills tailored specifically to your stack.

---

If Claude Recall saved you from re-explaining your project one more time, **[⭐ star it on GitHub](https://github.com/YehudaFrankel/claude-recall)** — it helps others find it.

**[YehudaFrankel/claude-recall](https://github.com/YehudaFrankel/claude-recall)**
