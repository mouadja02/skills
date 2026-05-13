---
name: cognitive-frame-shift
description: Forces systematic perspective rotation by analyzing any problem through six radically different lenses — the child, the alien, the domain expert, the contrarian, the future self, and the user who hates you. Each lens surfaces assumptions and blind spots that single-perspective analysis misses entirely. Activate when a decision feels obvious and you want to stress-test it, or when diverse perspectives haven't been genuinely considered.
---

# Cognitive Frame Shift

Every analysis reflects the perspective of its author. A senior engineer analyzes a product decision through an engineering lens. A marketer frames the same decision in terms of messaging. A new user frames it in terms of confusion. All three are looking at the same thing and seeing different things — and all three are partially right.

Cognitive frame shifting is deliberate perspective rotation: the discipline of temporarily inhabiting a radically different worldview and fully analyzing the problem from inside that worldview. Not "what would a child say about this?" as a thought experiment — but genuinely adopting the constraints, assumptions, and goals of a child to generate analysis that you, as yourself, could not produce.

Each frame produces insights the others cannot. The goal is not to agree with all six frames but to extract what each uniquely reveals.

## When to Activate

Activate this skill when:
- A decision feels obvious and hasn't been questioned from multiple angles
- The team holds a strong consensus and no one has played devil's advocate
- The user suspects they have a blind spot but can't identify it
- The problem involves users or stakeholders whose perspective hasn't been genuinely considered
- A design, strategy, or plan has been built by specialists who may have lost sight of the outside view

## The Six Lenses

### Lens 1: The Child (Age 8-10)

**The worldview:** No assumed complexity. Brutal honesty. No social filter. No industry knowledge. Everything either makes sense or it doesn't.

**What this lens reveals:**
- Unnecessary complexity masquerading as sophistication
- Things that are confusing because they were never explained, not because they're inherently complex
- Social conventions that adults follow without questioning
- The difference between "complicated" and "important"

**Questions this lens asks:**
- "Why does it have to be that way?"
- "What is this actually for?"
- "This doesn't make sense. Explain it to me again."
- "Can you do it without all that?"

**How to inhabit this lens:**
Strip out all assumed context and industry knowledge. Explain everything from zero. If an explanation requires prior knowledge, ask: why does it require that? Could it be redesigned so it doesn't?

---

### Lens 2: The Alien (No Prior Human Context)

**The worldview:** Completely foreign to all human social, cultural, and organizational conventions. Intensely rational. No sunk cost bias. No emotional attachment. Observing human behavior as an anthropologist.

**What this lens reveals:**
- Conventions that exist for historical reasons that no longer apply
- Organizational behaviors that are objectively strange when described neutrally
- Problems that humans consider normal but are actually dysfunctional by any rational measure
- The gap between what organizations say they do and what they actually do

**Questions this lens asks:**
- "Why do these beings behave this way? What objective function are they optimizing?"
- "This seems like a self-imposed constraint with no external cause. Is that correct?"
- "These two goals are directly contradictory. How do they resolve this?"
- "Why do they repeat this pattern when it consistently produces a bad outcome?"

**How to inhabit this lens:**
Describe the current situation as if writing a field report for an alien anthropology journal. Use neutral, behavioral language. "Humans in this organization spend 40% of their working time in synchronous verbal communication events (meetings) that produce a document summarizing what was agreed (minutes), which most participants do not read."

---

### Lens 3: The Domain Expert (Deep Specialist, No Business Context)

**The worldview:** Knows more about the underlying technical, scientific, or domain-specific reality than anyone in the organization. Has seen this pattern solved elegantly and badly in many contexts. Has no political investment in the current approach.

**What this lens reveals:**
- Solutions that are technically suboptimal when viewed through the domain lens
- Known failure modes that the team isn't aware of
- Best practices from adjacent contexts that haven't been applied
- The gap between how the organization understands the problem and how domain science understands it

**Questions this lens asks:**
- "Where in the literature has this been studied?"
- "What's the established approach to this problem in [adjacent domain]?"
- "This appears to violate [domain principle]. Is there a reason for the exception?"
- "The team seems unaware of [X]. Has anyone considered it?"

**How to inhabit this lens:**
Identify the domain most relevant to the problem (psychology, systems engineering, economics, distributed systems, organizational behavior, etc.) and reason from that domain's first principles. Cite patterns and failure modes known in that domain.

---

### Lens 4: The Contrarian (Brilliant, Informed Skeptic)

**The worldview:** Has seen every fashionable idea fail. Skeptical of consensus. Seeks the mechanism behind the claim, not the claim itself. Not cynical — has seen enough to know when momentum substitutes for evidence.

**What this lens reveals:**
- Assumptions that are taken as fact because everyone agrees with them
- Plans that depend on things being true that haven't been verified
- Confidence that exceeds evidence
- The specific way this plan is most likely to fail

**Questions this lens asks:**
- "What would have to be false for this plan to succeed?"
- "Who said this works? What was the context? Does that context apply here?"
- "What is the mechanism by which this produces the desired outcome?"
- "What evidence would change your mind? Have you looked for it?"

**How to inhabit this lens:**
Do not argue for the opposite. The contrarian lens finds the weakest assumptions in the strongest argument. Identify the 3 most critical assumptions the plan depends on and ask what evidence supports each.

---

### Lens 5: The Future Self (10 Years From Now)

**The worldview:** Looking back at this decision with full knowledge of how it played out. Aware of which concerns were real and which were noise. Can see the second and third-order consequences that weren't visible at decision time.

**What this lens reveals:**
- Short-term thinking that sacrifices long-term value
- Decisions that will be seen as obviously wrong in hindsight
- The one consequence that will matter most (rarely the one getting the most attention now)
- The thing being optimized for that actually didn't matter

**Questions this lens asks:**
- "Will this still seem like a good decision in 10 years? Why or why not?"
- "What is the one thing we're trading away that we'll regret?"
- "Are we solving the problem that exists today or the problem that will exist tomorrow?"
- "What are we building that will be a liability in 5 years?"

**How to inhabit this lens:**
Write a retrospective from 2036. Describe what the organization did, what the outcome was, and what the team wishes they had known or done differently. Be specific about which assumptions were wrong and why.

---

### Lens 6: The Hostile User (Knows Your Product, Hates It)

**The worldview:** Has tried to use this product/system/plan and found it frustrating, confusing, or inadequate. Has formed strong opinions. Is not shy about expressing them. Is not wrong.

**What this lens reveals:**
- Pain points that the team has normalized or rationalized away
- The gap between the intended user experience and the actual user experience
- Features or processes that serve the creator's needs, not the user's needs
- The complaint that users have that the team dismisses as "user error"

**Questions this lens asks:**
- "Why does this require me to do [X]? That's clearly designed for your convenience, not mine."
- "I tried to do [Y] and couldn't. Why is that so hard?"
- "Your documentation assumes I already know how to use this."
- "I switched to [competitor] because of [specific reason]. You should know that."

**How to inhabit this lens:**
Write the 1-star review. Write the support ticket from hell. Write the frustrated Slack message to a colleague. Be specific — vague frustration reveals nothing; specific friction reveals the design failure.

## Output Format

For each problem analyzed:

### Frame Shift Report

**The Problem as Originally Stated:**
[Original framing]

---

**Lens 1 — The Child:**
*What they see:* [The specific confusion or unnecessary complexity this lens reveals]
*The question that surfaces:* [The question a child would ask that the team hasn't asked]
*What this changes:* [The insight or implication]

**Lens 2 — The Alien:**
*Field observation:* [Neutral behavioral description of the current approach]
*What is objectively strange:* [The behavior that makes no sense without context]
*What this changes:* [The assumption or convention now visible]

**Lens 3 — The Domain Expert:**
*Domain perspective:* [Which domain, and what it says about this problem]
*What the team doesn't know:* [The specific knowledge gap]
*What this changes:* [The recommendation from domain expertise]

**Lens 4 — The Contrarian:**
*The three load-bearing assumptions:*
1. [Assumption + evidence for/against]
2. [Assumption + evidence for/against]
3. [Assumption + evidence for/against]
*The most likely failure mode:* [How this plan fails]

**Lens 5 — The Future Self:**
*The retrospective:* [What the 2036 version of this looks like]
*The thing that actually mattered:* [Not what's getting attention now]
*The regret:* [What the future self wishes had been done differently]

**Lens 6 — The Hostile User:**
*The 1-star review:* [Specific, honest, harsh]
*The support ticket:* [What the frustrated user is trying to do and can't]
*The thing that made them switch:* [The competitor's advantage that isn't being addressed]

---

### Synthesis

**What was hidden from the original frame:**
List the 3-5 most important insights that would not have been visible from the original perspective.

**The one change with the highest leverage:**
Based on all six lenses, what single change would most improve the outcome?

## Examples

**Problem: Designing an onboarding flow for a B2B SaaS product**

**Lens 1 — The Child:**
"Why do I have to fill out 8 fields before I can try the product? I just want to see if it works."
Insight: The onboarding collects information for the company before delivering value to the user. The order is wrong.

**Lens 2 — The Alien:**
"These organisms are asked to invest 25 minutes of effort before they understand the value they will receive. Statistically, 70% abandon this process. The organization calls this a 'funnel' and measures the 30% who complete it. No one asks why the default is abandonment."
Insight: The abandonment rate has been normalized. The question should be why anyone tolerates the current onboarding, not how to optimize it at the margins.

**Lens 4 — The Contrarian:**
Critical assumption: "Users who complete onboarding are the right users."
Evidence: Completion correlates with persistence, not product-market fit. You may be selecting for people willing to tolerate friction, not people for whom the product solves a real problem.

**Lens 6 — The Hostile User:**
"I signed up, spent 25 minutes configuring things, and then couldn't figure out how to do the one thing I came here to do. Your documentation sent me to a feature that doesn't exist in my plan. I cancelled."
Insight: The onboarding and the plan-tier feature set are misaligned. The hostile user's complaint identifies a specific, fixable mismatch.

## Guidelines

1. Fully inhabit each lens before moving to the next — don't switch perspectives mid-analysis
2. The most uncomfortable lens is usually the most valuable — don't rush past it
3. Lens 4 (Contrarian) should be genuinely critical, not diplomatic skepticism
4. Lens 6 (Hostile User) must be specific — vague hostility produces no insight
5. The Synthesis step is where the real value is — the individual lenses are tools for reaching it

## Gotchas

1. **Performing perspectives instead of inhabiting them** — "the child would say this is confusing" without saying WHY it's confusing and WHAT specifically would un-confuse it is not using the lens, it's gesturing at it.

2. **Only using comfortable lenses** — teams naturally skip the lenses that challenge their assumptions (usually Contrarian and Hostile User). These are the most important ones.

3. **Treating all lenses equally** — some lenses will be more relevant to a given problem than others. Apply judgment about which lenses to go deepest on.

4. **Synthesis without commitment** — the Frame Shift produces insight; it doesn't make the decision. The output should include at least one specific, actionable change, not just a list of perspectives.

## Integration

Pairs well with:
- `first-principles-deconstruction` — use the Alien and Child lenses to surface assumptions, then deconstruct them
- `bold-ideas-generator` — use the Future Self lens to evaluate boldness; use the Hostile User lens to identify where bold ideas need to be hardened
- `reverse-brainstorm` — the Contrarian and Hostile User lenses are natural sources of failure modes for Phase 2

---

## Skill Metadata

**Created**: 2026-05-13
**Category**: creative-thinking
**Version**: 1.0.0
