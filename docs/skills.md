# Skills and the Learning Loop

Skills are auto-triggered workflows. Describe what you need in plain English — the right skill fires automatically.

---

## Built-in skills

| Skill | What triggers it | What it does |
|-------|-----------------|-------------|
| `plan` | "plan [feature]", "I want to build X" | Structured planning — options with ratings, decision logged live |
| `verification-loop` | "verify this works", "before I ship" | Compile + smoke test + self-check after every change |
| `search-first` | "add new endpoint/feature" | Research before coding — finds existing implementations |
| `strategic-compact` | "should I compact?" | Safe context compaction without losing memory |
| `learn` | `/learn`, "End Session" | Extracts lessons, scores skills with step-level failure data, logs velocity |
| `evolve` | `/evolve` | Patches failing skills (2+ failures required), clusters patterns into new reusable skills |
| `evolve-check` | "evolve check", "skill health" | Read-only analysis — surfaces which skills are 🔴 urgent / 🟡 ready / 🟢 stable. No patching. |
| `code-reviewer` | "review this", "check this code" | Reviews against your project's past lessons and locked decisions — gets smarter every session |

Type `Generate Skills` and Claude creates additional skills tailored to your exact stack and file names.

---

## Optional skills

Skills that ship in the kit but aren't wired up by default. Add any with a single command.

| Skill | Install command | What it does |
|-------|----------------|-------------|
| `map-codebase` | `Install the map-codebase skill` | Builds a `code-map.md` organized by feature flow — entry point -> logic -> DB. Run once to bootstrap navigation; re-run after major structural changes. |
| `debug-session` | `Install the debug-session skill` | Structured diagnosis: reproduce -> isolate -> hypothesize -> fix -> verify -> log to regret.md |

---

## The learning loop

When a skill gets something wrong and you correct it, that correction gets logged. Run `/evolve` every few sessions:

```
session work
     |
/learn  ->  lessons.md        (patterns this session)
        ->  skill_scores.md   (Step N: produced X, needed Y — structured failure data)
        ->  velocity.md       (estimated vs actual)
             |
      /evolve-check  ->  groups failures by skill
                     ->  flags 2+ Y entries as ready to patch
                     ->  flags vague entries as data-missing (cannot patch)
                     ->  "Run /evolve on flagged skills now? [y/N]"
             |
      /evolve  ->  skips skills with only 1 failure (noise)
               ->  skips skills with vague "What Failed" (insufficient data)
               ->  reads step number + failure description -> patches exact step
               ->  clusters repeated lessons into new skills
               ->  logs every change to skill_improvements.md
             |
        better skills next session
```

Run `/learn` before End Session. Run `/evolve-check` to see what needs patching. Run `/evolve` when skills are flagged 🔴 or 🟡. The same skill failure at the same step is architecturally impossible after `/evolve` runs.

---

## What gets smarter over time

| File | What it tracks | Effect |
|------|---------------|--------|
| `lessons.md` | Patterns and fixes extracted by /learn | Applied before any code is touched each session |
| `decisions.md` | Settled architectural choices | Claude never re-debates what's already decided |
| `skill_scores.md` | Step-level failure log per skill: Step N / produced X / needed Y / Severity | /evolve-check surfaces patterns; /evolve patches the specific failing step |
| `regret.md` | Approaches tried and rejected | Never re-proposed — saves re-litigating bad ideas |
| `error-lookup.md` | Known errors -> cause -> fix | Surfaced automatically before you start investigating |
| `velocity.md` | Estimated vs actual sessions per task | Estimates reflect real track record after 20+ entries |
| `global-lessons.md` | Lessons that apply across all projects | Loaded at Start Session on every project you work on |

---

## Skill chaining

Add `## Auto-Chain` to any skill and it triggers the next step automatically:

```
fix-bug -> verification-loop -> smoke-test
                |
           if fail:
           debug-session -> smoke-test
```

No human steps between. Build your own chains by adding one section to any skill file.

---

## Self-healing

When a verify step fails, Claude attempts the minimal fix and retries once before escalating. Add a `## Recovery` section to a skill file to define what "minimal fix" means for that skill.
