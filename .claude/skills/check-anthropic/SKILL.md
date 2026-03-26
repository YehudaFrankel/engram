# Skill: check-anthropic

**Trigger:** `/check-anthropic` or "check for new Anthropic features" or "what's new in Claude Code"

**Description:** Fetches the Claude Code GitHub releases page and official docs to find new hooks, CLAUDE.md features, and skills API changes. Cross-references against what this project currently uses and rates each gap for relevance. Run every few weeks or after a major Claude Code release.

**Allowed Tools:** WebFetch, Read, Glob

---

## Steps

### 1. Fetch what's new

Fetch these three pages in parallel:

- `https://github.com/anthropics/claude-code/releases` — recent releases, changelogs
- `https://code.claude.com/docs/en/hooks` — full current hook event list
- `https://code.claude.com/docs/en/memory` — CLAUDE.md + @imports + rules/ features

Read each page and extract:
- Any new hook event names not previously known
- Any new CLAUDE.md syntax or frontmatter fields
- Any new skills API capabilities
- Any new settings.json options

### 2. Read what this project currently uses

- Read `.claude/settings.json` (project-level hooks)
- Read `~/.claude/settings.json` (global hooks, if exists)
- Glob `.claude/skills/*/SKILL.md` — list all skills, count them
- Read `CLAUDE.md` — note any @imports and rules/ files in use

Extract: all hook event names currently wired.

### 3. Cross-reference against known full hook list

The full official hook list as of last verification (24 events):
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `Notification`, `SubagentStart`, `SubagentStop`, `Stop`, `StopFailure`, `TeammateIdle`, `TaskCompleted`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`, `SessionEnd`

Compare: hooks in use vs full list → identify unused hooks.
Also check: any hooks on the fetched docs page that are NOT in the list above → those are new.

### 4. Rate each gap

For every unused hook (and any new features found), rate relevance:

| Rating | Meaning |
|---|---|
| **High** | Directly serves memory, learning, or automation goals — should evaluate now |
| **Medium** | Could help in specific scenarios — worth knowing about |
| **Low** | Niche use case unlikely to apply here |

Guidance for rating hooks:
- `PostCompact` — **High**: re-inject memory context after compaction fires
- `SessionEnd` — **High**: complement to Stop, fires on clean exit
- `FileChanged` — **Medium**: more granular drift detection than PostToolUse Edit|Write
- `StopFailure` — **Medium**: capture state when Claude errors out
- `SubagentStop` — **Low** unless this project uses subagents
- `TaskCompleted` — **Medium**: hook into task completion for auto-logging
- `TeammateIdle` — **Low**: multi-user setups only
- `ConfigChange` — **Low**: fires when settings change

### 5. Report

Output in this format:

```
## Claude Code Feature Check — [date]

### Releases scanned
[list any releases found with key changes]

### Hook coverage
Currently using: N / 24 hooks
[list hooks in use]

### High-priority gaps
[hook name] — [one line: what it does + why it's relevant here]

### Medium gaps
[hook name] — [one line]

### New features found (not in baseline)
[anything on the docs page not in the known list above]

### CLAUDE.md / Skills API
[any new syntax, frontmatter fields, or skills features found]

### Recommendation
[1-2 sentences: what to investigate next]
```

---

## Notes

- Run every 4-6 weeks, or after any Claude Code release announcement
- Pairs well with `/evolve` — run check-anthropic first, then evolve to implement anything rated High
- If a new hook is rated High, create a plan with `Plan [hook name integration]` before implementing
- Update the known hook list in Step 3 if new official hooks are found
