---
description: Files that must never be restructured — only minimal targeted edits
---

## Protected Files — Minimal Edits Only

Some files are too complex, order-sensitive, or load-bearing to restructure safely. For these files:
- Read the full file before touching anything
- Change only the minimum lines needed
- Confirm with user before applying

**Common examples of protected file types:**

| Type | Why |
|------|-----|
| Router / dispatcher files (if/else chain, switch-case routing) | Order-sensitive; restructuring breaks all routing |
| Scheduler / state machine logic | Complex state; partial edits cause silent failures |
| Idempotent install/migration scripts | Structure must be preserved to stay idempotent |
| Minified `.js` or `.css` | Edit the source, not the output |
| Shared platform libraries | Downstream consumers depend on exact API |

**Rule:** If a file would break many things if restructured, treat it as protected. Append/insert only — never reorder or refactor the whole thing.
