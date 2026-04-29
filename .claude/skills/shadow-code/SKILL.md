---
name: shadow-code
description: Developer sharpening exercise — user writes the implementation first, Claude reviews and compares. Keeps independent coding ability sharp. Triggers on "/shadow-code", "shadow mode", "I'll write it first", "let me try first".
allowed-tools: Read, Grep, Glob
---

# Skill: shadow-code

**Trigger:** `/shadow-code` or "shadow mode" or "I'll write it first" or "let me try first"

**Description:** You write the implementation. Claude reviews it, compares to what it would have written, and explains any differences — without rewriting unless you ask. Keeps the coding muscle sharp.

---

## Steps

1. **Confirm the task** — restate in one sentence what needs to be implemented. Make sure scope is clear before the user starts.

2. **Step back** — do not write any implementation code. Provide only:
   - The relevant file path and line number to work from
   - Any project-specific conventions that apply
   - What the method/function signature should be

3. **Wait for the user's implementation** — they paste or describe what they wrote.

4. **Review without rewriting** — compare their implementation to what Claude would have written. Report:
   - **Correct:** what they got right
   - **Gaps:** anything missing or wrong, with explanation of WHY (not just what)
   - **Differences:** where Claude would have done it differently, and whether their approach is also valid or strictly worse
   - **Project gotchas:** any platform-specific pattern they may not have applied

5. **Score it honestly:**
   - ✅ Production-ready — would ship as-is
   - 🟡 Mostly right — minor fixes needed (list them)
   - 🔴 Needs rework — fundamental issue (explain clearly, then offer to show the correct version)

6. **Only rewrite if asked** — if the user says "show me yours" or "fix it", then Claude writes the corrected version. Otherwise stop at the review.

---

## Notes

- This skill is about building the muscle, not shipping fast — be thorough in the review
- Never be dismissive of a working approach that differs from Claude's style
- If the user's approach is valid but unconventional, say so explicitly — don't imply it's wrong
- The goal is the gap analysis, not the grade
- Suggested cadence: every 5-10 sessions, or when a feature is small enough to attempt solo
