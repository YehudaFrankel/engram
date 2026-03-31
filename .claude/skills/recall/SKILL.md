---
name: recall
description: Natural language memory search. Use when the user asks "what did we decide about X", "do we know anything about X", "have we dealt with X before", or "/recall X". Faster than search-memory — single grep pass, no parallel agents.
allowed-tools: Bash, Read, Grep
effort: fast
---

# Skill: recall

**Trigger phrases:**
- `/recall [question or topic]`
- "what did we decide about X"
- "do we know anything about X"
- "have we seen X before"
- "what's in memory about X"
- Any quick single-topic lookup

**Use `search-memory` instead when:** the question could span 3+ memory categories and you want parallel agents with a synthesized answer.

---

## Steps

### Step 1 — Extract the query
Pull the search term(s) from the user's message. If it's a full question ("why did we move files to mobile/?"), extract the key nouns: "mobile files location".

### Step 2 — Run the search
Try semantic search first (finds related memories even with different wording). Falls back to keyword search automatically if the index doesn't exist or sentence-transformers isn't installed.

```
python tools/memory.py --search-semantic "[query]" --top 8
```

Run this via Bash. If semantic search returns no matches, also run keyword search:
```
python tools/memory.py --search "[query]" --top 8
```

### Step 3 — Present results

If results found:
```
## Recall: "[query]"

**[file name]** (score N)
> [matching lines]

**[file name]** (score N)
> [matching lines]

---
Bottom line: [1 sentence summary of what memory says]
```

If nothing found:
```
No memory found for "[query]".

This topic hasn't been captured yet. If it comes up this session, run /learn at the end to save it.
```

### Step 4 — Offer to dive deeper
If a result looks relevant but partial:
> "Found in `lessons.md` — want me to read the full entry?"

---

## Notes
- Never write or modify memory files in this skill — read only
- If `memory.py` is not found, fall back to: `Grep(pattern="[query]", path="[MEM]")` recursively
- This skill is intentionally fast — no agents, no synthesis overhead
- For broader research across multiple categories, use `search-memory`
