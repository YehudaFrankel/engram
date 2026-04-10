# Lifecycle Hooks

Eleven hooks run automatically — no commands needed, no configuration required after setup. All call a single script: `tools/memory.py`.

---

## Hook table

| Hook | When it fires | What it does |
|------|--------------|-------------|
| `SessionStart` | When a session begins | Loads MEMORY.md + status into context; surfaces interruption state if last session crashed |
| `UserPromptSubmit` | Before every prompt | Detects correction language and queues it for `/learn`; scans `regret.md` for keyword matches; checks `decisions.md` for planning conflicts; refreshes session title bar (session N \| open plans \| open todos) every 60 s via `refreshInterval` |
| `PreToolUse` | Before every Edit or Write | Searches individual memory files + follows `related:` links one level deep (Tunnels); respects `valid_until`/`valid_from` — expired or inactive memories are excluded |
| `PostToolUse` | After every Edit or Write | Runs drift check immediately after every file change; requires Claude to quote changed lines verbatim before proceeding to the next edit |
| `PreCompact` | Before context compaction | Surfaces memory checklist before context is compressed |
| `PostCompact` | After context compaction | Re-injects MEMORY.md so the session resumes warm, not cold |
| `Stop` (journal) | After every response | Auto-captures session summary — searchable forever, no `/learn` needed |
| `Stop` (reminder) | After every response | Reminds you to save memory; surfaces open plans with unresolved questions |
| `StopFailure` | When session ends via error | Writes interruption state; surfaced automatically on next session start |
| `PermissionRequest` | When Claude requests a permission | Pre-flight check before permission is granted or denied |
| `PermissionDenied` | When a tool use is actually denied | Logs the tool name and reason to `tasks/permission_denials.md` — review at End Session |
| `FileChanged` | When a file changes outside Claude | Alerts when `CLAUDE.md` or memory files are edited externally — catches external drift |

---

## memory.py subcommands

All hooks call `tools/memory.py` with a subcommand. You can also call these manually.

### Automatic (called by hooks)

| Subcommand | Hook | What it does |
|------------|------|-------------|
| `--session-start` | SessionStart | Injects memory into context; runs silent kit health check — flags broken wiring before you start |
| `--capture-correction` | UserPromptSubmit | Detects correction language, queues it for `/learn` |
| `--regret-guard` | UserPromptSubmit | Scans `regret.md` + `decisions.md` for entries matching the current task |
| `--decision-guard` | UserPromptSubmit | Detects planning language, warns if it contradicts a settled decision |
| `--error-lookup` | UserPromptSubmit | Matches debug-flavored prompts against `error-lookup.md` — injects known fix before you investigate |
| `--pre-edit` | PreToolUse | Searches memory for entries matching the filename being edited; fires before the change so Claude sees relevant warnings first |
| `--check-drift` | PostToolUse | Catches undocumented JS functions and CSS changes immediately after every file edit |
| `--verify-edit` | PostToolUse | Requires Claude to quote the changed lines verbatim — not a summary, the actual content |
| `--precompact` | PreCompact | Surfaces memory checklist before compaction |
| `--postcompact` | PostCompact | Re-injects MEMORY.md after compaction |
| `--journal` | Stop | Auto-captures what you worked on — timestamped, searchable |
| `--stop-check` | Stop | Reminds you to save memory; surfaces open plans |
| `--stop-failure` | StopFailure | Writes interruption state for recovery on next Start Session |
| `--permission-denied` | PermissionDenied | Logs the denied tool name + reason; appends to `tasks/permission_denials.md` |
| `--session-title` | UserPromptSubmit | Reads STATUS.md + open plans/todos; returns `hookSpecificOutput.sessionTitle` to set the Claude Code title bar |
| `--file-changed` | FileChanged | Checks if changed file is `CLAUDE.md` or a memory file; emits system alert if so |
| `--suggest-guards` | PostToolUse (error-lookup.md only) | When `error-lookup.md` is updated, prompts to run Generate Guards |

### On demand (type in Claude Code)

| Subcommand | Command | What it does |
|------------|---------|-------------|
| `--quick-learn` | `Quick Learn` | Writes a stub placeholder immediately, then prompts for 1-3 lessons. No /learn ceremony. |
| `--kit-health` | `Kit Health` | Checks all kit components: hooks wired, MEMORY.md present, skills installed, complexity profile fresh |
| `--context-score` | `Context Score` | Scores every CLAUDE.md section by how often it appears in session journals — surfaces dead weight |
| `--guard-check` | `Guard Check` | Runs all named guards from `guard-patterns.md` against the codebase — reports violations |
| `--velocity-estimate "task"` | `Estimate: [task]` | Keyword-matches the task against `velocity.md` history — reports what similar tasks actually took |
| `--mine-patterns` | `Mine Patterns` | Clusters all `lessons.md` entries by keyword frequency — surfaces recurring mistakes |
| `--bootstrap` | `python tools/memory.py --bootstrap` | Scans entire codebase, generates a grouped file index for immediate codebase awareness |
| `--complexity-scan` | (auto on first Start Session) | Detects stack, DB, tests, API surface — scores complexity and recommends which skills to use |
| `--search "query"` | (terminal) | Full-text search across all memory files — scored results with context |
| `--mempalace-audit` | `Memory Audit` | Scans all memory files for missing `## Source` blocks, missing `valid_until` on state/project types, missing frontmatter — outputs a plain-text report |
| `--check-expiry` | `Check Memory Expiry` | Surfaces memories past their `valid_until` date or not yet active (`valid_from` in the future) — prompts to update or archive |
