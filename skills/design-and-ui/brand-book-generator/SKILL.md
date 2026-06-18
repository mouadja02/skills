---
name: brand-book-generator
description: >
  Generate three radically distinct, on-trend brand concepts for any app or product and
  present them as a single no-scroll hero webpage — a bento "brand book" (logo + tagline,
  in-app screen, out-of-home, merch, palette, type, voice) that assembles itself with a
  staggered pop on every toggle. Grounded in 2024-2026 design trends, not safe defaults.
  Triggers: "brand kit", "brand book", "brand concepts", "show me a few directions",
  "make it look like an agency did it", "build a brand for my app".
license: MIT
metadata:
  author: hyperagent
  version: "1.0.0"
  source: alexmcdonnell-airtable/hyperagent-public-skills
---

# Brand Book Generator

Turns a one-line app description into a single **no-scroll hero webpage** that presents **three radically distinct brand routes** as a self-assembling **bento brand book**. Everything an agency would show — logo + tagline, in-app screen, out-of-home/billboard, merch, palette, type, voice — sits in one viewport. Toggling a route re-skins the entire canvas (color, fonts, corner radius), swaps every brand-applied mockup, and replays a staggered "assemble" animation.

## Inputs

- **Required:** app name, one-line description.
- **Optional:** audience, positioning/tone, founder photos, brand cues.

Proceed with strong invented directions if only name + one-liner are given.

## Ground the routes in CURRENT design trends (not stale defaults)

Search current year's trends first. Live trends to remix:
- **Claymorphism** — soft inflated 3D, warm saturated color, big squishy forms (tactile, playful).
- **Neo-brutalism + hi-vis** — stark canvas, dopamine acid color, monospace, hard edges, sticker energy.
- **Y2K / liquid chrome / retrofuture** — iridescent metal, holographic pink-cyan, scanlines.
- **Maximalism / structured excess**, **oversized & kinetic variable type**, **bento grids**.

## HARD RULES (do not violate)

- **NEVER use blue or purple gradients** — including the indigo→cyan→magenta "aurora"/AI-native mesh-gradient look. It is THE generic default and reads as un-designed. Reach for claymorphism, chrome/iridescent, hi-vis flat color, or maximalist clashing flats instead.
- **Avoid other over-trained looks:** warm cream + burnt-orange + serif, generic film-noir, flat gray SaaS minimalism.

## The divergence rule

Make the three routes feel like three different companies. Force divergence across:
- **Canvas VALUE** (don't ship three darks — vary light/dark)
- **Font pairing**
- **Surface texture** (soft-clay-3D vs flat-raw vs glossy-metal)
- **Accent family**
- **Voice**

Bold > safe. A proven trio: **claymorphism (warm) · neo-brutalist hi-vis (stark light) · Y2K chrome (dark metal)**.

## Workflow

### 1. Define three routes
Per route: name, idx, short tagline (gets typed), one positioning paragraph, 3 tone tags, 4-color palette (name + hex), type spec (display family + one display word + one mono line), one voice line.

### 2. Generate brand-applied mockups — 3 per route (9 total)
Per route: **in-app screen** (1:1), **out-of-home/billboard** (9:16), **merch flatlay** (3:2), art-directed to the route's world.

### 3. Build the bento brand book page

The page is a **100vh bento grid** with these tiles:
- **logo** (big) — wordmark + self-typing tagline + positioning + tone tags
- **app** — in-app screen mockup
- **merch** — merch flatlay
- **bill** (tall OOH) — billboard/out-of-home
- **pal** — palette swatches
- **type** — type specimen
- **voice** — verbal identity line

### Template mechanics

- **One 100vh shell, no scroll.** Collapses to scrollable stack under 900px.
- **Toggle = full re-skin + assemble replay** via `activate(key)` + the `.go` class.
- **Self-typing tagline** + blinking caret each activation; arrow keys switch.

### Theme token pattern

Each route gets its own CSS block:

```css
body[data-route="r1"] { /* claymorphism / warm tactile */
  --bg:#FFE3CC; --fg:#3A241B; --muted:#A8714C;
  --accent:#FF7A2F; --accent2:#FF4D6D; --radius:30px;
  --display:'Fredoka',sans-serif;
  --text:'Nunito',sans-serif;
  --mono:'Spline Sans Mono',monospace;
}
body[data-route="r2"] { /* neo-brutalist hi-vis / mono */
  --bg:#EAEAE3; --fg:#0E0E0C; --muted:#74746a;
  --accent:#C8FF00; --accent2:#1F4DFF; --radius:0px;
  --display:'Space Mono',monospace;
  --text:'Space Mono',monospace;
  --mono:'Space Mono',monospace;
}
body[data-route="r3"] { /* Y2K liquid chrome / retrofuture */
  --bg:#08080A; --fg:#EDEDF2; --muted:#8A8A98;
  --accent:#E8C7FF; --accent2:#8FE8FF; --radius:14px;
  --display:'Syne',sans-serif;
  --text:'Space Grotesk',sans-serif;
  --mono:'Space Mono',monospace;
}
```

### Route activation JS

```js
function activate(key) {
  const r = ROUTES[key];
  document.body.dataset.route = key;
  // Update toggles, tags, images, palette swatches, type specimen, voice line
  // Replay assemble animation
  bento.classList.remove("go");
  void bento.offsetWidth;
  bento.classList.add("go");
  typeTag(r.tagline);
}
```

## Gotchas

- Keep `ROUTES` keys `r1/r2/r3`.
- Fit-on-one-screen is the brief — keep copy tight so nothing overflows the desktop viewport.
- Re-check every route against the HARD RULES before publishing — especially no blue/purple gradients.

## Output

One no-scroll page = a full three-route brand book the founder tabs through and screen-records. Follow-ons: expand the chosen route into logo files, social kit, deck, packaging.
