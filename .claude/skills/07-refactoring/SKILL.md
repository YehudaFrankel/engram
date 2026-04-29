---
name: refactor
description: Use when cleaning up, simplifying, or restructuring existing code without changing behavior. Triggers on "refactor", "clean up", "simplify this", "this is getting messy", "too long", "hard to read", "extract this".
allowed-tools: Read, Edit, Grep, Glob
---

## Refactor

1. **Read the target file fully** — understand what it does before touching anything

2. **Identify the refactor type:**
   - Duplicated logic → extract shared helper
   - Method doing too many things → split by responsibility
   - Deep nesting → early return / guard clause
   - Magic numbers/strings → named constants
   - Long parameter list → group related params into an object/struct

3. **State the plan first:**
   > "I'll refactor X by doing Y. This changes structure but not behavior. Files affected: [list]."

4. **Wait for user confirmation** before changing anything

5. **One change at a time** — not a full rewrite; each step leaves code working

6. **Verify behavior unchanged** — walk through the before/after logic and confirm output is identical

7. **Do NOT while refactoring:**
   - Add new features or change behavior
   - Introduce new dependencies or libraries
   - Rename things in ways that break the public API
   - "Fix" things that weren't asked about
