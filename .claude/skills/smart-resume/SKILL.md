---
name: smart-resume
description: Reads STATUS.md, todo.md, and recent memory to identify what was in progress, then proposes and executes the specific next step. Use when resuming work after a break, or say "smart resume" / "pick up where we left off" / "what were we working on" / "what's next".
allowed-tools: Agent, Read, Grep, Bash
effort: low
keep-coding-instructions: true
---

# Skill: smart-resume

## Description
Reads recent work context — STATUS.md, todo, open plans — to infer what's in progress and propose the single most useful next action. Executes on confirmation.

**Trigger phrases:**
- "smart resume"
- "pick up where we left off"
- "what were we working on"
- "what's next"
- "continue"
- "resume"

---

## Steps

### Step 1 — Read context (parallel reads)

Simultaneously read:
1. **`[MEM]/STATUS.md`** — session number + last change summary
2. **`[MEM]/todo.md`** — open items (High/Medium priority)
3. **`[MEM]/plans/`** — glob for non-archived plan files; read the most recently modified

### Step 2 — Check for in-flight work

If STATUS.md or todo references a specific file being edited, check its current state:
- Grep for `// TODO` or `// IN PROGRESS` markers in the mentioned file (use offset+limit — never read whole large files)

### Step 3 — Infer the single most important next action

Rank candidates by specificity:
1. A plan file with `Status: In Progress` that has an identified next step
2. A High-priority todo item marked `[ ]`
3. The last change summary from STATUS.md — what's the natural follow-on?
4. A Medium-priority todo

### Step 4 — Propose with full context

```
## Smart Resume — Session [N]

**Last session:** [STATUS.md summary]
**Open work:** [specific todo or plan step]

**Proposed next step:**
[Specific action — e.g., "Add the routing line for appXxx in routes.js around line 200"]

**Files involved:** [list]

Go? (yes / skip / show me all open items)
```

### Step 5 — Execute on confirmation

If user says yes / go / do it:
- Follow `plan-before-edit.md` — show plan, wait for approval, then edit
- After edit: update STATUS.md + todo.md

If user says skip:
- Show next candidate from ranked list

If user says "show me all open items":
- Print the full todo.md High+Medium sections + all open plan files

---

## Notes

- Always follow plan-before-edit.md before touching any code
- This skill reads context only in Steps 1-2 — no edits until Step 5 after explicit confirmation
- If no clear next step exists, say so: "No open work found — what should we work on?"
