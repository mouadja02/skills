# Copywriting playbook

The visual format is replicable. The copy is what makes it land. This document is the most important reference in the skill — get the tokens and animations right but the copy generic, and the site fails. Get the tokens slightly wrong but the copy precisely targeted, and it still works.

## Voice principles

1. **One reader, address them directly.** Use second-person singular intimate (`tu` in French, `you` in English, equivalent in other languages). Never plural "you all".
2. **Quote the recipient.** At least once per page, render an exact phrase the recipient has said in public. The Method scene's blockquote and the Hook scene's typewriter are the natural homes.
3. **Reference their specific work.** Numbers, project names, dates. "500 wallets at GITEX Africa 2026" beats "your impressive marketing campaigns" by a factor of ten.
4. **Confrontational + complicit, not corporate.** "You did X." vs "I noticed your impressive achievement of X". The first is a peer talking; the second is an applicant grovelling.
5. **Asymmetry of stakes.** The reader has the leverage (they're being pursued); the sender is being honest about that. "You don't need me. But you might want me." reads as power. "I would be honored to work with you." reads as desperation.
6. **Behavioral psychology vocabulary, used sparingly.** Words like *capture*, *rupture*, *reappraisal*, *primitive*, *pattern recognition* signal expertise but only if used once each, not stacked.
7. **Numbers > adjectives.** "10 years" not "experienced". "0 generic applications" not "highly selective".

## Per-scene copy formulas

### Scene 0 — Hero HUD

Two pieces of copy in the HUD:

| Element | Formula | Example |
|---|---|---|
| Brand bar | `BRAND <strong>NAME</strong>` (split on the second word) | `MEGASUSS <strong>TECH</strong>` |
| Tag line | `For [Recipient Name] — [Their Specific Role]` | `For Karim Sahraoui — Founder` |

Plus a sub-tagline that appears at the end of the hero sequence:

```
[Two-word professional descriptor] · [Two-word skill] · [Two-word skill]
The one who [does the thing the recipient cannot delegate easily].
```

Example: `Software Engineer · Automation · Web Development` / `The one who opens the doors that code alone cannot close.`

The "one who…" phrase should be slightly poetic, not corporate. It's the sender's *position* in the recipient's narrative, not their job title.

### Scene 1 — Hook

Three typewritten lines + a counter + an italic aside.

**Three lines, formula:**

1. `You did [SPECIFIC FACT WITH NUMBER].`
   Highlight the number with `<span class="pu">`. The fact must be public, verifiable, and the recipient must be proud of it.

2. `I do [SCALED-DOWN ANALOGOUS THING] — for you alone.`
   Highlight the scaled thing. The "you alone" is the load-bearing phrase.

3. `The principles are <span class="pu">exactly</span> the same.`
   This is fixed. The word "exactly" carries the claim. Don't soften to "very similar" or "comparable".

**Counter:** A number from the recipient's own work — their views, their revenue, their followers. The counter labels itself in three short lines that justify the metric:

```
views generated
by one well-executed
idea
```

Or, depending on the metric:

```
followers reached
in twelve months
without a single ad
```

Mark the metric in a `var(--lg)` size with all-caps, gradient-clipped numbers.

**Aside:** A one-sentence italic Fraunces line that *credits* the recipient without flattering. The structure:

```
[Personal reaction]. <em>[Implication that scales beyond me]</em>.
```

Example: `It impressed me. <em>And I wasn't the only one.</em>`

### Scene 2 — Mirror

A 2-column compare table. Three rows. Each row has a category label (mono, uppercase) and a one-sentence body.

**Required row categories:**

1. **Capture** — what initially grabs attention
2. **Differentiation / Uniqueness** — why this isn't generic
3. **Conversion** — what action it produces

**Cell formula (per cell):**

```
[CATEGORY LABEL]
[Concrete description, 12-25 words]. [Mechanism in one phrase].
```

Example:

| Their move | My move |
|---|---|
| **VISUAL CAPTURE** — A bill sticking out of the wallet. Impossible to ignore. The reptile brain takes over. | **COGNITIVE CAPTURE** — A game where you play your own story. The founder brain detects: *someone gets me*. |

Left column is italic and dimmer (`color: var(--ink2)`). Right column is purple-highlight (`color: var(--purhi)`). The italic-vs-upright contrast reinforces the "your move (then) → my move (now)" reading.

### Scene 3 — Method

A blockquote (the recipient's words) + 3 expandable steps + a closer.

**Blockquote:** A direct quote from the recipient, attributed. Find one in their public talks, posts, or interviews. The Fraunces italic carries the gravity.

**Three steps:** Each is a moment in the user's *neurological* journey. Use exact time markers.

| Step | Time marker | Title pattern | Body sentence |
|---|---|---|---|
| 01 | `Second 0–3` | Two-word noun phrase: `Primitive Capture`, `Pattern Break`, `Hook` | What just happened in their brain in seconds 0–3 |
| 02 | `Second 3–60` | Two-word noun phrase: `Cognitive Rupture`, `Predictive Break` | The expectation violation |
| 03 | `Now` | Two-word noun phrase: `Positive Reappraisal`, `Curiosity Loop` | The reframing the reader is doing right now |

The body sentences each highlight one technical phrase in `<em>` (rendered as `--purhi` italic, not gradient). Pick verbs from neuroscience: *fired*, *triggered*, *lit up*, *re-evaluated*.

**Closer (`.mclose`):** One paragraph that contrasts the format with the default behavior. Formula:

```
This isn't the same as [GENERIC ACT]. [SHORT JUDGMENT — they don't get it]. <strong>I do — and I know how to build it.</strong>
```

The closing strong tag is the only place a non-italic, non-uppercase emphasis appears in the scene. It hits.

### Scene 4 — Reveal

Centered. Three pieces of copy:

**1. The label** (mono, small): `The Reveal`, `Behind the Curtain`, or culture-appropriate equivalent.

**2. The headline:**

```
What you just experienced is <span class="grad">[NAME OF THE TECHNIQUE].</span>
```

The technique name is the gradient-clipped phrase. Examples: *behavioral engineering*, *attention architecture*, *applied neuromarketing*. Whichever fits the reader's vocabulary.

**3. The body:** A one-paragraph denial of magic + reaffirmation of method.

```
No magic. No accident. A precise architecture. Every detail — [LIST 3 SPECIFIC SITE ELEMENTS] — was designed to produce a measurable neurological effect. Exactly like your [RECIPIENT'S WORK].
```

The list of 3 specific site elements is what proves you actually built it. Examples: "the game, the doors, the anonymous character" / "the typewriter, the counter, the silent character". Pick three the reader has just seen.

**4. The pull-quote:** Italic, single sentence, attribution-less. A statement of professional faith.

Examples:
- "When theory and data converge, the debate is over."
- "Form follows function follows feeling."
- "Engineering is the discipline of caring about details until they become invisible."

This quote carries the sender's professional creed. It's the most important sentence on the page.

### Scene 5 — Person

Two columns: identity + bio.

**Identity column:**

| Element | Formula | Example |
|---|---|---|
| Name | Initials only — `A. R.` (or full first name + last initial) | `A. R.` |
| Role | Two-line italic: `[DAY ROLE].\n[NIGHT ROLE].` | `QA Engineer by day.\nBuilder by night.` |
| 4 stats, formula `[NUMBER][SUFFIX] · [LABEL]` | See below | |

The four stat slots:

1. **Years of experience** — `10+` / `Years of software experience`
2. **Geographic / cultural breadth** — `2×` / `Countries — Morocco, France`
3. **Distinctive achievement** — `1×` / `AI Hackathon — 1st prize`
4. **Provocative zero** — `0` / `Generic applications sent`

The fourth is the format-defining stat. It signals self-awareness about the medium itself.

**Bio column:**

```
[RECIPIENT'S NAME], you proved that your ideas work. [SPECIFIC ACHIEVEMENT — REVENUE OR REACH]. [SOCIAL PROOF — CLIENTS / PARTNERS]. Now you need to build.

I'm a [PROFESSION] with [N] years of experience. I [VERB] what [PROBLEM]. I [VERB] what [OUTCOME]. And I understand the impact of every line on the human experience.

<strong>I'm not looking for a job. I'm looking for a partnership — the kind that turns your ideas into products that last.</strong>
```

The closing strong sentence is the format's *positioning statement*. It's not asking; it's reframing the relationship.

**Skill chips:** 8-12 mono-uppercase chips. Mix concrete tech (`TypeScript`, `Python`, `React/Next.js`), capabilities (`Quality Assurance`, `Automation`, `AI Workflows`), and tools (`Claude Code`, `CI/CD`, `GraphQL`). No SEO-keyword spam — this isn't a resume; it's a vocabulary signal.

**Project tiles:** Three groups, each with a `.blabel` heading:

1. **Built end-to-end** — sender's solo projects (with external links)
2. **Contributed to** — projects with bigger orgs (with external links)
3. **Side / nerdy** — hackathons, CLIs, quirky tools (no external link if not public)

Each tile is `<a class="bi">` with `[CATEGORY] / [PROJECT NAME — DESCRIPTION]`. Category is short uppercase (`E-COMMERCE`, `GOVERNMENT`, `OPEN SOURCE`).

### Scene 6 — Close

Five pieces of copy. Spend time on this scene; it's the last impression.

**1. Kicker:** `The Close`, or culture-equivalent.

**2. Headline:**

```
Now you know what I do<br>when I want <span class="grad">[NOUN].</span>
```

The gradient noun is *something*, *to win*, *what matters*. One word. Gravitas comes from brevity.

**3. Body:**

```
You have the [LIST 3 ASSETS]. The [MISSING PIECE] is what's missing. I build what you can't delegate to just anyone — and I do it with the same precision you put into your campaigns.
```

The "same precision as your X" is the thread that runs from scene 1 to here. Don't drop it.

**4. CTA copy:** A single button. The label is a *promise of revelation*, not a job-application verb.

| ✅ Good | ❌ Bad |
|---|---|
| `Find out who I am` | `Apply Now` |
| `Open the door` | `Send my CV` |
| `Continue the conversation` | `Get in touch` |
| `Let's talk` | `Submit` |

**5. Sign-off (`.csig`):** Italic Fraunces, two lines, line break exactly here:

```
This site was<br>
<span>designed only for you.</span>
```

The line break makes it feel handwritten. The second line in `--purhi` color is the closing flourish.

## Cultural / language adaptation

Anass.pro is in French with intimate `tu`. When adapting:

- **English:** use *you* (singular). The intimacy must come from specificity, since English doesn't have a tu/vous distinction.
- **Spanish:** use *tú* (Spain) or *vos* (Argentina/Uruguay) — match the recipient's region. Never *usted*.
- **German:** use *du*. The sender already implies familiarity by sending an unsolicited site.
- **Arabic:** use second-person masculine/feminine matching the recipient's gender, RTL layout — flip the right-side dot nav to the left, mirror the magnetic CTA logic.
- **Mandarin / Japanese:** the format becomes harder. Both languages discourage second-person address with strangers. Replace `你/あなた` with the recipient's name + role each time. The intimacy is then carried by repetition, not pronoun.

When in doubt, ask the user: "What's the most intimate-yet-respectful form of address for [recipient] in [their language]?"

## Anti-formula traps

These are copy moves that read as fake-intimate. Avoid:

- "I've been following your work for years." (Even if true, sounds creepy.)
- "Your story really resonated with me." (Generic; quotable from any LinkedIn outreach.)
- "I think we'd make a great team." (Asks for what hasn't been earned yet.)
- Multiple uses of the recipient's first name in succession. (Once per scene is enough.)
- Adjective stacking: "innovative, impressive, groundbreaking work". (Use one specific noun instead.)
- Future-tense promises: "I would build…" / "I could create…". The format has *already* built; use past or present tense for proof.

## Final read-through checklist

Before shipping, read the page out loud as if you were the recipient:

- [ ] Does my name/role appear in scene 0?
- [ ] Is there at least one specific number from my work in scene 1?
- [ ] Is there a verbatim quote of mine somewhere on the page?
- [ ] Does the Method scene describe what *I* just experienced (not generic neuroscience)?
- [ ] Is the gradient phrase per scene the most important phrase of that scene?
- [ ] Does the CTA copy promise revelation, not application?
- [ ] Could the same copy be sent to anyone else? (If yes — rewrite.)
