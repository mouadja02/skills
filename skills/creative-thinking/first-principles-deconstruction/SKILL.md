---
name: first-principles-deconstruction
description: Dismantles any problem down to its bedrock truths, then rebuilds solutions from scratch — ignoring industry conventions, borrowed assumptions, and "how it's always been done." Activate when the user is stuck in conventional solutions, wants to understand why something is done the way it is, or needs to design something genuinely novel.
---

# First-Principles Deconstruction

Most problems are solved by analogy: we look at what others have done, tweak it slightly, and call it a solution. First-principles thinking refuses this shortcut. It asks: what is actually, irreducibly true here — and if we built from only those truths, what would we arrive at?

Elon Musk didn't make cheaper rockets by negotiating with rocket suppliers. He asked: what is a rocket actually made of? What do those materials cost on the commodity market? What physics govern thrust-to-weight ratios? Then he built from there, arriving at 10x cost reduction not by optimizing the existing approach but by abandoning it entirely.

## When to Activate

Activate this skill when:
- The user feels trapped in a conventional framing of a problem
- Existing solutions feel expensive, inefficient, or wrong, but no one can articulate why
- The user says "why do we do it this way?" without a satisfying answer
- A design feels like an accumulation of historical accidents rather than intentional choices
- The user needs to build something genuinely new, not a derivative of existing products

## The Deconstruction Protocol

### Step 1: Identify the Claim or Assumption

Extract every assumption embedded in the problem statement. Assumptions often hide as:
- Inherited constraints ("We've always used a database for this")
- Industry standards ("This is how all SaaS products work")
- Resource assumptions ("This requires engineers to build")
- User assumptions ("Users won't do X")
- Time assumptions ("This takes months to build")

Write them all down. Do not evaluate them yet — just surface them.

### Step 2: Question Each Assumption

For each assumption, ask the Socratic trio:
1. **Is this actually true?** — What evidence supports it? What would have to be true for it to be false?
2. **Is this always true?** — Are there contexts where this assumption breaks down? Who does it differently?
3. **What does the world look like if this is false?** — If this assumption were wrong, what becomes possible?

This step is uncomfortable. Most assumptions feel self-evidently true until examined. That feeling is a signal — push through it.

### Step 3: Identify the Bedrock

Bedrock truths are claims that survive all three questions — they are true regardless of context, convention, or technology. Examples:
- "Information moves at the speed of light" (physics bedrock)
- "Humans have approximately 24 hours per day" (biology bedrock)
- "Trust requires repeated positive interactions over time" (psychology bedrock)
- "Code that is never executed cannot have bugs" (logic bedrock)

Separate bedrock from convention. Most "constraints" are conventions masquerading as bedrocks.

### Step 4: Rebuild from Bedrock

Starting only from the bedrocks identified in Step 3, ask:
- If we had never seen this problem solved before, what solution would we design?
- What does the ideal version of this look like, constrained only by actual physics, biology, and logic?
- What does the solution look like at 10x scale, built on these foundations?

This step often produces solutions that feel obvious in hindsight but are radical departures from current practice.

### Step 5: Identify the Bridge

First-principles solutions are often not immediately implementable — they require capability or context that doesn't yet exist. Identify:
- What capabilities are needed to implement the first-principles solution?
- Which of those capabilities can be built today?
- What is the minimum viable first step toward the first-principles solution?

This bridges vision with action without compromising the destination.

## The Assumption Taxonomy

Not all assumptions are equal. Classify each assumption:

**Type A — Physics/Biology/Math** (true bedrock)
Cannot be violated. Work within them. Examples: speed of light, human attention limits, mathematical proofs.

**Type B — Technology Constraints** (current-era bedrock, will change)
True today but not forever. Identify which era they belong to. "Large language models cannot reason" was a Type B assumption in 2020.

**Type C — Economic Constraints** (context-dependent)
True at the current scale or cost structure, but potentially false at a different scale. Batteries were "too expensive for electric cars" until manufacturing scale changed the economics.

**Type D — Social/Cultural Conventions** (often invisible)
The most important to surface. "Users prefer familiar interfaces" is a convention that can be changed by sufficiently good product design. "Enterprise software must be sold by salespeople" was a convention that SaaS disrupted.

**Type E — Organizational Habits** (pure convention)
These are the most common and the least defensible. "We do code reviews on Fridays," "we use this stack because our founding engineers knew it." No physical law enforces these.

## Output Format

### Deconstruction Report

**The Original Problem:**
[Restate the problem as given]

**Embedded Assumptions:**
| # | Assumption | Type (A-E) | Challenge |
|---|---|---|---|
| 1 | [assumption] | [type] | [what if false?] |

**The Bedrocks:**
List only Type A and B truths that survived questioning.

**The First-Principles Solution:**
Describe what the solution looks like built only from bedrocks — no conventions allowed.

**The Bridge:**
The minimum viable step from current state toward the first-principles solution, doable within existing constraints.

**The Assumptions Worth Attacking:**
Pick 1-3 Type D or E assumptions most worth challenging. These are where competitive advantage lives.

## Examples

**Problem:** "How do we reduce customer support costs?"

**Conventional approach:** Hire cheaper agents, build an FAQ, implement a chatbot.

**First-Principles Deconstruction:**

Assumption 1: "Support is needed because users get confused."
- Why do users get confused? Because the product is unclear.
- First-principles insight: The cheapest support ticket is the one that never gets created.

Assumption 2: "Support agents need to respond to every ticket."
- What is a support agent actually doing? Converting confusion into clarity.
- Bedrock: Clarity can be encoded once and distributed infinitely.

Assumption 3: "Support cost scales with user count."
- Does it have to? What if every resolved ticket made the next identical ticket self-resolving?
- First-principles solution: Build a system where every ticket resolution automatically updates the product, documentation, or onboarding to prevent recurrence.

**First-principles solution:** Product-driven support elimination. Every support interaction becomes a product team input, not a support team cost. The goal is to make the support team's job obsolete by fixing the product they're explaining.

---

**Problem:** "How do we improve code review quality?"

**Assumptions surfaced:**
- Code review requires human reviewers (Type B — technology changing this now)
- Reviews happen after code is written (Type D — cultural convention)
- Feedback is delivered as text comments (Type D — convention)

**First-principles solution:** Design the feedback loop into the writing process, not after it. Pair programming, live AI review, automated constraint checking while typing — make the review continuous rather than episodic.

## Guidelines

1. Always complete the full deconstruction before proposing solutions — jumping to solutions too early recreates conventional thinking
2. The most valuable step is often identifying the Type D assumptions — these are where real competitive advantage lives
3. First-principles solutions often feel "too simple" or "obviously impossible" — both reactions indicate you've found something real
4. The bridge step is as important as the vision — a solution with no path is philosophy, not strategy
5. Don't apply first-principles thinking to every problem — reserve it for decisions that are expensive to reverse or where the stakes are high

## Gotchas

1. **Confusing "difficult" with "bedrock"** — something being hard to change is not the same as it being physically impossible to change. Many Type D assumptions feel like Type A.

2. **Stopping at one level** — "Users need a login page" can be questioned (why do users need to log in? What are we protecting?), which itself can be questioned (why does that need protection in this way?). Keep going until you hit actual physics.

3. **First-principles thinking as skepticism theater** — questioning everything without ever committing to a rebuilt solution is not first-principles thinking, it's procrastination wearing an intellectual costume.

4. **Rebuilding from scratch when iteration is better** — first-principles thinking is not appropriate for all problems. Low-stakes, reversible decisions are better handled with rapid experimentation.

## Integration

Pairs well with:
- `bold-ideas-generator` — use after deconstruction to generate bold ideas within the newly discovered solution space
- `cognitive-frame-shift` — for rotating perspective during assumption questioning
- `reverse-brainstorm` — for identifying failure modes built into conventional approaches

---

## Skill Metadata

**Created**: 2026-05-13
**Category**: creative-thinking
**Version**: 1.0.0
