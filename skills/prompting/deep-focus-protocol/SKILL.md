---
name: deep-focus-protocol
description: Structures work sessions for peak cognitive performance on hard problems. Defines scope ruthlessly, eliminates scope creep, batches cognitive modes, and builds momentum through deliberate sequencing. Activate when the user needs to do deep creative or intellectual work and wants to protect their best thinking time from fragmentation.
---

# Deep Focus Protocol

Creativity and complex thinking require a cognitive state that most work environments systematically destroy. Shallow work — email, meetings, quick tasks, context-switching — is not less work. It actively prevents the brain from entering the depth state where novel ideas and hard problems yield.

Deep focus is not about working longer. It is about creating conditions where your best thinking can happen and protecting those conditions from degradation.

## When to Activate

Activate this skill when:
- The user needs to do complex, creative, or intellectually demanding work
- The user is starting a deep work session and wants to structure it
- The current approach keeps getting interrupted or derailed
- The user wants to maximize the quality of a single session
- The task requires sustained concentration (design, writing, architecture, difficult analysis)

## The Deep Focus Framework

### Phase 1: Session Design (10 minutes before starting)

Before the session begins, define three things exactly:

**1. The One Output**
What single, concrete artifact will this session produce? Not "work on X" — that's a process, not an output.

Bad: "Work on the authentication system"
Good: "Write the complete specification for the session management system, including all edge cases for token expiration and refresh"

The output must be specific enough that you can tell, unambiguously, at the end of the session whether you produced it.

**2. The Scope Wall**
Define explicitly what is OUT of scope for this session. This is as important as defining what's in scope. Scope creep during deep work is the primary cause of sessions that feel unproductive — you end with a lot of partial work and no completed output.

Write: "I will NOT touch [X], [Y], [Z] during this session, even if I notice problems there."

**3. The Session Length**
Pick a duration based on the output complexity:
- 45-minute session: Single well-defined deliverable
- 90-minute session: Two connected deliverables or one complex one
- 2x 90-minute sessions with a break: Full creative sprint (maximum recommended single day)

Do not work longer than 90 minutes continuously. Cognitive quality, not quantity, is the goal.

### Phase 2: Environment Configuration

Before starting the timer, configure the environment:

**Cognitive environment:**
- Close everything not needed for this specific output
- Open only the files, tools, and references directly needed
- If the task requires research, do that research BEFORE starting — mid-session research breaks are depth disruptors
- Have the output document/file ready to receive work before starting

**Interruption environment:**
- Notifications off for the session duration
- Set a status indicating unavailability
- Pre-answer or defer any likely interruptions (check Slack/email briefly, clear urgent items, then close it)

**Attention anchor:**
Write, in one sentence, the output you're working toward. Keep it visible. When you drift, use this to return.

### Phase 3: The Session Structure

**Minutes 0-5: Warm-up ramp**
Do not start with the hardest part. Begin with a small, related, easy task that engages the cognitive domain:
- Review the last relevant document
- Write a 3-sentence summary of where you are
- Sketch an outline or diagram

The warm-up is not wasted time. It recruits the relevant cognitive networks before applying them to the hard problem.

**Minutes 5-70 (for 90-min session): Deep work block**
Work on the defined output. The only permitted interruptions:
- Noting a scope item to address in a future session (write it, don't act on it)
- A genuine emergency that cannot wait 20 minutes

When distracted:
1. Notice the distraction
2. Write it down if it's a task thought ("I need to check that email" → write it in a capture list)
3. Return to the attention anchor
4. Resume

**Minutes 70-80: Integration**
Slow down deliberate production. Begin integrating and reviewing what was created:
- Does the output meet the specification defined in Phase 1?
- What's incomplete?
- What, if anything, changed the scope or revealed new requirements?

**Minutes 80-90: Shutdown**
A deliberate shutdown ritual signals to the brain that the deep work session is complete:
- Write the "next session" setup: what would you do in the first 5 minutes of the next session?
- Capture all loose thoughts and scope items from the session
- Note the state of the output: what's done, what's partial, what's remaining

The shutdown ritual is not optional. It allows the unconscious to continue processing after the session ends — the insight that arrives in the shower often comes because the shutdown ritual handed off the problem properly.

### Phase 4: Recovery

Deep work is cognitively expensive. It requires recovery:

**Between sessions (same day):**
- Minimum 20-minute break with no screen
- Physical movement is optimal
- Do not fill this break with shallow work — it interrupts recovery

**After a full deep work day:**
- Shallow work only for the remaining hours
- No second deep work session on the same problem same day
- Sleep is the most important recovery mechanism — the session's output consolidates during sleep

## Cognitive Mode Batching

The biggest productivity killer is mixing cognitive modes within a session. Different types of thinking compete for the same neural resources:

| Mode | Cognitive Resource | Incompatible With |
|---|---|---|
| Deep creation | Sustained attention, working memory | Evaluation, communication |
| Critical evaluation | Analytical focus | Generation, exploration |
| Communication | Social cognition | Deep analysis |
| Exploration/research | Associative thinking | Precision work |
| Administrative | Low cognitive load | High cognitive load |

**Rule:** A deep focus session should operate in one cognitive mode. Pick before starting.

If the task requires both generation and evaluation (e.g., writing that must be high-quality from the start), use alternating micro-blocks: 20 minutes generation, 10 minutes evaluation, repeat. Do not mix them sentence-by-sentence.

## The Momentum Principle

Momentum in deep work is real: cognitive state accumulates over the first 20-30 minutes of a session and reaches its highest quality around minutes 40-60. This means:

1. **Interruptions at minute 25 are more expensive than interruptions at minute 5.** You lose more accumulated state.
2. **The first session of the day is the most valuable.** Protect it. Do not let it be consumed by email.
3. **Incomplete work degrades momentum.** Finish one output before starting another. Partial outputs leave cognitive residue that competes with the next task.

The best way to maintain momentum across multiple sessions:
- End each session with the shutdown ritual
- Start each session with a 5-minute review of the previous session's output
- Never start a new output in the same session as completing one

## Output Format

When helping a user design a deep focus session, produce:

### Session Plan

**Session goal:** [The single, specific output]

**Scope wall:**
- In: [Exactly what is included]
- Out: [Explicitly excluded]

**Duration:** [45 / 90 minutes]

**Warm-up task:** [The 5-minute ramp-in activity]

**Environment setup:**
- [ ] Open: [specific files/tools]
- [ ] Close: [specific applications]
- [ ] Notifications: off
- [ ] Status: set to unavailable

**Attention anchor sentence:** [One sentence to return to when drifting]

**Shutdown checklist:**
- [ ] Output assessment: done / partial / blocked
- [ ] Next session setup: [first 5 minutes of next session]
- [ ] Capture list cleared

## Examples

**User:** "I need to write the technical specification for the API rate-limiting system. I keep getting distracted."

**Session Plan:**

**Session goal:** Complete first draft of the rate-limiting specification: endpoints affected, rate limit tiers, algorithm choice (token bucket vs. leaky bucket), response format for 429s, and header specification.

**Scope wall:**
- In: Rate limiting spec for the public API
- Out: Internal admin API rate limits, authentication changes, caching strategy, anything in the Jira backlog that "would be good to add while we're in this area"

**Duration:** 90 minutes

**Warm-up task:** Re-read the last PR that added the current (inadequate) rate limiting and write a 3-sentence summary of what it does and why it's not enough.

**Attention anchor:** "The output is a spec someone else could implement without asking me a single question."

**Shutdown:** Write the three open questions that remain after the spec, rank-ordered by how much they'd change the design.

---

**User:** "I need to design the architecture for a new feature but every time I sit down to think about it I end up doing other things."

**Session Plan:**

**Session goal:** Produce a C4 Context diagram and a bulleted list of 5-7 key architectural decisions (not just components — actual decisions with trade-offs noted).

**Scope wall:**
- In: Architecture for this feature only
- Out: Refactoring existing code, related features, the "while we're at it" cleanup list

**Warm-up task:** Draw a rough sketch of the current system state without referring to any documentation — just from memory. Note what feels uncertain.

**Attention anchor:** "Architectural decisions, not component inventory."

## Guidelines

1. One output per session — not one topic, one deliverable
2. The scope wall is as important as the scope — write it before starting, not as a reminder when you drift
3. The shutdown ritual is not optional — it's what makes the next session productive
4. Deep work requires recovery — protect the recovery as much as the session
5. Schedule deep work for your peak cognitive hours — most people have 2-4 peak hours per day; never fill them with email

## Gotchas

1. **Confusing busyness with depth** — a day filled with shallow tasks feels productive but produces no deep output. Measure sessions by output produced, not time spent.

2. **Treating the warm-up as optional** — skipping straight to the hard work causes the first 20 minutes to be inefficient anyway. The warm-up routes the cognitive investment better.

3. **Planning without protecting** — scheduling a deep work session and then allowing interruptions produces the worst outcome: you've allocated the time but haven't produced the output. Protect the session or reschedule it.

4. **Deep work on the wrong output** — spending 90 minutes in deep focus on something low-leverage is still low-leverage. Deep focus amplifies output quality; it doesn't change output importance.

## Integration

Pairs well with:
- `bold-ideas-generator` — design a deep focus session specifically for bold ideation
- `idea-velocity` — use a 45-minute deep focus session for Phase 1 generation
- `cognitive-frame-shift` — run a 90-minute deep focus session to fully apply all six lenses to a high-stakes decision

---

## Skill Metadata

**Created**: 2026-05-13
**Category**: creative-thinking
**Version**: 1.0.0
