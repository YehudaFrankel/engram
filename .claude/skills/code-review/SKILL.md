---
name: code-review
description: Use when the user wants to review a file for bugs, antipatterns, or quality issues. Triggers on "review", "check for issues", "look for problems", "audit", "before I ship".
allowed-tools: Read, Grep, Glob
---

## Code Review

1. **Read the target file** fully before reporting anything

2. **Check for general antipatterns:**

   **Backend / API:**
   - [ ] Auth check missing on protected endpoints
   - [ ] User input concatenated directly into SQL (injection risk)
   - [ ] Missing error handling on DB calls or external requests
   - [ ] Secrets or credentials hardcoded in source
   - [ ] N+1 query patterns (query inside a loop)
   - [ ] Missing tenant/org filter on multi-tenant queries

   **JavaScript / Frontend:**
   - [ ] `console.log` left in
   - [ ] Missing error handling on async calls
   - [ ] Direct DOM manipulation before checking element exists
   - [ ] Hardcoded IDs or environment-specific values
   - [ ] Inline styles that should be CSS classes
   - [ ] Missing mobile breakpoints

   **General:**
   - [ ] Functions doing more than one thing
   - [ ] Magic numbers/strings without named constants
   - [ ] Dead code or commented-out blocks left in
   - [ ] Missing input validation at system boundaries

3. **Report findings** in a table:
   | File | Line | Issue | Severity |
   |------|------|-------|----------|

4. Ask: "Fix any of these now, or just flag for later?"

5. **Do not change anything** until the user confirms.
