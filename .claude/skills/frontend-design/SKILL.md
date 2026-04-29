---
name: frontend-design
description: Commits to a bold design direction before writing a single line of CSS. Generates a complete design system — palette, font pairing, style direction, and UX rules. Triggers on "build a landing page", "design this UI", "create a component", "design system for", "new page design", "frontend design".
allowed-tools: Read, Write, Edit
---

# Frontend Design

Commits to a bold design direction before writing a single line of CSS. Generates a complete design system — palette, font pairing, style direction, and UX rules — for a specific product type.

**Trigger:** "build a landing page" / "design this UI" / "create a component" / "design system for" / "new page design" / "frontend design"

---

## Step 1 — Commit to a Direction

Before any code, answer these five questions:

1. **What is this product's purpose?** (utility tool, community space, marketplace, content platform)
2. **Who is the primary audience?** (age, tech literacy, context of use — mobile on the go? desktop at work?)
3. **Which archetype fits?** (choose from the 10 below)
4. **What makes this NOT look like every other app?** (the one visual choice that creates identity)
5. **What are the anti-goals?** (what should this explicitly NOT look like?)

---

## Step 2 — Choose an Archetype

| Archetype | Signature Elements | Best For |
|-----------|-------------------|----------|
| **Editorial** | Serif headings, generous whitespace, magazine-like layouts | Content platforms, newsletters, blogs |
| **Swiss** | Grid-based, grotesque fonts, asymmetric balance, bold color blocks | Portfolios, agencies, design tools |
| **Brutalist** | Raw HTML feel, monospace fonts, harsh borders, stark contrast | Developer tools, art projects |
| **Minimalist** | One accent color max, extreme whitespace, barely-there UI | Productivity apps, utilities |
| **Maximalist** | Rich textures, layered elements, multiple colors | Entertainment, games, creative tools |
| **Retro-Futuristic** | Neon accents on dark, mono fonts, terminal aesthetics | Dev tools, music apps |
| **Organic** | Warm tones, rounded shapes, natural textures | Wellness, food, community |
| **Industrial** | Dark backgrounds, yellow/orange accents, utility-first | Construction, logistics |
| **Art Deco** | Gold accents, geometric patterns, luxury feel | Finance, premium products |
| **Lo-Fi** | Paper textures, sketch-like borders, handwritten fonts | Personal projects, indie apps |

---

## Step 3 — Generate Design Tokens

**Rule:** Every value in CSS must reference a token. Zero hardcoded colors, spacing, or font sizes.

### Required Token Categories

1. **Colors** — primary, secondary, accent, surface, text (with full 100-900 scales)
2. **Typography** — font families (max 2), size scale (6-8 steps), weight scale, line heights
3. **Spacing** — consistent scale (4, 8, 12, 16, 24, 32, 48, 64, 96)
4. **Borders** — radius scale (sm, md, lg, full), width scale, color
5. **Shadows** — elevation levels (sm, md, lg, xl)
6. **Motion** — duration scale (fast: 150ms, normal: 300ms, slow: 500ms), easing curves

---

## Step 4 — Typography Rules

**Distinctive fonts only.** Avoid: Inter, Roboto, Arial, Open Sans, Lato, Montserrat (overused).

Recommended pairings by archetype:
| Archetype | Heading | Body |
|-----------|---------|------|
| Editorial | Playfair Display | Source Serif Pro |
| Swiss | Space Grotesk | DM Sans |
| Brutalist | Space Mono | IBM Plex Mono |
| Minimalist | DM Sans | DM Sans (weight variation) |
| Organic | Fraunces | Nunito |
| Art Deco | Poiret One | Josefin Sans |
| Lo-Fi | Caveat | Karla |

**Weight contrast:** Use extreme differences — 300 for body, 700+ for headings.
**Line height:** Headings 1.1-1.2, body 1.5-1.6.

---

## Step 5 — Color System

**The 60-30-10 rule:**
- 60% dominant surface color
- 30% secondary color
- 10% accent color (CTAs, highlights)

**Avoid cliches:** Purple/indigo gradients, blue-only accents, neon on dark (unless Retro-Futuristic).

---

## Step 6 — Component Standards

**Every interactive element needs:** Default, Hover, Active, Focus (visible ring), Disabled, Loading states.

**Responsive breakpoints:** Mobile 375px (design here first), Tablet 768px, Desktop 1024px.

**Touch targets:** Minimum 44x44px on mobile.

**Empty states:** Design before full states. Show illustration + message + primary action.

---

## Step 7 — Quality Checklist

- [ ] Archetype consistent across all elements
- [ ] All values use tokens — zero hardcoded colors/spacing/sizes
- [ ] Typography is distinctive (not Inter/Roboto/Arial)
- [ ] 60-30-10 color distribution holds
- [ ] WCAG AA contrast (4.5:1 text, 3:1 large text)
- [ ] Responsive at 375px, 768px, 1024px
- [ ] All interactive states designed
- [ ] Empty states designed
