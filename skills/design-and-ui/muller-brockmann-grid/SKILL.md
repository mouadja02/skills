---
name: muller-brockmann-grid
description: >
  Build editorial/magazine/report webpages on a GENUINE Müller-Brockmann modular grid
  (International Typographic Style). Encodes the discipline (columns + modules + baseline,
  grotesque type, flush-left, restrained black/white/red palette) AND the front-end
  engineering to make the grid real, visible, and verified: one CSS-variable source of
  truth, an interactive grid-toggle overlay, subgrid bands, 8px baseline lock, and
  runtime optical alignment. Triggers: "magazine spread", "grid system", "Swiss design",
  "editorial layout", "show the grid", "align everything to the grid".
license: MIT
metadata:
  author: hyperagent
  version: "1.0.0"
  source: alexmcdonnell-airtable/hyperagent-public-skills
---

# Müller-Brockmann Grid Systems — built real, visible, and verified

Josef Müller-Brockmann (1914–1996), Zurich; *Grid Systems in Graphic Design* (1981) is the corpus. The grid is treated as an ethic, not decoration: **"The grid system is an aid, not a guarantee. It permits a number of possible uses and each designer can look for a solution appropriate to his personal style. But one must learn how to use the grid; it is an art that requires practice."**

> Two real review notes this skill exists to prevent:
> 1. *"the grid is just slapped on top and misaligned"* → the overlay wasn't in the same content box as the content (see §2.2).
> 2. *"the H in the headline is off the grid"* → the headline's BOX was on the grid but its INK wasn't; large glyphs carry a side-bearing (see §2.6). **Box-on-grid ≠ ink-on-grid.**

---

## PART 1 — THE DISCIPLINE (decide before drawing)

- **Objective order.** The grid brings "constructive thought," legibility, and "objective and functional" design.
- **Modular grid.** Divide the type area into **modules** — columns AND rows — separated by consistent **gutters**, inside defined **margins**. For the web, a **12-column grid + 8px baseline** is a robust general default.
- **Baseline grid.** Vertical rhythm is sacred: **leading = a whole multiple of the baseline unit**, and every element snaps to it.
- **Typography.** A **grotesque sans** (Akzidenz-Grotesk / Helvetica; on the web Inter, Helvetica Now, Archivo). **Flush-left, ragged-right.** Few sizes, large jumps in **scale** for hierarchy.
- **Palette.** Pure white paper, near-black ink, **one accent — red is canonical** (`#e4002b`).
- **White space + asymmetry.** Generous margins; asymmetric compositions held in tension by the grid.

---

## PART 2 — MAKE THE GRID REAL ON THE WEB

### 2.1 One source of truth

Put every grid parameter in `:root` CSS variables:

```css
:root {
  --cols: 12;
  --bl: 8px;              /* baseline unit */
  --lh: 24px;             /* leading = 3 × baseline */
  --gutter: 24px;
  --margin: 72px;
  --maxw: 1296px;
  --paper: #ffffff;
  --ink: #111315;
  --ink-soft: #5b6066;
  --accent: #e4002b;
}
```

### 2.2 The overlay MUST live in the SAME content box ← #1 bug

Failure mode: content sits in a centered `max-width` container while the overlay is a full-width sibling. On any viewport wider than `--maxw`, they no longer share column positions.

**Fix:** put `.guides` *inside* the same `.wrap`, and draw the column guides with the same `repeat(var(--cols),1fr)` + `column-gap:var(--gutter)`.

### 2.3 Place every element by column LINE via subgrid bands

```css
.band {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: subgrid;
  column-gap: var(--gutter);
  align-items: start;
}
@supports not (grid-template-columns: subgrid) {
  .band { grid-template-columns: repeat(var(--cols), 1fr); }
}
```

Children place with `grid-column: <startline> / <endline>` (e.g. `1 / 6`, `6 / 13`).

### 2.4 Lock vertical rhythm to the baseline

- Leading = `--lh` (e.g. 24px = 3×8). **Every line-height in px (not unitless) for display type.**
- Every margin/padding a multiple of the baseline.
- **Media heights = multiples of the leading** (e.g. 240/360/432/480px) so a photo's top AND bottom both land on lines.

### 2.5 The toggle (sizzle within the sizzle)

A control (button **+ `G` key**) toggles `body.grid-on`; overlay fades 0→1. Overlay draws: translucent numbered column fields, baseline lines, and margin lines.

### 2.6 OPTICAL ALIGNMENT — display ink, not its box ← the subtle bug

A 180px headline whose layout box is exactly on line 1 still looks misaligned because the letterform's **ink** is inset by its **left side-bearing**.

```js
// After document.fonts.ready and on resize:
var cvs = document.createElement('canvas'), ctx = cvs.getContext('2d');
document.querySelectorAll('.masthead,.numeral,.shead h2,.h2b').forEach(function(el){
  el.style.marginLeft = '0px';
  var cs = getComputedStyle(el), ch = (el.textContent||'').trim()[0];
  if (!ch) return;
  if (cs.textTransform === 'uppercase') ch = ch.toUpperCase();
  ctx.font = cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
  ctx.textAlign = 'left';
  var abl = ctx.measureText(ch).actualBoundingBoxLeft;
  if (isFinite(abl)) el.style.marginLeft = abl.toFixed(2)+'px';
});
```

**CRITICAL:** side-bearing is font-specific. Headless Chrome usually lacks the webfont, so canvas falls back to a different grotesque.

---

## PART 3 — VERIFY (don't trust, measure)

Render with headless Chrome (Puppeteer) and assert at **several widths** (e.g. 1440 / 1180 / 900):

1. **Column adherence** — every `.band > *` left snaps to a column START and right to a column END (~0px).
2. **Overlay match** — each `.guides .col` rect equals the computed column rect (~0px).
3. **Baseline** — text tops modulo the baseline ≈ 0.
4. **Optical ink** — each display element's ink-left equals its own column line.

A clean run: `col=0px overlay=0px baseline≤4px ink=0px` → `GRID VERIFY: PASS`.

---

## PART 4 — CRAFT DEFAULTS

- **Palette:** white `#fff`, ink `#111`, one accent (Swiss red `#e4002b`).
- **Type:** Inter / Helvetica Now / Archivo for display + body; Space Mono / IBM Plex Mono for folios, captions, grid annotations.
- **Hierarchy** through scale + weight + white space, not color. Treat key data as **large numerals**.

---

## PART 5 — WORKFLOW

1. Pick the subject; gather real photos.
2. Generate the scaffold (`:root` tokens, `.grid`/`.band` subgrid, `.guides` overlay, toggle JS, optical-alignment JS).
3. Build spreads as subgrid bands; place everything by column line; lock spacing to the baseline.
4. Add the overlay + toggle + optical-alignment JS.
5. Verify: eyeball a top-left zoom crop. Fix, republish.

## CREED

A grid you can't toggle on and measure is a mood board, not a system. Build it from one source of truth, prove it at 0px, and align the **ink**.
