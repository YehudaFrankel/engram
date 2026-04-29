---
name: skill-creator
description: Create a new reusable skill from scratch. Triggers on "create a skill", "new skill", "make a skill called", "add a skill for", "/skill-creator".
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Skill: skill-creator

**Trigger:** `/skill-creator` or "create a skill" or "make a skill called" or "add a skill for"

**Description:** Builds a new SKILL.md from scratch by gathering requirements, writing the step-by-step instructions, creating the file, and wiring it into the workflow map.

---

## Steps

1. **Gather requirements** — ask the user (if not already clear):
   - What is the skill called? (slug, e.g. `fix-bug`, `new-endpoint`)
   - What phrase(s) should trigger it?
   - What does it do — one sentence?
   - What are the steps? (ask for a rough description; you will formalize them)
   - Which tools does it need? (Read, Write, Edit, Bash, Grep, Glob, Agent, etc.)

2. **Check for duplicates** — glob existing skills for similar names or trigger phrases:
   ```
   Glob pattern="**\SKILL.md" path=".claude\skills"
   ```
   Read any close matches. If a duplicate exists, report it and ask: "Update existing or create new?"

3. **Draft the SKILL.md** using this template:
   ```markdown
   ---
   name: skill-name
   description: One-line description — used for skill discovery. Include trigger phrases.
   allowed-tools: Read, Edit, Write, Glob, Grep
   ---

   # Skill: skill-name

   **Trigger:** `/skill-name` or "trigger phrase A" or "trigger phrase B"

   **Description:** What this skill does in one sentence.

   **Allowed Tools:** Read, Edit, Write, ...

   ---

   ## Steps

   1. **Step one** — what to do first
   2. **Step two** — next action
   3. ...

   ---

   ## Notes

   - Any caveats, edge cases, or project-specific rules
   ```

4. **Show the draft** to the user and ask: "Does this look right, or any changes before I write it?"

5. **Write the file** once approved:
   - Path: `.claude/skills/<skill-name>/SKILL.md`
   - Use the Write tool

6. **Add to CLAUDE.md skill map** if it belongs in a workflow — find the relevant row and insert it.

7. **Report:** "Skill `/<skill-name>` created at `.claude/skills/<skill-name>/SKILL.md`. Trigger: [phrases]. Added to workflow: [yes/no]."

---

## Notes

- Skill slugs must be lowercase kebab-case
- `allowed-tools` in frontmatter controls what the skill can use — be conservative; only list tools the steps actually need
- After creating, push via your memory sync script so the skill is available on all machines
