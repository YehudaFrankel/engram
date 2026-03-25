---
name: powershell-safe
description: Enforce safe PowerShell string patterns before writing or editing any .ps1 file, or before passing PowerShell via the Bash tool. Triggers on "write a powershell script", "edit the .ps1", "run powershell", "powershell command", or any task that produces PowerShell content.
allowed-tools: Read, Edit, Write, Bash
---

# Skill: powershell-safe

**Auto-applies whenever writing, editing, or running PowerShell content.**

---

## Rules — apply every time, no exceptions

### 1. ASCII-only strings
- **Never** use em dashes (`—`) — replace with hyphen-minus (`-`) or ` -- `
- **Never** use curly/smart quotes (`"` `"` `'` `'`) — use straight quotes only
- **Never** use emoji in string literals or comments inside `.ps1` files
- **Never** copy-paste text from markdown/chat that may contain Unicode punctuation

> Em dashes silently corrupt `.ps1` files — PowerShell parses them as unknown tokens, failing with no clear error message.

### 2. Variable interpolation via Bash tool
When passing PowerShell through the Bash tool, `$variables` get expanded by the shell before PowerShell sees them:
- Wrap the entire command in **single quotes** to prevent shell expansion, OR
- Escape every `$` as `` `$ `` inside double-quoted Bash strings, OR
- Write to a `.ps1` file first, then execute: `powershell -File script.ps1`

```bash
# WRONG — $name expanded by shell, PowerShell sees empty string
powershell -Command "Write-Output $name"

# RIGHT — single quotes prevent shell expansion
powershell -Command 'Write-Output $name'

# RIGHT — write file, execute file
echo 'Write-Output $name' > tmp.ps1 && powershell -File tmp.ps1
```

### 3. Backticks in strings
PowerShell uses backtick (`` ` ``) as its escape character. Inside Bash double-quoted strings, backticks trigger command substitution:
- Use **single quotes** for the outer Bash string when the PowerShell content contains backticks
- Or escape as `` \` `` in double-quoted contexts

### 4. Here-strings via Bash
PowerShell here-strings (`@" "@` or `@' '@`) are fragile through Bash:
- The closing `"@` or `'@` **must be at the start of a line with no leading whitespace**
- Prefer writing the script to a file and executing it instead

### 5. Test before embedding
For any non-trivial PowerShell string, test with `Write-Output` first:
```powershell
Write-Output "your string here"
```
Verify it prints cleanly before embedding in a larger command or script.

---

## Checklist — run before writing any PowerShell

- [ ] No em dashes, smart quotes, or emoji in string literals
- [ ] `$variables` protected from shell expansion (single quotes or file-based execution)
- [ ] Backticks handled correctly for context (Bash single-quoted or escaped)
- [ ] Here-string closers at column 0 if used
- [ ] Tested with `Write-Output` if any doubt about a string value

---

## Common failures

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `Unexpected token` with no obvious cause | Em dash in string | Replace `—` with `-` |
| `$variable` always empty | Shell expanded it before PowerShell ran | Single-quote the Bash string |
| Here-string parse error | Closing `"@` has leading whitespace | Move to column 0 |
| Backtick disappears | Bash swallowed it as command substitution | Single-quote the Bash wrapper |
