# Clankbrain for Teams

## The Team Problem

The stateless problem is worse on a team.

One developer spends three hours debugging an obscure error, finds the root cause, fixes it, and moves on. Next week a teammate hits the same error. Same three hours. Zero information transferred.

One developer settles a difficult architectural debate and moves on. A new developer joins two months later, doesn't know the debate happened, and reopens it.

One developer learns that a particular approach fails in your stack. Nobody else knows. The next developer learns it the same way — by trying it.

The knowledge lives in individual heads, individual sessions, and individual conversations. It doesn't compound. It evaporates.

Clankbrain makes the team's collective knowledge load automatically for every developer, every session.

---

## How It Works at Team Scale

Every developer has their own Clankbrain setup. Personal memory — their own lessons, their own session journal, their own velocity data — stays local.

Shared memory syncs across the team. When one developer settles an architectural decision, it goes into shared memory. When one developer logs the root cause of a hard error, every developer has that fix on their next Start Session. When one developer marks an approach as rejected, nobody on the team proposes it again.

The team lead runs `Setup Team` once. Every developer runs `Join Team` once. After that, every Start Session silently pulls the latest shared memory before anyone types a word.

---

## What One Developer's Work Buys the Whole Team

### One debug session. Zero reruns.

**Before:** Developer A spends two hours on an error nobody has seen before. Finds the fix. Closes the session. Developer B hits the same error three weeks later. Same two hours.

**After:** Developer A's session ends with the root cause logged to the shared error-lookup file. Developer B's Start Session pulls it automatically. When the error appears, the fix surfaces before Claude starts investigating. Five minutes instead of two hours.

### One rejected approach. Blocked for everyone.

**Before:** Your team decides approach X doesn't work in your stack. Each developer learns this eventually, usually by trying it. The learning cost gets paid once per developer.

**After:** The approach gets logged to shared `regret.md` once. The regret-guard hook scans every prompt for every developer against this file. Nobody on the team goes down that path again — including developers who join six months from now.

### One architectural debate. Settled permanently.

**Before:** The senior developer settles a difficult design question. The reasoning lives in a Slack thread nobody will find, or in a comment nobody reads, or nowhere. The same debate resurfaces every time a new developer touches that part of the codebase.

**After:** The decision goes into shared `decisions.md` with the context, the rationale, and when it applies. Every developer reads it automatically at Start Session. The debate does not reopen.

---

## What Onboarding Looks Like

**Before:** A new developer joins. They spend the first two weeks asking questions that have already been answered, making mistakes that have already been made, and learning the codebase's failure modes one by one. Tribal knowledge lives in other people's heads. It transfers slowly, incompletely, and only when someone has time to explain it.

**After:** A new developer joins. They run two commands and type `Handoff`. Claude produces a complete document: current state of the project, the next three tasks, every settled architectural decision and why, known bugs and their status, and the gotchas that aren't obvious from the code.

The shared memory is the onboarding document. It's built automatically from every session of accumulated decisions, lessons, and patterns across the whole team. It's always current. Nobody had to write it.

The new developer is fully context-aware before writing a line of code.

---

## What the Team Lead Sees

Every developer's End Session updates the shared memory. What compounds is not just individual knowledge — it's the team's collective knowledge, growing automatically every session.

Over time:

- Architectural decisions stick across the whole team, not just in the head of whoever made them
- Errors get debugged once and never again, by anyone
- Onboarding takes two minutes instead of two weeks
- When a developer leaves, the knowledge stays

The developers who leave take their personal memory with them. The shared knowledge doesn't go anywhere.

---

## Rolling It Out

### Week 1 — One developer, one project

Start with your most active developer on your most active project. Run `npx clankbrain` and choose Full. Run Start Session and End Session for one week.

This isn't a pilot. This is building the foundation the rest of the team will pull from.

### Week 2 — Connect the team

That developer runs `Setup Team` once. This creates the shared memory repo and configures sync.

Every other developer runs `Join Team` once. From this point, every Start Session silently pulls the shared memory before anyone types a word.

### Week 3 and beyond — Let it compound

No new habits required beyond two commands. Start Session. End Session. The shared memory grows automatically. Every debug session, every settled decision, every rejected approach adds to what every developer loads the next morning.

After 10 team sessions, the shared error-lookup file has real entries. After 20, `decisions.md` covers the major architectural questions. After 50, a new developer can onboard from the accumulated memory alone.

---

## The Honest Part

This only works if every developer runs End Session. One developer skipping it doesn't just cost them their own compounding — it costs the team the knowledge they would have contributed.

The team lead's job in the first two weeks is to make the habit stick. After that, the system runs itself.

Three rules: **Always run End Session. Run `/evolve-check` to see which skills need patching. Run `/evolve` when skills are flagged.** Everything else is automatic.

`/evolve-check` takes 5 seconds and shows exactly which skills are urgent, which are ready to patch, and which need better failure data before they can be improved. It never changes anything — it just surfaces what needs attention.

---

## Getting Started

```
npx clankbrain
```

Choose Full. One developer, one project, one week to build the foundation. Then `Setup Team`. Then `Join Team` for every developer.

That's the whole rollout.

---

*Built by Yehuda Frankel. Tested across 160+ real sessions on a production codebase.*
*[github.com/YehudaFrankel/clankbrain](https://github.com/YehudaFrankel/clankbrain)*
