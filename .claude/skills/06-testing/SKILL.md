---
name: run-verification
description: Use when verifying a feature works, after making changes, or before shipping. Triggers on "verify this works", "test this", "does this work", "run the checklist", "before I ship", "check this end to end".
allowed-tools: Read, Grep, Glob, Bash
---

## Verification

1. **Identify what changed** — ask the user what was just modified (which layer: frontend, API, data, email, scheduler, etc.)

2. **Check for common pre-test blockers:**
   - Any build/compile step needed after the change?
   - Any server restart or cache clear required?
   - Any DB migration that needs to run first?

3. **Walk through the relevant layer checklist** — report each item: PASS / FAIL / UNTESTED
   - Frontend change: Does it render correctly? Are all states handled (loading, error, empty)?
   - API change: Does the endpoint return the correct shape? Auth still working?
   - Data change: Does the migration run cleanly? Does existing data still query correctly?
   - Email/async: Did the job fire? Did output reach the destination?

4. **For any FAIL** — state the exact symptom and most likely cause

5. **Report:** "Verification: [N] pass, [N] fail, [N] untested. Ready to ship: [yes/no]."
