---
name: ux-heuristics
description: Evaluates interface usability using Nielsen's 10 heuristics + Krug's principles. Returns a severity-scored list of issues. Triggers on "audit this for usability", "heuristic review", "UX issues", "usability check", "ux heuristics".
allowed-tools: Read
---

# UX Heuristics

Evaluates interface usability using Nielsen's 10 heuristics + Krug's "Don't Make Me Think" principles. Returns a severity-scored list of what's broken and why.

---

## Core Philosophy

Users scan, they don't read. They satisfice, they don't optimize. They muddle through, they don't figure out.

> "Every page should be self-evident. If something requires thinking, it's a usability problem." — Steve Krug

---

## Krug's Three Laws

1. **Don't make me think.** Pages should be self-evident. Clear labels beat clever marketing copy.
2. **It doesn't matter how many times I click, as long as each click is mindless.** Minimize cognitive effort per interaction.
3. **Get rid of half the words on each page, then get rid of half of what's left.** Ruthlessly eliminate unnecessary text.

---

## The Trunk Test

Drop a user on any random page. Can they immediately answer:
- What site is this? What page am I on? What are the major sections?
- What are my options at this level? Where am I in the hierarchy? How can I search?

If any answer requires effort, the navigation is broken.

---

## Nielsen's 10 Heuristics

| # | Heuristic | What to Check |
|---|-----------|---------------|
| 1 | Visibility of System Status | Loading indicators? Form submission feedback? Current state visible? |
| 2 | Match System and Real World | Jargon-free labels? Natural reading order? Icons match mental models? |
| 3 | User Control and Freedom | Undo available? Cancel on every modal? No dead ends? |
| 4 | Consistency and Standards | Same action = same label? Button styles consistent? |
| 5 | Error Prevention | Confirmation for destructive actions? Inline validation? Disabled states? |
| 6 | Recognition Rather Than Recall | Options visible? Recent items surfaced? Labels on icons? |
| 7 | Flexibility and Efficiency | Keyboard shortcuts? Bulk actions? Search as navigation? |
| 8 | Aesthetic and Minimalist Design | Only essential info visible? Progressive disclosure? White space? |
| 9 | Help Recover from Errors | Plain language? Specific not generic? Suggest a fix? |
| 10 | Help and Documentation | Searchable? Task-focused? Concrete steps? |

---

## Severity Scale

| Severity | Label | Priority |
|----------|-------|----------|
| 0 | Not a problem | Skip |
| 1 | Cosmetic | Fix if time permits |
| 2 | Minor | Fix in next iteration |
| 3 | Major | Fix before shipping |
| 4 | Catastrophic | Fix immediately |

---

## Audit Output Format

| # | Heuristic Violated | Issue | Severity | Recommendation |
|---|-------------------|-------|----------|----------------|
| 1 | H8: Minimalist Design | Dashboard shows 12 metrics above fold | 2 | Progressive disclosure: show top 4, expand for rest |
| 2 | H1: System Status | No loading indicator on search | 3 | Add spinner or skeleton screen |

Sort by severity (highest first). Summary: total issues, count by severity, top 3 fixes.

---

## Quick Diagnostic Checklist (60 seconds)

- [ ] Can I tell what page this is and what I can do here?
- [ ] Is there a clear visual hierarchy?
- [ ] Do all interactive elements look clickable?
- [ ] Is there feedback when I take an action?
- [ ] Can I undo or go back easily?
- [ ] Are error messages helpful and specific?
- [ ] Does it work on mobile without hover?
- [ ] Are tap targets large enough (44x44px)?
- [ ] Is the most important action obvious?
- [ ] Would a first-time user know what to do?
