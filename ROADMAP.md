# Clankbrain Roadmap

Where the kit is headed. Rated against what's needed to move from 8/10 to 10/10 in the public Claude Code kit space (Session 208 assessment).

**Guiding rule:** ship one at a time, watch it in the wild, then decide the next. Do not build these in parallel.

---

## 1. One-Command Install with Auto-Repo Creation — PRIORITY

**Why:** Biggest adoption blocker today is "too much setup." Removes the biggest barrier before anything else ships.

**Scope:**
- `install.py --memory-repo` flag
- GitHub API via PAT (v1) → OAuth App (v2)
- Creates private `claude-memory-$project` repo, initial push of CLAUDE.md + MEMORY.md template
- Store token in OS keychain (macOS Keychain / Windows Credential Manager) — not a JSON file on disk
- Prior art: `plans/clankbrain-cloud.md` in webapps memory (already scoped — revive rather than start fresh)

**Effort:** 1–2 sessions

**Gate:** ship before starting any other roadmap item.

---

## 2. Self-Tuning Evolve

**Why:** Delivers the "compound over time without maintenance" promise. Category separation — nobody else auto-prunes.

**Scope:**
- End Session hook: if `session_count % 10 == 0`, auto-run `/evolve-check`, write `proposed-prunes.md`
- End Session UI: single-prompt batch — *"6 skills haven't fired in 30 sessions. Archive? [y/n]"*
- Building blocks exist (`skill_scores.md`, `/evolve-check`) — just add auto-trigger + UI

**Effort:** 1 session

---

## 3. Multi-IDE Support

**Why:** Market expansion. Don't start until #1 and #2 are tight — scaling an un-tight product is the trap.

**Scope:**
- Split into **Clankbrain Core** (memory files + Markdown rules — universal) and **Clankbrain Claude Code** (skills, agents, hooks — Claude-specific)
- Add `Clankbrain Cursor` adapter: `.cursorrules` + native Cursor memory equivalents
- Copilot/Windsurf: weaker — extension APIs less capable; mostly doc-level value

**Effort:** 4–6 sessions per new IDE

---

## 4. Built-In Cost Dashboard

**Why:** Shareable moment — "you saved $X this month vs. vanilla." Marketing weight.

**Scope:**
- Phase 1 — check if Claude Code exposes per-session token counts to hooks. If yes: `.claude/cost-log.json` written per session; `/cost` skill reads + renders monthly table
- Phase 2 — if API data isn't cleanly accessible: MVP with manual bill entry + session count → cost-per-session trend chart

**Effort:** 2–3 sessions if API data accessible; 1 session if manual-only MVP

---

## 5. Retention Data (Public Stats)

**Why:** Credibility. Requires adoption first — reverse dependency on everything above.

**Scope:**
- Telemetry opt-in already exists (`CLANKBRAIN_NO_TELEMETRY=1`)
- Missing: a receiver + aggregator. Cheapest — Cloudflare Worker + D1, ~$0/mo.
- Public page at `clankbrain.com/stats` showing anonymized retention curve

**Effort:** 1 session infrastructure + ongoing

**Gate:** don't start until ≥50 users. Aggregates from 3 users are noise.

---

## Honest Trap List

- **Building 2+ in parallel** — ship one, watch, decide next. Half-finished features compound debt.
- **Starting #5 before users exist** — retention of 3 users is noise.
- **Starting #3 before kit is tight** — scaling a loose product multiplies the mess.
- **Adding features instead of pruning** — the kit's own `regret.md` rule applies. Each feature must justify its weight. Archive, don't delete, for reversibility.

---

_Reviewed Session 208 (2026-04-19). Re-review when any line item ships or when the assessment changes._
