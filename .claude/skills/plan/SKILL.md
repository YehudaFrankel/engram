---
name: plan
description: Structured planning session for a new feature or change. Creates a dedicated plan file, drafts options with build cost/friction/payoff ratings, tracks the decision live. Triggers on "plan [feature]", "I want to build X", "design X", "plan mode", "thinking about building".
model: claude-opus-4-6
effort: high
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Skill: plan

**Trigger:** `"plan [feature]"` · `"I want to build X"` · `"design X"` · `"plan mode"` · `"thinking about building X"`

---

## Steps

### Step 1 — Open or create the plan file
- Derive a slug from the feature name: lowercase, hyphens (e.g. `your-journey`, `email-throttle`)
- Check if `[MEM]/plans/[slug].md` already exists
  - **Yes** → read it, display the full file, skip to Step 4
  - **No** → copy `[MEM]/plans/_template.md` to `[MEM]/plans/[slug].md`, fill in Feature Name + Created date + Project name
- `[MEM]` = `.claude/memory/` relative to project root

### Step 2 — Understand the problem
Ask or infer from context:
- What problem does this solve?
- Who is it for?
- What does "this worked" look like for the user?

Write answers into the **Problem** section. **Display the full plan.**

### Step 3 — Research before drafting
Before writing a single option:
- Grep the codebase for any existing related functionality
- Read `[MEM]/decisions.md` — any settled decisions that apply?
- Read `[MEM]/tasks/regret.md` — any rejected approaches to avoid re-proposing?

Surface anything relevant inline: *"Found existing X in file Y — Option A could build on this."*

### Step 4 — Draft options
Generate 2–4 distinct options. For each:
- Give it a clear name (e.g. "Passive Timeline", "Full Write Surface", "Email Only")
- Rate on three axes: **Build cost** (Low/Medium/High), **User friction** (None/Low/Medium/High), **Payoff** (Low/Medium/High)
- Write 2–3 lines of notes — what it does, key trade-off
- End with a **Build cost comparison** table

Write to the **Options** section. **Display the full plan.**

### Step 5 — Decision
Ask which option the user wants, or if they want to defer.

| User says | Action |
|-----------|--------|
| Picks an option | Mark decision, update Status → `Ready to Code`, log rationale. Immediately append to `[MEM]/decisions.md`. |
| "Not sure" / "Later" | Leave Decision unchecked, Status stays `Draft`. List open questions explicitly. |
| "Not building this" | Status → `On Hold`. Note why in Alternatives Considered. |

**Display the full plan.**

### Step 6 — Technical spec (only if Ready to Code)
Fill in the **Technical Spec** section:
- SQL changes (ALTER TABLE, CREATE TABLE)
- Files to change — ordered table with file + what changes
- New endpoints / API shape
- Any open questions that must be resolved before the first line of code

**Display the full plan.**

### Step 7 — Open questions sweep
Review everything written. Add any unresolved questions to the **Open Questions** checklist.
State explicitly: *"N open questions before this is ready to code."*

### Step 8 — Update MEMORY.md plans index
Add or update the entry in `[MEM]/MEMORY.md`:
```
- [Plan: feature-name](plans/feature-name.md) — Status: Draft/Ready/On Hold — one-line summary
```

---

## Auto-display rule
After **every step** that writes to the plan file — read it back and display the **full file contents**.
Never show a diff or summary. Always the full plan. This is not optional.

## Closing message
| Status | Message |
|--------|---------|
| Ready to Code | "Plan complete. N open questions resolved. Say 'Start coding [feature]' when ready. When coding is done, move this file to `plans/archive/` to keep plans/ clean." |
| Draft | "Plan saved. N open questions remain — resolve before coding." |
| On Hold | "Plan saved as On Hold. Revisit when ready." |

## Auto-Chain
- Status = `Ready to Code` and user says "start coding" → hand off to `search-first` skill
- Status = `Draft` with 0 open questions → prompt: "All questions resolved — ready to mark Ready to Code?"
