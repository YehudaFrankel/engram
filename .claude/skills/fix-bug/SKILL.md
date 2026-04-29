---
name: fix-bug
description: Use when the user reports a LOGIC bug — wrong behavior, incorrect output, or a feature not working as designed. Triggers on "fix the bug where", "it's broken", "not sending", "not saving", "wrong result", "something broke".
allowed-tools: Read, Edit, Grep, Glob, Bash
effort: high
keep-coding-instructions: true
---

## Fix Bug

1. **Locate the failure layer** — ask: is it frontend, API/backend, database, scheduler, or email?

2. **Read the relevant file** — don't guess; read it with offset+limit if large

3. **Hypothesize one root cause** — state it before touching anything:
   > "I think the issue is X because Y"

4. **Check common silent failure modes first:**
   - Build artifact not updated after source change (cache, compiled output, stale class)
   - Wrong variable scope (session/context object used in wrong method)
   - Missing auth/ownership check silently filtering the record out
   - INSERT missing required fields → row created but invisible
   - Query missing tenant/org filter → returns wrong user's data
   - Async callback firing before data is ready

5. **Fix only the confirmed root cause** — minimum code change

6. **Verify** — re-test the exact failing case, confirm nothing adjacent broke

7. **Log it** — add one line to `tasks/error-lookup.md`:
   `[date] | error description | root cause | fix applied`

8. Report: "Bug fixed. Root cause was: [X]. Changed: [file:line]. Verified: [how]."

## Auto-Chain
After step 8 — automatically run the following WITHOUT waiting for user to ask:

**Step A — Verification:**
- Run the verification or smoke-test skill on the changed file(s)
- Only stop when verification reports all checks passed

**Step B — Guard (always, after any fix):**
- Run the `guard` skill on the changed file(s)
- Guard will scan for known error patterns AND log the root cause as a new permanent rule
- This ensures the same class of error can never ship again
