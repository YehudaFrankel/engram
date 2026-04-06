# Every Command

Type these in Claude Code chat. All commands are plain English.

---

## Daily

| Command | What it does |
|---------|-------------|
| `Start Session` | Reads memory, applies lessons, surfaces open plans, picks up where you left off |
| `End Session` | Runs /learn, updates STATUS.md, saves everything to memory locally |
| `/learn` | Extracts lessons, scores skills with step-level failure data (Step N / produced X / needed Y), logs velocity — auto-runs at End Session |
| `/evolve-check` | Read-only skill health check — shows 🔴 urgent / 🟡 ready / 🟢 stable / ⚠️ data-missing. Run before /evolve. |
| `/evolve` | Patches failing skills (requires 2+ Y entries with structured failure data), clusters repeated patterns into new reusable skills |
| `Quick Learn` | Fast lesson capture — writes a stub immediately, then prompts for 1-3 lessons |
| `Plan [feature]` | Structured planning — options with ratings, decision logged live |
| `Show Plan` | Display the full current plan file — always the complete document, never a summary |
| `Should I compact?` | Guides safe context compaction without losing memory |

---

## Memory

| Command | What it does |
|---------|-------------|
| `/recall [topic]` | Semantic search across all memory files — finds related memories even if the wording is different. Falls back to keyword search automatically if the index isn't built. |
| `/forget [topic]` | Invalidate a stale or wrong memory — marks it as removed, keeps history intact |

### Semantic search setup (one-time)

`/recall` uses embedding-based search when enabled. To set it up:

```bash
pip install sentence-transformers
python tools/memory.py --build-index
```

This downloads `all-MiniLM-L6-v2` (~90MB, runs fully locally, no API key) and builds `memory_embeddings.pkl` in your memory directory. Rebuild whenever you add significant new memory files:

```bash
python tools/memory.py --build-index   # rebuild index
```

You can also run it directly:

```bash
python tools/memory.py --search-semantic "why did we move files to mobile"
python tools/memory.py --search-semantic "auth error on admin endpoints" --top 10
```

Without the index, `/recall` falls back to keyword scoring (the original behavior) — no setup needed to get started.

**What if it fails?**

| Scenario | What happens | How to fix |
|----------|-------------|------------|
| `sentence-transformers` not installed | `/recall` falls back to keyword search automatically — no error shown | Run `pip install sentence-transformers` when ready to enable semantic mode |
| Model download interrupted (network drop mid-download) | `--build-index` fails with an import or file error on next run | Delete `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2` and re-run `--build-index` |
| `memory_embeddings.pkl` corrupted or from a different model version | `--search-semantic` prints a load error and exits; keyword search still works | Delete `.claude/memory/memory_embeddings.pkl` and re-run `--build-index` |

In all three cases, keyword search continues to work. `/recall` will never silently return wrong results.

---

## Analysis

| Command | What it does |
|---------|-------------|
| `Progress Report` | Dashboard of sessions, lessons, errors, skill accuracy — built from your actual history |
| `Check Drift` | Manually run drift detector — find undocumented functions and stale memory entries |
| `Analyze Codebase` | Full scan of all JS, CSS, and backend — documents every function, class, and endpoint |
| `Code Health` | Finds leftover console.log, hardcoded values, dead code, missing error handling — reports file + line |
| `Kit Health` | Check all kit components are wired and healthy |
| `Context Score` | Score every CLAUDE.md section by session journal usage — find dead weight bloating your context |
| `Mine Patterns` | Cluster lessons.md across all sessions — surface recurring mistakes you haven't noticed |
| `Guard Check` | Run all named guards from `guard-patterns.md` against the codebase, report violations |
| `Estimate: [task]` | Match task to past velocity history — reports what similar tasks actually took, not what felt right |
| `/check-anthropic` | Fetch Claude Code releases and docs, cross-reference hooks and features in use, report gaps |

---

## Planning

| Command | What it does |
|---------|-------------|
| `Debug Session` | Structured diagnosis: reproduce -> isolate -> hypothesize -> fix -> verify -> log to regret.md |
| `Handoff` | Generates HANDOFF.md — current state, next 3 tasks, key decisions, known bugs, how to start |

---

## Setup and recovery

| Command | What it does |
|---------|-------------|
| `Setup Memory` | First-time setup — creates all memory files for your project |
| `Install Memory` | New machine — copies memory files to Claude's system path |
| `Generate Skills` | Auto-creates skills tailored to your actual stack, file names, and patterns |
| `Upgrade to Full` | Upgrade from Lite to Full mode — downloads memory.py and wires lifecycle hooks |
| `Update Kit` | Pulls latest kit version — shows what will change, asks for confirmation. Never touches your memory, skills, or code. |

---

## Sync (opt-in)

| Command | What it does |
|---------|-------------|
| `Setup Sync: [repo URL]` | One-time setup — points memory at your private GitHub repo |
| `Sync Memory` | Push memory to your repo after a session |
| `Pull Memory` | Pull memory on a new machine |
| `Sync Status` | Check if anything is unpushed |
| `Setup Team: [repo URL]` | Manager runs once — creates the shared repo and seeds it with your memory |
| `Join Team: [repo URL]` | New member runs once — loads the team's knowledge into your local memory |
| `Team Push` | Share what you learned with the team. Run at End Session. |
| `Team Status` | Check last sync times and recent commits |

Team Pull runs automatically at Start Session — no command needed.
