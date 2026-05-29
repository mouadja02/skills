---
name: codebase-diagrams-and-slides
description: >-
  Turns any codebase into branded, presentation-ready SVG diagrams and an optional
  smooth animated HTML slide deck. Analyzes a repository in any language (Markdown,
  Python, Rust, dbt, SQL, JS/TS, Java, Go, ...), extracts its architecture / flow /
  story, and generates eye-friendly 16:9 diagrams plus a polished, professional
  presentation. Use when the user asks to visualize, diagram, document, illustrate,
  or present a codebase, architecture, pipeline, or project; to build slides or a
  deck about a repo; or to produce diagrams from code. Defaults to the company brand
  palette (#03045e, #0077b6, #00b4d8, #90e0ef, #caf0f8) and writes to docs/diagrams/
  and docs/presentation.html.
compatibility: "Any codebase · Cursor agents"
metadata:
  audience: Engineers, architects, presenters
  author: ATOS
---

# Codebase → Diagrams & Slides

Produce a small set of **branded vector diagrams** and an optional **animated HTML
slide deck** that explain a codebase to humans. The output bar is high: light,
clean, eye-friendly, professionally typeset, well-spaced, and visually verified.

This skill is **language-agnostic**. It reads the repo, distills the story, then
renders it with a proven, palette-driven toolkit so results are consistent every time.

## What you produce

| Artifact | Default path | Notes |
|---|---|---|
| Diagrams | `docs/diagrams/*.svg` | N branded 16:9 (1280×720) vector files, PPT-insertable |
| QA renders | `docs/diagrams/preview/*.png` | screenshots used to visually verify layout |
| Slide deck | `docs/presentation.html` | optional single-file animated deck that embeds the diagrams |
| Build script | `docs/diagrams/build_diagrams.py` | reproducible generator (imports the toolkit) |

## Inputs & defaults

Resolve these before building. Everything except the codebase has a smart default.

| Input | Default | Notes |
|---|---|---|
| **Codebase** | current repo / path given | scope to a folder or whole repo |
| **Palette** | `["#03045e","#0077b6","#00b4d8","#90e0ef","#caf0f8"]` | company branding; accept any 5-color list |
| **# diagrams** | 4–6, chosen by archetype | see archetype map below |
| **Diagram set / layouts** | archetype-driven | see `references/diagram_patterns.md` |
| **Slides?** | only if requested | if yes, default **10–12** slides |
| **Audience / depth** | technical, medium depth | shapes wording and density |
| **Language** | English | match the user's language if they ask |
| **Aspect / theme** | 16:9 · light | diagrams are light; deck is light |
| **Output dirs** | `docs/diagrams/`, `docs/presentation.html` | keep deck next to `diagrams/` |

## Decide vs. ask

- If the user says **"you decide / feel free / pick for me"**, do **not** interrogate
  them — apply the defaults above and **state your assumptions** in the summary.
- Otherwise, if key parameters are missing, ask **once** with a compact `AskQuestion`
  (max ~5 questions). High-value questions only:
  1. Number of diagrams (auto / 3 / 5 / 6).
  2. Slide deck? (no / yes ~8 / yes ~12 / yes — you choose count).
  3. Palette (company default / custom hex list).
  4. Audience (engineers / mixed / executives).
  5. Anything specific to emphasize (a subsystem, a flow, KPIs…).
- Never block on trivia. Pick reasonable defaults for fonts, spacing, file names.

## Workflow

```
- [ ] 0  Resolve inputs (codebase, palette, #diagrams, slides?, audience)
- [ ] 1  Explore the codebase and distill the story
- [ ] 2  Plan the diagram set (archetype → set)
- [ ] 3  Generate diagrams with the toolkit → docs/diagrams/
- [ ] 4  Render to PNG, VIEW them, fix overlaps/overflow
- [ ] 5  (optional) Build the deck from the template → docs/presentation.html
- [ ] 6  Summarize, embed previews, offer tweaks
```

**0 · Resolve** — settle inputs per the policy above. Echo the plan in one line.

**1 · Explore** — understand before drawing. Prefer the `explore` subagent (or read
key files: entry points, READMEs, config, module/dir layout, command/agent/route
definitions, data models). Extract: purpose, top-level components, layers, the main
flow/lifecycle, key entities, data/state movement, external systems, and any
"reliability" rules (guards, tests, policies). Write a 5–10 bullet "story" you will
draw. Do not fabricate behavior — only diagram what the code shows.

**2 · Plan the set** — map the codebase archetype to a diagram set (table below).
Pick the count from inputs. Each diagram = one clear idea.

**3 · Generate** — copy `scripts/svg_kit.py` into `docs/diagrams/`, then write
`docs/diagrams/build_diagrams.py` that does `import svg_kit as k` and composes each
diagram with the proven primitives (so the output folder is self-contained and
reproducible). Canvas is **1280×720**. Use the layout recipes in
`references/diagram_patterns.md`. Follow `references/design_system.md` for palette
roles, fonts, spacing. Call `k.use_palette([...])` first, then run it to emit SVGs.

**4 · Verify (mandatory)** — render every SVG to PNG with `scripts/render.py` and
**actually open the PNGs** to inspect. Fix text overflow, overlaps, off-canvas
elements, weak contrast, and crowding. Re-render after each fix. Never ship diagrams
you have not looked at.

**5 · Deck (optional)** — copy `templates/presentation.html` to
`docs/presentation.html`. Set the 5 palette vars in `:root`, brand text, and slide
content. Embed diagrams with relative `img src="diagrams/<file>.svg"`. The slide
engine auto-counts slides, builds dots, supports keyboard / dots / buttons / swipe /
fullscreen / deep-links, and respects reduced motion — don't reinvent it. Then render
slides (`render.py html ... --slides N`) and view them. See
`references/slide_deck_spec.md`.

**6 · Summarize** — list outputs, embed a few preview PNGs, state assumptions, and
offer concrete next tweaks (count, language, dark theme, logo, PDF/PPTX export).

## Codebase archetype → diagram set

Use as a starting set; trim/extend to the requested count.

| Archetype (signals) | Recommended diagrams |
|---|---|
| **Agentic / pipeline / workflow** (agents, commands, phases, guards) | layered architecture · phase/flow · agent or worker roster · command/entry-point map · guards/policies columns · file/state handoff |
| **Library / SDK** (public API, packages) | module architecture · public API surface · core data/types model · request/call lifecycle (sequence) · extension points |
| **Web app / service** (routes, components, controllers) | system architecture · component/module tree · request lifecycle · data/state flow · deployment topology |
| **Data / dbt / ELT** (models, sources, tests) | layer model (staging→marts) · DAG/lineage · source→target flow · materialization & schemas · tests/quality gates |
| **CLI tool** (subcommands, config) | command map · execution flow · config resolution · output/artifacts |
| **Systems / Rust / Go** (crates, services) | crate/module architecture · data/ownership flow · concurrency/runtime model · build & deploy |

Reusable layouts that cover almost everything: **layered bands**, **phase/snake
flow**, **card grid (roster)**, **mapping rows**, **themed column cards**,
**node/handoff flow**. Recipes: `references/diagram_patterns.md`.

## Design system (summary)

Full detail in `references/design_system.md`. Essentials:

- **Palette roles** (from the 5 colors, darkest→lightest): darkest = headings /
  emphasis fills (white text on it); mid = section accents / arrows; bright = accents
  & highlights; light = chip/box fills; pale = backgrounds. Body text is the darkest
  color; secondary text a derived muted tint. Light background, generous whitespace.
- **Contrast**: dark text on light fills. Never light-on-light or rainbow chips.
- **Fonts** — diagrams use **system-safe** fonts (Segoe UI / system stack) so they
  render identically inside PowerPoint. The HTML deck uses **premium webfonts**
  (Bricolage Grotesque display + Plus Jakarta Sans body + IBM Plex Mono) with safe
  fallbacks. Avoid generic Inter/Roboto in the deck.
- **Spacing** — consistent margins, breathing room, aligned grids; never crowd.
- **Motion** (deck only) — one orchestrated load: directional slide transitions +
  staggered reveals. Purposeful, smooth, never gratuitous.

## Quality bar

What makes the output good — hold to all of it:

1. **One idea per diagram.** A viewer gets it in ~5 seconds.
2. **Clarity over density.** Cut detail before crowding.
3. **Strong hierarchy.** Title → sections → items, sized accordingly.
4. **Restraint.** Few colors, aligned grids, consistent radii/shadows.
5. **Motion with purpose** (deck) and **respect reduced-motion**.
6. **Verify visually.** Render and look. Fix anything that overlaps or overflows.
7. **Truthful.** Diagram only what the code does. Don't invent metrics/numbers.

## Verification (do not skip)

`SKILL` below = `.cursor/skills/codebase-diagrams-and-slides`. Copy `svg_kit.py` once
so the build script can import it (`cp` on macOS/Linux, `Copy-Item` in PowerShell).

```
# diagrams
cp  $SKILL/scripts/svg_kit.py  docs/diagrams/
python -X utf8 docs/diagrams/build_diagrams.py
python $SKILL/scripts/render.py svgs --dir docs/diagrams --out docs/diagrams/preview
# → open the PNGs and inspect every one; fix and re-render

# deck
python $SKILL/scripts/render.py html --file docs/presentation.html --slides N \
       --out docs/diagrams/preview --size 1600x900
# → open the slide PNGs and inspect; fix and re-render
```

`render.py` finds Chrome/Edge automatically (Windows/macOS/Linux). On Windows use
`python -X utf8`.

## Output & portability

- Diagrams: `docs/diagrams/`. Deck: `docs/presentation.html` (keep it **next to**
  `diagrams/` because it references the SVGs by relative path).
- For a self-contained, send-anywhere deck, inline the SVG markup into the HTML
  instead of `img src` (note this trade-off to the user).
- The deck loads webfonts from Google Fonts when online; it degrades gracefully
  offline via the fallback stack.

## Anti-patterns

- No rainbow palettes, no light-text-on-light, no overlapping/clipped elements.
- Don't fabricate data, KPIs, or behavior not present in the code.
- Don't ship without rendering and viewing the output.
- Don't hand-place dozens of chips by eye — use the toolkit's text measurement.
- No Windows-style paths in generated code (`scripts/x.py`, not `scripts\x.py`).
- Don't drop or restyle the company palette unless the user gives a new one.

## Files in this skill

| File | Use |
|---|---|
| `scripts/svg_kit.py` | **Execute/import.** Palette-driven SVG primitives (Theme, text measurement, chips, cards, arrows, db cylinder, header/footer). The heart of consistent diagrams. |
| `scripts/render.py` | **Execute.** Cross-platform headless-browser renderer for SVG + HTML → PNG (visual QA). |
| `templates/presentation.html` | **Copy & adapt.** The full animated deck (CSS design system + slide engine + every slide layout). |
| `templates/build_diagrams_example.py` | **Read/run.** Worked example: build two diagrams with `svg_kit`. |
| `references/design_system.md` | Palette roles, font pairings + Google Fonts link, spacing, do/don't. |
| `references/diagram_patterns.md` | The six reusable diagram layouts with layout math and toolkit calls. |
| `references/slide_deck_spec.md` | Deck architecture: slide types, transitions, chrome, nav, accessibility, export. |
