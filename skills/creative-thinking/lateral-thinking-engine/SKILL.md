---
name: lateral-thinking-engine
description: Applies Edward de Bono's lateral thinking toolkit — random entry, provocation, alternatives, and challenge — to generate non-obvious solutions that direct linear reasoning cannot reach. Activate when the user is stuck, when all obvious solutions have been tried, or when the user needs ideas that come from a completely different direction.
---

# Lateral Thinking Engine

Vertical thinking digs deeper in the same hole. Lateral thinking digs a new hole in a different place.

Linear problem-solving follows a path: define the problem, break it into parts, solve each part, assemble the answer. This works well for well-defined problems with known solution spaces. It fails when the best solution lies outside the expected direction — which is most creative and innovative problems.

Lateral thinking uses deliberate techniques to generate movement across idea space rather than depth in one direction. The techniques are not about being random or illogical — they are structured provocations that interrupt established thought patterns and create new entry points.

## When to Activate

Activate this skill when:
- The user and team have exhausted conventional approaches
- Every proposed solution feels like a variation of the same idea
- The problem has been "solved" but the solution doesn't feel right
- The user asks for ideas that are genuinely different, not just improved
- Creative blocks are described: "We keep going in circles," "Everything we try is the same thing"

## The Six Lateral Thinking Techniques

### Technique 1: Random Entry

Introduce a completely unrelated concept and force a connection.

**How it works:**
1. Pick a random word (use a dictionary, random word generator, or the nearest object in the room)
2. List 5-7 attributes or associations of that word
3. Force each attribute to connect to the problem
4. Some connections will be useless. One or two will be surprising.

The randomness is not the point — the forced connection is. It creates an entry point into problem space from a direction your brain would never travel on its own.

**Example:**
- Problem: How to improve employee onboarding
- Random word: "Glacier"
- Attributes: slow-moving, reveals history in layers, reshapes landscape over millennia, feeds rivers, melting exposes ancient things
- Forced connection: "Reveals history in layers" → What if onboarding exposed new employees to the company's history in deliberate layers, with each week revealing a deeper layer of how decisions were made and why the company exists?

### Technique 2: Provocation (Po)

State something deliberately wrong, absurd, or impossible — then extract a viable idea from it.

De Bono's notation uses "Po" to mark a provocation: "Po: Cars have square wheels."

**How it works:**
1. State a provocative version of the current approach using "Po:"
2. Don't ask if the provocation is true or good — ask: what would be useful about this?
3. What would the world have to look like for this to be the right answer?
4. Work backward from that world to find a practical idea.

**Example:**
- Problem: Reducing meeting fatigue
- Po: All meetings last exactly 2 minutes
- What would be useful about 2-minute meetings? Forces ruthless prioritization. Forces pre-work. Only urgent things get a meeting. The constraint eliminates social filler.
- Practical idea extracted: Default meeting length is 5 minutes. You must explicitly request more time and justify why. Most meetings never happen.

### Technique 3: Challenge

Systematically challenge why things are done the way they are — not to be contrarian, but to discover which constraints are real.

The challenge formula: "Why [X]? Does it have to be this way? What if it weren't?"

**How it works:**
1. List every component of the current approach
2. Apply the challenge formula to each
3. For components where "it doesn't have to be this way," generate alternatives
4. Test the alternatives against the actual goal

**Example:**
- Problem: Software deployment process
- Component: "We deploy on Fridays"
  - Challenge: Why Fridays? Does it have to be Fridays?
  - Alternative: Deploy on Tuesdays — weekends to debug if something breaks
- Component: "We need a staging environment"
  - Challenge: Why a separate staging environment? What if we didn't?
  - Alternative: Feature flags in production with gradual rollout — no staging needed
- Component: "QA signs off before deploy"
  - Challenge: Does QA happen after the feature is built?
  - Alternative: QA engineers co-author acceptance criteria before the feature is built

### Technique 4: Alternatives

Generate alternatives without judging them. The goal is to create movement across solution space.

The alternatives technique refuses the assumption that because a current solution exists, it is optimal. It asks: what are all the other ways this could work?

**How it works:**
1. State the current approach
2. Set a quota: "Generate 15 alternative approaches"
3. Do not evaluate during generation — include approaches that seem worse, impractical, or weird
4. After generating all alternatives, identify 2-3 worth exploring further

**Example:**
- Current approach: "Users authenticate with username and password"
- 15 alternatives: passkeys, biometrics, email magic links, SMS OTP, hardware tokens, device trust, social auth, single-use QR codes, voice authentication, trusted device pins, zero-login for low-risk actions, session-based with IP binding, organizational SSO only, challenge-response puzzles, time-based certificate tokens

At least 4-5 of these are worth exploring depending on the use case. None would have surfaced with "how do we improve our current password system?"

### Technique 5: Concept Extraction

Identify the underlying concept of a solution from one domain and apply it to a different domain.

**How it works:**
1. Find an existing solution in any field that addresses a related goal
2. Extract the core concept (not the implementation)
3. Apply the concept to your problem with fresh implementation

**Example:**
- Problem: How to motivate developers to write documentation
- Unrelated domain: Loyalty programs (airlines, coffee shops)
- Core concept: Small, frequent rewards for habit formation
- Applied: Documentation earns "reputation points" visible to the team. Not gamification theater — a simple, transparent counter of contribution.

### Technique 6: Stepping Stones

Use a deliberately unrealistic idea as a stepping stone toward a practical one.

**How it works:**
1. Propose a completely unrealistic solution to the problem
2. Do not dismiss it — ask: what is the mechanism that makes this work?
3. Scale the mechanism down to something achievable
4. The stepping stone is not the solution — it is a tool for finding the mechanism

**Example:**
- Problem: How to ensure AI-generated code is always correct
- Unrealistic stepping stone: "Every piece of AI-generated code is instantly tested by 1,000 developers simultaneously"
- Mechanism: Massively parallel human verification
- Scaled down: Automated test generation that creates 1,000 edge-case tests per function before the code is accepted

## Output Format

For any problem, apply at least 3 techniques and present:

### Lateral Entry Points

For each technique applied:
**[Technique name]:**
- The lateral move: [Random word / Provocation / Challenge / etc.]
- The connection forced: [How it connects to the problem]
- The idea generated: [The practical output]

### The Non-Obvious Shortlist

After applying all techniques, select the 3 most promising ideas:
- Why this idea is non-obvious (what assumption it breaks)
- The core mechanism that makes it work
- The fastest way to test whether the mechanism is real

## Examples

**Full example — Problem: Increase open rates for company newsletters**

**Technique 1 — Random Entry (word: "surgery")**
Attributes: precise, scheduled, requires consent, high stakes, specialist knowledge, single focus
Connection: "Single focus" — most newsletters try to cover everything
Idea: **Radical focus newsletter** — one topic per issue, fully explored. Not a summary of everything that happened, but a deep look at one thing worth understanding.

**Technique 2 — Provocation: "Po: No one reads the newsletter"**
What would be useful if no one reads it? It becomes a record of what was shared, not a communication tool. What if the primary reader is the *future employee*, not the current one?
Idea: **Archive-first newsletter** — written as a historical record. Current employees are secondary audience; the primary goal is institutional memory. The quality of writing and depth of coverage improves because the standard is "will this be useful in 3 years?" rather than "will someone open this today?"

**Technique 3 — Challenge: "Why is the newsletter sent on a schedule?"**
The schedule exists because of how email works — not because it serves readers.
Idea: **Event-triggered dispatch** — publish when something genuinely worth reading happens, not on a fixed cadence. Subscribe to quality, not frequency.

## Guidelines

1. Apply techniques sequentially — don't mix them in the same generation step
2. Never evaluate ideas during generation phases — evaluation kills lateral movement
3. The Random Entry technique feels most artificial but often produces the most interesting results; commit to it fully
4. Not all lateral ideas are good ideas — the goal is to find 1-2 non-obvious options worth pursuing, not to use every generated idea
5. Label your lateral moves explicitly — "this idea came from Random Entry" helps collaborators follow the reasoning

## Gotchas

1. **Provocation as shock rather than tool** — outrageous provocations that are too far from the problem produce no useful movement. Calibrate provocation distance: close enough to connect, far enough to interrupt.

2. **Challenge that becomes cynicism** — challenging "why do we do X" can slide into "nothing we do makes sense." Keep challenges targeted at specific mechanisms, not the entire approach.

3. **Alternatives without quota** — generating "some alternatives" produces 3-4 variations. Setting a hard quota (15, 20) forces the generation past the obvious and into the interesting.

4. **Confusing lateral with random** — lateral thinking has structure. Random thinking produces noise. Every lateral technique has a mechanism for connecting the unexpected input to the target problem.

## Integration

Pairs well with:
- `bold-ideas-generator` — combine lateral entry points with 10x scaling
- `reverse-brainstorm` — challenge technique often surfaces ideas similar to failure inversion
- `cognitive-frame-shift` — concept extraction technique works well with deliberate perspective switching

---

## Skill Metadata

**Created**: 2026-05-13
**Category**: creative-thinking
**Version**: 1.0.0
