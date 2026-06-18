# Slide Deck Spec

How to build the animated HTML presentation. Start from
`templates/presentation.html` — it already contains the full design system, the slide
engine, and one example of every slide layout. **Adapt content; don't rebuild the
engine.**

## Build steps

1. Copy `templates/presentation.html` → `docs/presentation.html`.
2. In `:root`, set the five palette vars to the brand palette (and `--ink`/`--muted`
   if a custom palette needs them).
3. Set brand text (`.brand`, footer) and the `<title>`.
4. Replace the slides between `<div class="deck">…</div>` with your content. Each
   slide is `<section class="slide" data-title="...">`. Order them as the narrative.
5. Embed diagrams on figure slides: `<img src="diagrams/<file>.svg" alt="...">`
   (relative path — keep the deck in `docs/` next to `diagrams/`).
6. Leave the `<script>` engine as-is. It auto-counts slides, builds dots, and wires
   navigation.
7. Render & view: `python scripts/render.py html --file docs/presentation.html
   --slides N --out docs/diagrams/preview --size 1600x900`. Fix anything that
   overflows the viewport, then re-render.

## Narrative arc (default 10–12 slides)

1. **Cover** — name, one-line value prop, brand chips, nav hint.
2. **Problem / why** — 3 pain cards, then a one-line "so we built…".
3. **Overview** — input → pipeline → output, 3 steps.
4–N. **Detail** — one slide per diagram (embed the SVG) and/or native grids:
   architecture, flow, roster, commands/entry points, guards/policies, data/state.
5 (near end). **Metrics / outcomes** — only real, code-backed measures; otherwise
   present the *framework* (what is measured), not invented numbers.
6. **Closing** — recap stats (counts), one-line takeaway, sign-off.

Match the diagram set: every diagram earns a slide; add native slides for content
that animates better as HTML (grids, metrics, step flows).

## Slide layouts (in the template)

| Class / pattern | Use |
|---|---|
| `.cover` | hero title (gradient), lead, chips, hint |
| head + `.cols3` `.pcard` | statement + 3 cards |
| `.flow` `.step` | input → process → output |
| `.figwrap` + `.figure img` | embed an SVG diagram + caption chips |
| `.agrid` `.acard` | roster grid (icon, name, tag, role, in→out) |
| `.cgrid` `.ccard` | command / entry-point cards with chips |
| `.kgrid` `.kcard` | metric cards (animated accent bar) |
| `.closing` `.stats` | big recap numbers + takeaway |

## Animation model

- Slide transition: `.slide` is absolute & faded/translated; `.active` shows it,
  `.past` shifts left. Directional, ~.66 s.
- Reveals: children with `class="reveal" style="--d:N"` fade/rise in, staggered by
  `--d`. Add `--d` 0,1,2,… in reading order.
- Figures animate with a subtle scale-in.
- Ambient blurred blobs drift slowly.
- `@media (prefers-reduced-motion: reduce)` disables transforms — keep it.

## Slide engine (already wired)

- Keyboard: → / ↓ / Space / PageDown = next; ← / ↑ / PageUp = prev; Home/End; `F`
  fullscreen.
- On-screen: prev/next buttons, clickable dot rail, slide counter.
- Touch swipe; deep-links (`presentation.html#6`); progress bar.
- The engine reads `total = slides.length` — add/remove `<section class="slide">`
  blocks and everything updates automatically.

## Embedding diagrams: two options

| Option | How | When |
|---|---|---|
| **Reference** (default) | `<img src="diagrams/x.svg">` | editable, small file; keep deck beside `diagrams/` |
| **Inline** | paste the `<svg>…</svg>` into the slide | fully self-contained single file to send around |

## Export

- **PDF**: open the deck → `Ctrl/Cmd+P` → Save as PDF, Landscape, margins None,
  enable "Background graphics". Navigate to each slide or print per `#N`.
- **PPTX**: easiest via the PDF, or insert the individual SVGs into PowerPoint
  (Insert → Pictures → This Device) for a native, editable deck.

## Checklist

- [ ] palette vars set; brand text updated
- [ ] every slide fits 16:9 with no scroll (verified by render)
- [ ] figure SVGs resolve (relative path) and are crisp
- [ ] reveals ordered with `--d`; reduced-motion kept
- [ ] no fabricated metrics; wording matches the code
