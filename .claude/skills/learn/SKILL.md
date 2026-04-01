# Skill: learn

**Trigger:** `/learn` or "extract patterns" or "learn from this session"

**Description:** Extracts reusable patterns, lessons, and decisions from the current session and saves them to memory files. Run before End Session or before /compact to capture what was learned.

**Allowed Tools:** Read, Edit, Write, Glob, Grep

---

## Steps

1. **Check `tasks/corrections_queue.md`** — if it has entries, read each one. These are prompts where you were corrected mid-session (auto-captured by hook). Convert each into a lesson entry using the format in step 3, then clear the file back to its header only (keep the two comment lines, delete the `## date` entries).

2. **Review the current conversation for:**
   - Bugs fixed and their root causes
   - Patterns that worked well
   - Mistakes made and how they were corrected
   - Architectural decisions made
   - Stack-specific gotchas discovered

3. **Conflict check before saving:**
   For each new lesson or decision, run:
   ```
   python tools/memory.py --search "[key term from lesson]" --top 3
   ```
   Scan the results for contradictions — existing memory that says the opposite. If found:
   - Show both the old and new entry side by side
   - Ask: "This conflicts with an existing memory. Replace it? (yes / keep both / skip)"
   - If replacing: use `/forget` to invalidate the old entry, then save the new one
   - If keeping both: add a note `(supersedes [old filename])` to the new entry

4. **Categorize findings:**
   - Bugs/errors → append to `.claude/memory/lessons.md` (create if missing)
   - Architectural decisions → append to `.claude/memory/decisions.md` (create if missing)
   - Rejected approaches → append to `tasks/regret.md` (format: `| Date | Approach | Why Rejected |`)
   - Repeated patterns (3+ times) → flag as skill candidate

5. **Format each entry as:**
   ```
   ## [YYYY-MM-DD] - [short title]
   **Context:** what you were doing
   **Problem:** what went wrong or what was learned
   **Solution/Pattern:** what works
   **Apply when:** trigger conditions
   ```

6. **Global lessons check:** For each lesson, ask: "Does this apply beyond this project?" If yes, also append to `~/.claude/global-lessons.md`:
   ```
   ## [YYYY-MM-DD] - [title]
   **Source:** [project name]
   **Pattern:** [what works]
   **Apply when:** [trigger]
   ```

7. **Skill scoring:** Log each skill that fired this session to `tasks/skill_scores.md`:
   `| [date] | [skill] | [used for] | Y/N | [what specifically failed — be precise, /evolve uses this to patch the right step] | - |`
   If Y: the "What Failed" column is critical — describe the exact step that was wrong, not just "it didn't work".

8. **Velocity log:** If this session had an estimated task, append to `tasks/velocity.md`:
   `| [date] | [task] | [estimated] | [actual] | [complexity 1-5] | [notes] |`

9. **After writing:**
   - Report: "Extracted N lessons: [list titles]"
   - If any pattern appeared 3+ times: "Suggest creating skill: [name] — run /evolve to cluster"

---

## Notes

- Never delete existing entries — only append
- Keep entries concise — one lesson per entry
- Run before End Session to preserve session knowledge
- Run before `/compact` to avoid losing insights
- If a pattern recurs across sessions, it belongs in a skill not just lessons.md
