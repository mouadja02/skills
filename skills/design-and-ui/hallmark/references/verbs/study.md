# `hallmark study`

Moved verbatim from SKILL.md so the entry file stays small, next to `audit.md` and `redesign.md`. Links of the form `references/...` resolve from the skill root.

## `hallmark study`

The user has supplied a reference — either an attached screenshot or a URL to a live page — of a design they admire. They want to learn from it — its shape, its type, its rhythm — and apply that *DNA* to their own content. They do not want a pixel-faithful copy.

**Critical position:** `study` extracts structure, not pixels. It names the macrostructure, the archetypes, the type-pairing, the colour anchor, and (in image mode) the rhythm. It produces a *diagnosis report* before any code, then offers to rebuild the user's content using the extracted DNA. Pixel-cloning is not a feature.

**Always read [`references/study.md`](../study.md) before invoking this verb.** That file contains the source-mode detection rules, the extraction protocol (vision-pass for image mode, HTML/CSS-pass for URL mode), the structured-fields schema, the refusal heuristics (both image-mode and URL-mode refuse lists), the junk-or-blocked detection for URLs, and the type-role vocabulary. Do not work from intuition.

### Source-mode detection

If the user's input starts with `http://` or `https://` → **URL mode**. Otherwise → **image mode**. Same verb, same diagnosis output, different signal sources. The two modes share the schema and the diagnosis shape; they differ on what each extraction step can know — see `study.md` § Source mode.

### Pipeline

1. **Refuse-or-proceed check.** Before extracting anything (and in URL mode, **before WebFetch fires**), run the refusal heuristics in `study.md`. Image mode checks the image's content; URL mode runs the URL refuse list (themeforest, framer.com/templates, webflow.com/templates, gumroad UI-kit listings, dribbble shots, behance galleries, disclosed competitors). Ambiguous sources get one short question: *"Is this your own work, a public reference for inspiration, or someone else's live site?"*

2. **Extraction pass.**
   - **Image mode:** vision-pass on the attached capture per `study.md` § Five-step protocol.
   - **URL mode:** WebFetch the URL, then parse the returned HTML and any linked stylesheets. If the response trips any junk-or-blocked signal (auth wall, SPA shell, non-2xx response, no styling signal, < 1 KB body), **fall back** — emit the screenshot-fallback message from `study.md` § Junk-or-blocked detection and stop. Do not silently degrade.
   
   Output the structured-fields schema in `study.md` § The structured fields. URL mode fills the mode-conditional fields (`display_face`, `body_face`, `paper_value`, `accent_value`, `motion_library`) with exact values; image mode leaves those null.

3. **Diagnosis report.** Return a one-page "this is what you're looking at" using the matching template (image-mode template or URL-mode template) from `study.md` § The diagnosis report. Names the macrostructure, names the archetypes, points at the type pairing (with exact font names in URL mode), identifies anti-patterns the user should *not* carry over. URL-mode diagnoses must also call out the rhythm blind spot.

4. **Confirmation question.** Ask: *"Adopt this DNA wholesale, or change one axis? For example, I could keep the macrostructure but pick a theme that better matches your tone."* The diagnosis report's last line **also** surfaces the `design.md` emission CTA — *"Or — say `lock the DNA` if you want a portable `design.md` of this DNA."* Wait for the user's answer before doing anything.

5. **Branch on the user's response:**
   - **"Build with this DNA"** → run the build step below. Pick the closest matching theme from the catalog. Stamp the comment with the inferred macrostructure + archetypes + theme + source mode. The user's content goes in; the source's content does not.
   - **"Lock the DNA"** (or any other emission trigger phrase per `study.md` § Trigger phrases) → emit a portable `design.md` of the DNA per `study.md` § Emitting a `design.md` from `study`. **In URL mode, run the attestation step first** — ask whether the source is (a) user's own, (b) public reference for the user's brand, or (c) something else. (c) refuses emission; (a) and (b) write the file with a `## Provenance` block recording the answer. **Image mode emits without asking** — the user owns the screenshot. The emitted file becomes the project's locked system; subsequent runs defer to it.
   - **"Just the diagnosis was enough"** / silence → stop. The diagnosis is a complete deliverable.

### Output contract for `study`

When `study` produces code, the macrostructure stamp must include a `studied: yes` flag, the theme picked, and the source mode. Image mode example:

```css
/* Hallmark · macrostructure: Marquee Hero · H1 hero knobs: size=xxl, alignment=left-bias
 * theme: Studio · accent: forest-green ~3% · studied: yes · DNA-source: image (user reference)
 */
```

URL mode example — additionally records the URL and any exact-fonts / exact-colours that informed the build:

```css
/* Hallmark · macrostructure: Marquee Hero · H1 hero knobs: size=xxl, alignment=left-bias
 * theme: Studio · accent: forest-green ~3% · studied: yes · DNA-source: url
 * source-url: https://example.com/  ·  observed-fonts: Inter Tight + Inter
 * observed-accent: oklch(58% 0.16 35)  ·  rhythm: unknown (URL mode)
 */
```

The stamp signals to future Hallmark runs that this page's structure was extracted, not invented. That matters for the audit verb: a `studied: yes` page is audited *more* leniently for "Specimen fall-through" (the user explicitly chose this DNA) but *more* strictly for "did you actually use the extracted DNA, or did you drift back to defaults?"

### Limits to spell out to the user

When you return the diagnosis, name the limits explicitly:

- **Fonts:** in image mode, the skill names a *role* and proposes one or two real candidates from the canon — visual font ID is unreliable. In URL mode, the skill names the *exact* fonts the page loads (via `@font-face`, Google Fonts, `next/font`). The role still drives the rebuild — Hallmark may pick a different specific face for the user's content.
- **Imagery:** the skill never copies the source's photography. It generates structurally-equivalent placeholders or asks for the user's own assets.
- **Theme drift is allowed.** If the source is a Specimen and the user's content is a SaaS landing page, the skill picks a different theme. The DNA is the macrostructure + archetype + colour-anchor + type-pairing — not the dress.
- **Rhythm is the URL-mode blind spot.** HTML alone can't tell you whether the visual rhythm reads generous or templated. URL-mode diagnoses always state this and offer a screenshot fallback if it matters.

If `references/study.md` cannot be loaded for any reason, refuse the verb politely and direct the user to `hallmark redesign` with a written description of what they want from the source.
