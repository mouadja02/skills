# Design System

The visual language that makes the output light, clean, professional and
eye-friendly. Both the SVG diagrams and the HTML deck share one palette.

## Palette

Default (company branding), ordered **darkest → lightest**:

| Token | Hex | Role |
|---|---|---|
| `navy` | `#03045e` | headings, body text, emphasis fills (white text on it), strongest accents |
| `blue` | `#0077b6` | section accents, arrows, links, secondary emphasis |
| `cyan` | `#00b4d8` | bright accents, highlights, dashed/guard elements, progress |
| `light` | `#90e0ef` | chip & box fills, soft borders |
| `pale` | `#caf0f8` | page/section backgrounds, subtle fills |

Any 5-colour list works — `svg_kit.Theme.from_palette()` derives the rest:

- `ink` = darkest (body text)
- `muted` = `mix(darkest, white, .50)` (secondary text)
- `line` = `mix(darkest, white, .86)` (hairlines / soft borders)
- `tint` = `mix(palest, white, .55)` (very light card tint)

### Rules

- **Background light.** White or near-white with faint tints; never dark behind diagrams.
- **Dark text on light fills.** Body text = `navy`; secondary = `muted`. Never
  light-on-light. White text only on `navy`/`blue` fills.
- **Few colours per element.** One accent stripe + one fill + dark text. No rainbow.
- **Emphasis** = the `navy`→`cyan` gradient (`url(#accent)`), used sparingly for
  hero text, the deck progress bar, and one "brain"/primary block per diagram.

## Typography

Two separate font strategies — this matters:

### Diagrams (SVG) — system-safe only
PowerPoint renders SVG text with **system** fonts, so use a system stack (the
toolkit default). Do **not** rely on webfonts inside SVG.

```
font:  'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif
mono:  'Cascadia Code', 'Consolas', 'SF Mono', ui-monospace, monospace
```

### Deck (HTML) — premium webfonts
Use distinctive, professional fonts (avoid generic Inter/Roboto). Default pairing:

```html
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
```

| Role | Font | Fallback |
|---|---|---|
| display / headings | Bricolage Grotesque | Plus Jakarta Sans, system-ui |
| body | Plus Jakarta Sans | system-ui, Segoe UI |
| mono / labels | IBM Plex Mono | ui-monospace, Consolas |

Alternate professional pairings (rotate to avoid sameness): *Fraunces* + *Hanken
Grotesk*; *Schibsted Grotesk* + *Inter Tight*; *Sora* + *Manrope*; *Clash Display*
(self-host) + *Plus Jakarta Sans*.

## Type scale

| Use | Size (SVG px) | Weight |
|---|---|---|
| diagram title | 27 | 700 |
| diagram subtitle | 14.5 | 400 |
| section label | 15–16 | 700 |
| card title | 14–16.5 | 700 |
| body / item | 12–13 | 400 |
| chip / mono | 11–12.5 | 400–600 |

Deck headings use `clamp()` so they scale to the screen (e.g.
`clamp(30px,4.4vw,52px)` for H2, big hero on the cover).

## Spacing

- Outer margin: **60 px** in SVG (`x: 60 … W-60`).
- Consistent gaps: 12–26 px between peers; 22–30 px between groups.
- Card padding: 18–26 px. Corner radius: 11–18 px. One soft shadow (`url(#soft)`).
- **Breathing room beats density.** If it feels tight, remove an item or split slides.
- Align everything to an invisible grid; centre multi-column groups on the canvas.

## Motion (deck only)

- One orchestrated page-load per slide: directional slide transition + **staggered
  reveals** (`--d` index → `transition-delay`). Durations ~.5–.8 s, easing
  `cubic-bezier(.2,.7,.2,1)`.
- Ambient: slow-drifting blurred blobs at low opacity for depth.
- Always include `@media (prefers-reduced-motion: reduce)` to disable transforms.
- Motion supports comprehension; never distracts.

## Do / Don't

- ✅ Light bg, dark text, generous space, aligned grids, one accent per element.
- ✅ Verify by rendering to PNG and looking.
- ❌ Rainbow chips, light-on-light, overlaps/clipping, tiny crammed text.
- ❌ Webfonts inside SVG, generic deck fonts, fabricated numbers.
