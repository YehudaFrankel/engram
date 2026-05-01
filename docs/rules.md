# Rules — Path Scoping and Always-Load

Rules are markdown files in `.claude/rules/` that Claude reads as standing instructions. Two loading modes: always-load and path-scoped.

---

## Always-load rules

Rules that apply regardless of what file you're editing. Declared with `alwaysApply: true` and imported in CLAUDE.md via `@rules/`:

```yaml
---
description: Require a written plan before any code edit
alwaysApply: true
---
```

Keep this list short — every always-load rule consumes context on every turn. Good candidates:
- `plan-before-edit` — plan + approval before any edit
- `work-rules` — core behavioral rules
- `token-rules` — context management

---

## Path-scoped rules

Rules that only load when you're editing a matching file type. Declared with `globs` and `alwaysApply: false`:

```yaml
---
description: SQL injection patterns and quoting rules for Java + SQL files
globs:
  - "**/*.java"
  - "**/*.sql"
alwaysApply: false
---
```

Claude Code auto-discovers these when you open a matching file. They do not consume context on unrelated turns (e.g. editing CSS won't load your Java quoting rules).

**To activate path-scoping:** remove the rule from the `@rules/` imports in CLAUDE.md. If it stays in `@rules/`, it always loads regardless of frontmatter.

---

## Common glob patterns

| Files | Glob |
|-------|------|
| All Java | `**/*.java` |
| Java + SQL | `**/*.java`, `**/*.sql` |
| All JS/TS | `**/*.js`, `**/*.ts`, `**/*.jsx`, `**/*.tsx` |
| HTML + CSS + JS | `**/*.html`, `**/*.css`, `**/*.js` |
| Python | `**/*.py` |
| All code files | `**/*.{js,ts,java,py,go,rb,sql}` |

---

## Recommended split for a new project

| Rule | Mode | Why |
|------|------|-----|
| `plan-before-edit` | always-load | Applies to every file type — must include WAIT for approval |
| `work-rules` | always-load | Behavioral — not file-specific |
| `token-rules` | always-load | Context management — not file-specific |
| `karpathy-principles` | always-load | 4 universal coding principles: think first, simplicity, surgical changes, goal-driven |
| `coding-conventions` | path-scoped (`*.java`, `*.js`) | Only relevant when writing code |
| `database` | path-scoped (`*.java`, `*.sql`) | Only relevant near DB code |
| `design-system` | path-scoped (`*.html`, `*.css`, `*.js`) | Only relevant in frontend files |
| `error-lookup` | path-scoped (`*.java`, `*.js`) | Only relevant when debugging code |

CLAUDE.md stays under 150 lines. Context stays focused.

---

## Writing a new rule

```markdown
---
description: One-line summary — shown in Claude Code's rule picker, so be specific
globs:
  - "**/*.ts"
  - "**/*.tsx"
alwaysApply: false
---

## Rule title

Your instructions here. Be direct — Claude reads this verbatim before each turn
where a matching file is open.
```

Add it to `.claude/rules/`. If it should always load, also add `@rules/your-rule.md` to CLAUDE.md.
