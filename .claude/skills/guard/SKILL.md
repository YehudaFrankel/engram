---
name: guard
description: Scans recently changed files against a growing library of known error patterns, flags violations before they ship. After any bug fix, extracts the root cause as a new permanent rule. Trigger on "guard check", "scan for issues", "check conventions", "did I miss anything", "scan my changes".
keep-coding-instructions: true
---

# Guard — Pattern Scanner + Rule Logger

Guard has two jobs:
1. **Scan** — check recently changed files against all known error patterns
2. **Learn** — after any bug fix, extract the root cause as a new checkable rule so it never happens again

---

## Step 1: Identify files to scan

Pull from conversation context: which files were just edited?
If not clear, ask: "Which files should I scan?"

---

## Step 2: Load the pattern library

Read `.claude/rules/guard-patterns.md`.

If the file does not exist, create it with at least these starter patterns:
- Auth check missing on protected endpoint
- User input concatenated directly into SQL query
- Missing error handling on async operation
- Hardcoded environment-specific value (localhost, test credential)
- Console.log / debug print left in production code

---

## Step 3: Scan each file against every pattern

For each pattern in guard-patterns.md, run a targeted grep on the changed file(s).

Report each violation clearly:

```
⚠️  [PATTERN NAME]
   File: src/routes/admin.js:42
   Code: db.query("SELECT * WHERE id=" + req.params.id)
   Why:  Raw string concatenation = SQL injection. Use parameterized queries.
```

If nothing is wrong: `✓ All [N] pattern checks passed. Nothing flagged.`

---

## Step 4: Learn mode — run after every bug fix

After any bug is fixed, extract the pattern and make it permanent.

1. **Name the pattern** — short, screaming-snake-case ID (e.g. `MISSING_AUTH_CHECK`)
2. **Describe the violation** — one sentence, concrete
3. **Write the grep** — what to search for, what signals a violation
4. **Explain why** — what goes wrong at runtime if this is missed
5. **Append** the new entry to `guard-patterns.md`
6. Report: `New rule added: [PATTERN NAME] — will be checked on every future guard scan.`

The point is: every bug that gets fixed once should be impossible to ship twice.

---

## Step 5: Report summary

```
Guard scan complete — [N] patterns checked, [M] violations found.
[List violations or "All clear."]
[List any new rules added this run.]
```
