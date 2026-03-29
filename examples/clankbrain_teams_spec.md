# Clankbrain Teams — Technical Spec

> Status: Draft — thinking stage, not committed to building yet.

---

## The Core Idea

Separate personal memory from shared memory. Personal stays local. Shared syncs to a team git repo that everyone reads and writes.

---

## Architecture

```
.claude/memory/
  personal/           ← local only, never pushed to team repo
    user_profile.md   ← how I work, my preferences
    user_feedback.md  ← corrections specific to my workflow
  shared/             ← syncs to team repo
    decisions.md      ← architectural choices the whole team respects
    feedback.md       ← patterns the whole team should avoid
    project_status.md ← current state of the project
    regret.md         ← rejected approaches + why
    lessons.md        ← accumulated session learnings
```

Personal/ is never touched by team sync.
Shared/ is the team's collective brain.

---

## Commands

### Setup (team admin — runs once)
```bash
python sync.py setup-team https://github.com/org/team-memory
```
- Creates shared/ directory
- Initializes git in shared/ pointing to team repo
- Migrates existing shared-worthy memory files into shared/
- Leaves personal/ untouched

### Join (new team member — runs once)
```bash
python sync.py join https://github.com/org/team-memory
```
- Clones team repo into shared/
- Preserves any existing personal/ files
- Runs session-start hook to load both personal + shared into context

### Push (after session)
```bash
python sync.py team-push
```
- Pulls latest from team repo first (reduces conflicts)
- Commits and pushes shared/ changes
- Reports what was added

### Pull (start of session)
```bash
python sync.py team-pull
```
- Pulls latest shared memory from team repo
- Reports what changed since last pull

---

## Merge Conflict Strategy

Memory files are append-only by design — new entries are added at the bottom, old entries are never edited. This means:

- `decisions.md` — new decisions appended → rarely conflicts
- `lessons.md` — new lessons appended → rarely conflicts
- `feedback.md` — new patterns appended → rarely conflicts
- `regret.md` — new entries appended → rarely conflicts
- `project_status.md` — the one file that gets edited in place → most likely conflict source

**Resolution:** For project_status.md, the last-write wins. It's a status file, not an audit log. Whoever pushed last is most current.

For all other files — git merge handles it automatically because entries are appended not edited.

---

## Access Model (v1 — simple)

Everyone on the team can read and write shared memory. No roles, no permissions.

**Why start here:** The trust model for shared memory is the same as the trust model for shared code. If you trust someone to commit to the repo, you trust them to update shared memory.

**Future:** Read-only members (contractors, clients), admin-only files (decisions.md locked to leads).

---

## What Goes in Shared vs Personal

| Memory file | Where it lives | Why |
|-------------|---------------|-----|
| `user_profile.md` | personal/ | Your preferences, not the team's |
| `user_feedback.md` | personal/ | Your corrections, not the team's |
| `decisions.md` | shared/ | Team-wide architectural choices |
| `feedback.md` | shared/ | Patterns the whole team should avoid |
| `project_status.md` | shared/ | Current state everyone needs |
| `regret.md` | shared/ | Rejected approaches everyone should know |
| `lessons.md` | shared/ | Accumulated learnings from all sessions |
| `complexity_profile.md` | shared/ | Codebase profile everyone uses |

---

## Hook Changes

`session_start_hook` pulls from both personal/ and shared/:
```python
load_memory("personal/")
load_memory("shared/")   # pulls latest from team repo first
```

`stop_hook` offers to push shared/ changes:
```
Session complete. 3 new entries added to shared memory.
Push to team? (y/n)
```

Or auto-push if `team_auto_push: true` in config.

---

## Onboarding Flow (new team member)

1. Install clankbrain: `npx clankbrain`
2. Join team: `python sync.py join https://github.com/org/team-memory`
3. Open Claude Code → Start Session
4. Claude loads personal memory (empty, new user) + shared memory (full team context)
5. New member immediately benefits from all team decisions, lessons, rejected approaches

**Time to full context for a new hire: ~2 minutes.**

---

## Open Questions

1. **Auto-push or prompt?** Auto-push is smoother but could push garbage if End Session isn't run cleanly. Prompt is safer but adds friction.

2. **Who initializes shared memory?** The first person to run `setup-team` seeds it. Do they migrate their personal memory into shared, or start fresh? Starting fresh is cleaner but wastes existing knowledge.

3. **What's the right granularity?** One shared repo per project, or one per organization? Per-project is more isolated. Per-org means lessons from one project help others.

4. **How do you handle a contractor?** They should read shared memory but maybe not write decisions.md. Read-only mode for specific files?

5. **Pricing model?** Free for open source / public repos. Paid for private team repos? Or charge per seat?

---

## Monetization Path

**Free tier:** Personal use, unlimited. Git sync to your own repo. Everything today.

**Teams tier ($15-25/seat/month):**
- Shared memory repo (hosted, no GitHub setup needed)
- Web dashboard to view/edit team memory
- Audit log (who added what, when)
- Onboarding flow for new members

**Enterprise tier (custom):**
- Private deployment
- SSO / SAML
- Admin controls (who can write decisions.md)
- Compliance exports

---

## Build Order

1. personal/ vs shared/ directory split — no new infra, just reorganization
2. `sync.py join` command — clone team repo into shared/
3. Hook changes to load both directories
4. Auto-pull at session start
5. Prompt to push at session end
6. Web dashboard (separate project, bigger lift)
