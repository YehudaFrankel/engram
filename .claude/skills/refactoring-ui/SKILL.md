---
name: refactoring-ui
description: Tactical rules for making interfaces look intentional and polished. Specific, actionable fixes for the most common visual problems. Triggers on "my UI looks off", "fix the design", "visual hierarchy", "polish the UI", "refactoring ui".
allowed-tools: Read, Edit
---

# Refactoring UI

Tactical rules for making interfaces look intentional, professional, and polished. Specific, actionable fixes for the most common visual design problems.

**Trigger:** "my UI looks off" / "fix the design" / "visual hierarchy" / "polish the UI" / "refactoring ui"

## Core Approach

**Work in grayscale first.** Solve layout, spacing, and hierarchy before introducing color.

**Design systems beat one-off decisions.** Define spacing scale, type scale, color palette — apply consistently.

---

## Hierarchy

**Use all four sources:**
1. **Size** — larger = more important
2. **Weight** — bold = more important
3. **Color** — darker = more important; secondary content uses muted color
4. **Spacing** — related elements sit closer

**De-emphasize to create contrast.** Making less-important things lighter is often more effective than making important things bolder.

**Labels vs. values.** Labels (name, date, status) are secondary — make them smaller/lighter. Values are primary.

---

## Whitespace

**Start with too much, then remove.** Most designs are too dense.

**Dense != information-rich.** Dense layouts feel cheap. Whitespace signals quality.

**Space between sections > space within sections.** Use 2-3x more space between unrelated sections.

---

## Shadows

**Two-part shadows are more realistic:**
- Small, sharp, close shadow (1-2px offset, no blur, 0.1 opacity)
- Larger, blurred ambient shadow (4-8px offset, 8-16px blur, 0.05 opacity)

**Never use black for shadow color.** Use a darkened version of the background color.

**Don't apply shadows everywhere.** Reserve for: floating cards, dropdowns, modals, hover states.

---

## Borders

**Use less of them.** Most of the time you need better spacing or a background color change.

**Four alternatives to borders:**
1. Background color — slightly different surface color
2. Box shadow — subtle shadow instead of border
3. Spacing — more whitespace creates separation
4. Bold heading — section title creates separation implicitly

---

## Color

**Never use grey on a colored background.** Use a lighter tint of the background color instead.

**One accent color.** Everything interactive uses it. Everything else does not.

**Define a full 9-step scale (100-900)** for each color in your palette.

---

## Typography

**Don't use more than two typefaces.**

**Line height scales inversely with font size.** Large headings: 1.1-1.2. Body text: 1.5-1.6.

**Limit your type scale.** Pick 6-8 sizes: 12, 14, 16, 18, 24, 30, 36, 48.

**Letter spacing for all-caps.** Always add `letter-spacing: 0.05-0.1em` to all-caps text.

---

## Refactoring Diagnostic Order

When something looks wrong, work through this order:
1. **Hierarchy problem?** Is there a clear dominant element?
2. **Spacing problem?** Too dense? Inconsistent padding?
3. **Color problem?** Low contrast? Too many competing colors?
4. **Typography problem?** Too many sizes? Inconsistent weights?
5. **Shadow/border problem?** Too many borders? Shadows too dark?
6. **Component problem?** Missing interaction states? Inconsistent radius?

Fix in this order. Hierarchy first — it usually solves the other problems.

---

## Quick Wins

| Problem | Fix |
|---------|-----|
| Everything same visual weight | Pick one primary element per section, de-emphasize rest |
| Looks like a form, not a product | Add generous padding, remove borders, increase section spacing |
| Colors feel muddy | Saturate more aggressively; add colorized greys |
| Shadows look fake | Use two-part shadows; never pure black |
| Typography unfinished | Tighten heading line height; add letter-spacing to all-caps |
| Terrible on mobile | Check at 375px; ensure touch targets >= 44pt |
