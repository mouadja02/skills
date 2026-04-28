---
name: anass-pro-style
description: Build hyper-personalized, narrative-driven, single-file portfolio/pitch websites in the style of anass.pro. Use when the user asks for a "site like anass.pro", a one-recipient candidacy/pitch site, a behavioral-engineering landing page, a single-file storytelling portfolio with a pixel-art game hero, custom cursor, typewriter text, procedural Web Audio SFX, scroll-revealed scenes, or a dark purple narrative interface that addresses one named reader. Trigger on phrases like "personal pitch site", "one-page candidacy", "narrative portfolio", "scrollytelling pitch", "pixel-art hero", "interactive landing for X", or any request to recreate / clone / adapt anass.pro.
---

# Anass.pro-style narrative pitch sites

This skill captures the design system, interaction patterns, and authoring playbook behind [anass.pro](https://anass.pro) — a single-file, vanilla-JS, hyper-personalized pitch site that uses an interactive pixel-art game, procedural Web Audio SFX, scroll-revealed scenes and behavioral copywriting to address exactly one named reader.

Use it when the user wants to build something with the same DNA: a one-recipient narrative landing page that *feels designed for them and only them*.

## What you are recreating

Anass.pro is not a generic portfolio. It is a behavioral pitch built around four ideas:

1. **One reader, one URL.** The site is addressed to a specific named person. Their name appears in the HUD, in narrative cards, and inside the storytelling. No one else receives this URL.
2. **Story as architecture.** The page is a sequence of *scenes* (Hero → Hook → Mirror → Method → Reveal → Person → Close). Each scene has a psychological job — capture, rupture, reappraisal — not just "section + content".
3. **The medium is the message.** The interactive pixel-art game in the hero is itself the proof of capability. A typewriter with key clicks, a counter that ticks up to 8.6M, a character that follows the user across scenes — every effect demonstrates the engineering claim the copy is making.
4. **Single-file, no framework.** The whole thing ships as one ~120 KB HTML file with inline `<style>` and `<script>`, vanilla JS classes, a Canvas 2D engine, and Web Audio API for procedural sound. No build, no React, no audio assets.

If the user wants a generic personal portfolio, **stop and switch to `frontend-design`**. Use this skill only when the brief is a one-recipient pitch / candidacy / narrative landing page.

## Workflow when invoked

```
Task progress:
- [ ] 1. Confirm fit: is there ONE specific named recipient and a story to tell about them?
- [ ] 2. Gather inputs: recipient name + role, sender pitch, 2-4 specific facts about the recipient, the "ask" (CTA target), assets (logos), language/tone
- [ ] 3. Pick a scene sequence (use the 7-scene default, or adapt)
- [ ] 4. Lock the design tokens (see references/design-tokens.md) — pick palette + 4 fonts
- [ ] 5. Scaffold the single HTML file from templates/starter.html
- [ ] 6. Implement scenes top-to-bottom using references/section-recipes.md
- [ ] 7. Wire the signature interactions (references/animation-patterns.md)
- [ ] 8. Add procedural Web Audio SFX if appropriate (references/web-audio-sfx.md)
- [ ] 9. Add the pixel-art canvas hero if appropriate (references/pixel-game-canvas.md)
- [ ] 10. Verify reduced-motion + mobile breakpoints + a11y
```

Stop after step 2 and confirm the brief with the user before scaffolding. The whole point of the format is that it knows the reader; if you don't have specifics about the reader, the site collapses into another generic template.

## Step 1 — Confirm fit

Ask the user (briefly, one round of questions only):

- **Who is the one reader?** Name, role, company. The site addresses them by name.
- **What do they already do well?** 1-3 specific facts. The "Mirror" scene reflects these back. ("You ran a 500-wallet stunt at GITEX" works; "you do marketing" does not.)
- **What is the sender pitching?** A role, a partnership, a service. One thing.
- **What is the CTA target?** Usually a LinkedIn URL, an email, or a Calendly. Single button at the end.
- **Language + tone?** Anass.pro is French, intimate `tu`. Match the recipient's culture. Default to confrontational + complicit, not corporate.
- **Assets?** Brand logo, photo, illustrations. Optional — the site can run on pure CSS/canvas if needed.

If the user can't answer the "Who is the one reader?" or "What do they already do well?" questions concretely, **don't build this**. Push back: "this format only works when we can name specific things the reader has done. Otherwise it reads as fake intimacy. Want me to switch to a regular portfolio instead?"

## Step 2 — Default scene sequence (the seven-scene narrative)

Use this exact sequence unless the user has a strong reason to deviate. Each scene has a CSS hook, a `data-s` index for the dot-nav, and a psychological job.

| # | Section id | Title pattern | Job | Required elements |
|---|---|---|---|---|
| 0 | `#game-hero` | (no heading — the hero IS a game) | Capture: trigger pattern-recognition in the first 3 seconds | Pixel-art canvas, HUD with recipient's name, intro speech card, persistent CTA pill |
| 1 | `#s-hook` | "You did X. I do Y. Same principle." | Hook: state the analogy between the reader's work and the site itself | Brand bar, 3 typewritten lines, animated counter, italic aside |
| 2 | `#s1` (Mirror) | "You used 500 X. I use one." | Mirror: prove you understand them by tabulating their move next to yours | 2-column compare table with row labels |
| 3 | `#s2` (Method) | A quote from the recipient | Method: 3 expandable steps explaining the psychology of what just happened | 3-card flex-grow row, big italic ordinal numbers, closing line |
| 4 | `#s3` (Reveal) | "What you just lived through is X." | Reveal: name the technique. Italic gradient title. | Centered, watermark logo glowing behind, body + pull quote |
| 5 | `#s4` (Person) | "A. R." (sender) | Person: brief identity + stats + project grid | 2-col grid: stats left, bio + chips + project tiles right |
| 6 | `#s5` (Close) | "Now you know what I do when I want something." | Close: the ask. One gradient CTA. Italic Fraunces sign-off. | Big condensed headline, body, single magnetic CTA, small meta line, italic sig |

The user is allowed to skip Mirror or Method, but **never skip Hero, Reveal, or Close** — they carry the format's identity.

## Step 3 — Lock the design tokens

Open `references/design-tokens.md` and pick (or accept the defaults):

- **Palette** — anass.pro defaults to dark midnight + electric purple + soft cyan. The reference file lists 5 alternative palettes that preserve the architecture.
- **Type system** — 4 fonts, one role each:
  - Display (condensed bold) → section titles, hooks
  - Body (humanist sans) → paragraphs, italic asides
  - Mono (technical) → labels, kickers, chips, codes
  - Italic display serif → emotional moments, quotes, sign-offs
  - Defaults: Barlow / Barlow Condensed / JetBrains Mono / Fraunces. Don't substitute Inter — it kills the voice.
- **Cursor mode** — desktop default is `cursor:none` + custom dot+ring follower. Touch devices fall back to native cursor.

Inject all tokens as `:root` CSS variables. Reference: `references/design-tokens.md`.

## Step 4 — Scaffold the file

Start from `templates/starter.html`. It contains:

- The exact `:root` design tokens
- All seven scene wrappers with correct ids and `data-s` indices
- Custom cursor + progress bar + dot nav + sound toggle + next-cue + back-top elements pre-wired
- A minimal `GameEngine` stub, a `Typer` class, the `Splitter`, the `IntersectionObserver` reveal, and the magnetic-CTA loop
- Reduced-motion media query
- Mobile breakpoints

Copy it, then rename ids/classes only if you have a strong reason. The class names (`.scene`, `.rv`, `.sw`, `.grad`, `.pu`, `.cs-arr`) are referenced from multiple scripts and CSS rules — keep them.

## Step 5 — Implement scenes

For each scene, follow the recipe in `references/section-recipes.md`. The reference file gives you, per scene:

- The HTML skeleton (copy-paste)
- Required CSS (already in starter.html)
- Animation hooks (which classes to add: `.rv`, `.rv.split`, `.d1`/`.d2`/`.d3` stagger, etc.)
- Copy structure (kicker → title → sub → body → CTA), with the rationale for each

Two non-negotiables across all scenes:

1. **Use `<span class="pu">…</span>` to highlight key purple words** (the recipient's words, the specific numbers, the verbs of action).
2. **Use `<span class="grad">…</span>` to gradient-clip the most emotional phrase per scene** — never more than one per scene. Overuse kills it.

## Step 6 — Wire the signature interactions

These six interactions *are* the format. Skip them and you have a dark purple landing page; include them and you have an anass.pro-style site. Implement in this order, each is independent:

1. **Custom cursor** (dot + ring with smooth follow, scale-up on links). Skip on touch.
2. **Scroll progress bar** at the top, gradient-filled.
3. **Right-side dot navigation**, IntersectionObserver-driven, click to scroll.
4. **Scroll reveal** — `.rv` class fades up when in view; `.rv.split` splits text into per-word spans with `--i` index for staggered fade.
5. **Typewriter** with character-by-character reveal and per-keystroke audio click. Punctuation pauses (commas → +90ms, periods → +160ms).
6. **Magnetic CTA** — desktop only, the CTA gently follows the cursor when within 160px.

Optional but high-impact:

7. **Persistent character buddy** — a pixel sprite that jumps with a parabolic arc to the currently-visible section.
8. **Animated counter** that ticks up with audio clicks every N units, then a final "ding".

All recipes in `references/animation-patterns.md`.

## Step 7 — Procedural Web Audio SFX

The site has zero audio files. Every sound is synthesized at runtime via `AudioContext`. This is fundamental to the "all-craft" feeling. Read `references/web-audio-sfx.md` for ready-to-paste recipes for:

- `key` (typewriter click + thud) — fires on every typed character
- `click` (UI confirmation)
- `ding` (counter completion)
- `tick` (counter pulse)
- `cta` (CTA hover/click)
- `spell` (game projectile)
- `explosion` (game boss death — noise + lowpass sweep)
- `monster` (boss arrival — 4-layer: thud + sawtooth drone + tension sine + whoosh)
- `jumpLand` (character lands after a jump arc)

Wrap them in a single `SFX` module with a global mute toggle, persisted to `localStorage`. Default to **muted-but-armed**: the toggle reads "Activer les sons" on first load — never autoplay.

## Step 8 — Pixel-art canvas hero (optional, recommended)

The hero is the format's signature. If the project has time/budget, implement it. Reference: `references/pixel-game-canvas.md`. Key architecture:

- Single `<canvas id="game-canvas">` filling the viewport
- A `GameEngine` class with `update(now)` / `render()` running on `requestAnimationFrame`
- 3 parallax building layers + animated stars + procedural ground/road
- Procedurally-drawn 8-frame walking sprite (no sprite sheet — pure `ctx.fillRect`)
- Phase machine: `0=walk-in` → `1/2/3=boss fights` → `4=victory walk` → `7=final reveal`
- Speech-bubble "intro card" + a side stack of past dialogue cards
- Bezier-curve pointer arrows from card to character

If the project is constrained, **replace the game with a static animated illustration** (canvas star field + parallax buildings, no characters/bosses). The narrative still works.

## Step 9 — Accessibility, performance, mobile

Non-negotiable checks before shipping:

- `@media (prefers-reduced-motion: reduce)` collapses all transitions/animations to 0.01ms
- Native cursor on touch (`@media (hover:none)` or `width <= 768px`)
- All interactive game/SFX elements are duplicated as visible HTML so screen readers see the content
- Live region (`<div aria-live="polite">`) announces phase transitions if you implement the game
- All images have `alt`; decorative images use `aria-hidden="true"` and empty alt
- The CTA is a real `<a href="…">`, not a div
- Mobile: dot nav, custom cursor, magnetic CTA all disabled. Game scales sprites to 0.65×.
- The single HTML file should stay under 200 KB. Inline SVG noise; don't link to image files unless necessary.

## Common mistakes to avoid

| Trap | Fix |
|---|---|
| Generic copy ("I'm a passionate developer") | Quote the recipient. Reference their specific work. Use `tu`/intimate form. |
| Inter / Roboto / system fonts | Use the Barlow + Fraunces stack. Distinctive type carries the voice. |
| Gradient on every heading | Exactly one `.grad` per scene. The rest is `.pu` (purple ink) for emphasis. |
| Audio on autoplay | Default muted. Toggle is opt-in. |
| Heavy build pipeline | Single HTML file. No bundler. The constraint is the point. |
| Multiple CTAs | One CTA in the Close. The Hero CTA only appears after the user scrolls back to the top after reading. |
| Overdone parallax | 3 building layers max. More noise, less signal. |
| Skipping the Reveal scene | The Reveal is what reframes the whole experience as engineering. Without it the site reads as gimmick. |

## Reference files (read on demand)

- `references/design-tokens.md` — Colors, type system, spacing scale, alternative palettes
- `references/section-recipes.md` — HTML/CSS skeletons for each of the 7 scenes
- `references/animation-patterns.md` — Cursor, reveal, typewriter, magnetic CTA, character buddy, counter
- `references/web-audio-sfx.md` — Procedural sound recipes (copy-paste functions)
- `references/pixel-game-canvas.md` — Game engine architecture, sprite drawing, parallax, bosses
- `references/copywriting-playbook.md` — Voice, tone, structure formulas for each scene's text
- `templates/starter.html` — A complete, working scaffold to copy from

Read each reference file only when you reach the corresponding step. They're all under 400 lines so a single read is cheap.

## When NOT to use this skill

- Generic personal portfolio (broad audience) → use `frontend-design` instead
- Marketing landing page for a SaaS → use `ui-ux-pro-max` or `slides`
- Multi-page site with navigation → wrong format; this skill is for one scrollable page addressed to one reader
- Light/airy / corporate brand → wrong palette; this format is dark, intense, and confrontational
- The user can't name the recipient or specific facts about them → push back, don't fake intimacy
