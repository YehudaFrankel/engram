---
name: End Session
description: Use at the end of every working session. Chains learn → memory update → drift check → status update in the correct order. Prevents lost context and memory drift.
---

# End Session Agent

Closes the session cleanly. Run in order — do not skip steps.

---

## Step 1 — Extract Lessons
Run `/learn` — invoke the `learn` skill.
- Extract patterns, lessons, decisions, and rejected approaches from this session
- Write to `memory/lessons.md`, `memory/decisions.md`, `memory/tasks/regret.md`
- Score any skills used this session in `memory/tasks/skill_scores.md`

**BREAKPOINT:** "Lessons extracted: [N new]. Decisions logged: [N]. Proceed to memory update?"

---

## Step 2 — Update Memory Files
For everything changed this session, update the relevant memory file immediately:

| What changed | Update this |
|---|---|
| JS function added/changed | `memory/js_functions.md` |
| HTML/CSS changed | `memory/html_css_reference.md` |
| Endpoint or backend method | `memory/backend_reference.md` |
| Architecture decision | `memory/decisions.md` |
| Code-map exists | `code-map.md` — line numbers, flows, DB entries |

---

## Step 3 — Drift Check
Run `python tools/memory.py --check-drift`
- Fix any drift found before closing

**BREAKPOINT:** "Drift check: [clean / N issues fixed]. Proceed to status update?"

---

## Step 4 — Update STATUS.md
- Increment session number
- Write one-line summary of what changed this session
- Update `currentDate` in `memory/MEMORY.md` to today's date

---

## Step 5 — Evolve Check
Run `/evolve-check` — scan `memory/tasks/skill_scores.md` and report each skill:
- 🔴 URGENT — multiple unpatched failures
- 🟡 WATCH — 1–2 unpatched failures
- 🟢 STABLE — no failures
- ⚠️ DATA MISSING — fewer than 3 data points

Run `/evolve` only if 🔴 or 🟡 with structured failure data.

---

## Step 6 — Sync (if configured)
If cross-machine or team sync is set up, run `Sync Memory` / `Team Push` now.

---

## Step 7 — Final Report (always show this)

End every session with this exact format:

```
Session complete. [commit hash if applicable]

**Lessons extracted:** N
- [one line per lesson]

**Decisions:** N
- [one line per decision]

**Evolve Check:**
- 🔴 URGENT: [skill] — [reason]   (or "none")
- 🟡 WATCH: [skill] — [reason]    (or "none")
- 🟢 STABLE: [comma-separated list]
- ⚠️ DATA MISSING: [skill] — [reason]   (or "none")
```

Never skip this report.
