# Design tokens

All tokens are injected as CSS custom properties on `:root`. Don't introduce new ad-hoc colors or fonts during scene authoring — pick from the table or extend the palette here first.

## Default palette: Midnight Purple (anass.pro)

```css
:root {
  /* Surfaces */
  --bg:      #09080C;          /* page background — near-black, warm */
  --bg2:     #111018;          /* alt section background — slight lift */

  /* Ink */
  --ink:     #ECEAF4;          /* primary text — off-white with violet bias */
  --ink2:    rgba(236,234,244,.78);   /* secondary text */
  --dim:     rgba(236,234,244,.35);   /* tertiary / labels */

  /* Brand */
  --purple:  #7B4FE0;          /* core brand — deep electric purple */
  --purhi:   #A07EF0;          /* highlight purple — hover/active */
  --cyan:    #5B9FD8;          /* cool accent — used sparingly in gradients */

  /* Gradient endpoints (one place, used everywhere) */
  --wa:      #5B6DE0;          /* gradient start — violet-blue */
  --wb:      #A855F7;          /* gradient end — magenta-violet */

  /* Borders */
  --border:  rgba(123,79,224,.16);    /* subtle violet hairline on cards/tables */
}
```

### Usage rules

- `--bg` covers the body; `--bg2` lifts hero subsections (Reveal scene uses it).
- `--ink` for body text. `--ink2` for paragraphs that aren't the lede. `--dim` for kickers and metadata only.
- `--purple` is the *brand* — use it for highlighted words (`<span class="pu">`), kickers, hover states.
- `--purhi` only on hover/focus or "alive" states.
- `--cyan` is the *secondary spell* — it appears in waves and the second projectile in the game. Use it for at most one decorative element per scene.
- Gradient `linear-gradient(135deg, var(--wa), var(--wb))` is the format's signature. Reserve it for: the top progress bar, exactly one gradient-clipped phrase per scene (`.grad`), the CTA button, and the rule under headings.

## Alternative palettes (preserve the architecture, change the mood)

These are drop-in replacements — same variable names, different values. Pick one and substitute in `:root`. Don't blend two palettes.

### "Bone & Ember" (warm dark)

```css
--bg:#0E0A07; --bg2:#16110C;
--ink:#F4ECDF; --ink2:rgba(244,236,223,.78); --dim:rgba(244,236,223,.35);
--purple:#E0834F; --purhi:#F0A87E;
--cyan:#D8B25B;
--wa:#E0925B; --wb:#F75555;
--border:rgba(224,131,79,.18);
```

### "Lab Coat" (cool clinical)

```css
--bg:#0A0E12; --bg2:#10151B;
--ink:#E6EFF5; --ink2:rgba(230,239,245,.78); --dim:rgba(230,239,245,.35);
--purple:#4FBFE0; --purhi:#7ED6F0;
--cyan:#5BD89B;
--wa:#5BB7E0; --wb:#55F7C9;
--border:rgba(79,191,224,.16);
```

### "Night Garden" (verdant night)

```css
--bg:#070C09; --bg2:#0E1612;
--ink:#E8F4EC; --ink2:rgba(232,244,236,.78); --dim:rgba(232,244,236,.35);
--purple:#4FE08F; --purhi:#7EF0AE;
--cyan:#5BD8B7;
--wa:#5BE07B; --wb:#A8F755;
--border:rgba(79,224,143,.16);
```

### "Plum Velvet" (warmer purple)

```css
--bg:#0A0712; --bg2:#13101A;
--ink:#F1EAF4; --ink2:rgba(241,234,244,.78); --dim:rgba(241,234,244,.35);
--purple:#A04FE0; --purhi:#C07EF0;
--cyan:#E05B9F;
--wa:#A05BE0; --wb:#F755D6;
--border:rgba(160,79,224,.16);
```

### "Editorial Mono" (high-contrast, no chroma)

Drop the gradient — replace it with a single accent color. Best when copy carries the entire emotional load.

```css
--bg:#070707; --bg2:#0F0F0F;
--ink:#F5F5F5; --ink2:rgba(245,245,245,.72); --dim:rgba(245,245,245,.32);
--purple:#FF3B3B; --purhi:#FF6E6E;     /* single red accent */
--cyan:#FF3B3B;
--wa:#FF3B3B; --wb:#FF3B3B;            /* "gradient" is solid */
--border:rgba(255,59,59,.18);
```

## Typography system

Four fonts, four roles. Each font does exactly one job. **Do not** substitute a single font for multiple roles — the contrast between condensed-bold display and italic-serif quotes is the format's typographic identity.

```css
:root {
  --fb: 'Barlow', sans-serif;              /* body */
  --fc: 'Barlow Condensed', sans-serif;    /* display, condensed bold */
  --fm: 'JetBrains Mono', monospace;       /* labels, kickers, chips */
  --fs: 'Fraunces', 'Times New Roman', serif; /* italic display, quotes, sign-offs */

  /* Sizes */
  --xs:.68rem; --sm:.82rem; --base:.95rem; --md:1.05rem; --lg:1.25rem;

  /* Letter-spacing */
  --lsc:.16em;     /* "uppercase wide" — kickers, mono labels */
  --lsw:.09em;     /* "uppercase normal" — buttons, chips */
  --lsn:.02em;     /* "natural" — body */
}
```

Google Fonts URL (preconnect first, then load):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Barlow+Condensed:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,800;1,9..144,400&display=swap" rel="stylesheet">
```

### Per-element type rules

| Role | Font | Weight | Style | Size example |
|---|---|---|---|---|
| Section title (`.sec-title`, `.chl`) | `--fc` | 800 | upright | `clamp(2.8rem, 6vw, 5rem)` |
| Hero / hook line (`.hook-line`) | `--fc` | 700 | upright | `clamp(1.9rem, 4.5vw, 3.4rem)` |
| Sub / tagline (`.sec-sub`, `.cbody`) | `--fb` | 300 | italic | `var(--lg)` to `clamp(1.05rem, 1.8vw, 1.3rem)` |
| Body paragraph (`.rev-body`, `.pbio`) | `--fb` | 300 | upright | `var(--lg)` |
| Kicker / label (`.sec-label`, `.bi-tag`) | `--fm` | 400 | upright | `var(--xs)`, uppercase, `--lsc` |
| Chip (`.chip`) | `--fm` | 400 | upright | `var(--xs)`, uppercase, `--lsw` |
| Italic display quote (`.mquote`, `.csig`) | `--fs` | 400 | italic | `clamp(1.7rem, 3.2vw, 2.6rem)`, `font-variation-settings:"opsz" 96` |
| CTA (`.cta`) | `--fc` | 600 | upright | `var(--base)`, uppercase, `--lsw` |

### Why these specific fonts

- **Barlow Condensed @ 800** has a strong vertical rhythm that competes with Cyrillic/Arabic-style heaviness — perfect for "tu as utilisé 500 porte-monnaie" hitting hard.
- **Barlow @ 300 italic** is the voice of the *sub*. Light + italic reads as personal address.
- **JetBrains Mono @ 400** is technical without being pixelly. It signals "this person ships code", which the site's claim depends on.
- **Fraunces @ italic** with high optical-size (`opsz` 96+) is editorial luxury — it appears at exactly the moments the tone shifts to confession or revelation. Don't use Fraunces for body text; the optical-sizing axis is what makes the italic display work.

## Spacing scale

The site uses a coarse, intentional spacing system, not a fine-grained 8px grid.

```
0.6rem   tight (chip padding)
1rem     standard cell padding
1.5rem   between adjacent content blocks within a card
2rem     section internal padding
3.5rem   between major content groups in a scene
4rem     between scenes' subtitle and content
7rem 8vw `.scene` outer padding (top/bottom 7rem, left/right 8vw)
```

Mobile (`<=768px`) collapses scene padding to `4.5rem 6vw 7rem`.

## Motion tokens

Two easing curves, one timing scale. Don't reach for cubic-beziers ad hoc.

```css
:root {
  /* Easing */
  --ease-out:    cubic-bezier(.22, 1, .36, 1);   /* default reveal/transition */
  --ease-cubic:  ease;                            /* simple opacity fades */

  /* Durations */
  /* fast hover    180-220ms */
  /* reveal        650ms */
  /* word stagger  45ms per word, 25ms for closing copy */
  /* card show     480ms */
  /* arrow draw    1000ms */
  /* counter rise  2000ms (cubic ease-out) */
}
```

## Decorative effects

### SVG noise overlay (always on)

```css
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity: .025;        /* keep this low — it's a texture, not a graphic */
  pointer-events: none;
  z-index: 9997;
}
```

This is the "film grain" feel. Without it, the dark surface looks digital and flat. Don't increase opacity above `.04` or it becomes noise.

### Heading rule (gradient bar)

```css
.rule {
  width: 40px; height: 2px;
  background: linear-gradient(90deg, var(--wa), var(--wb));
  margin: 1.5rem 0;
}
```

Used as a punctuation mark between sub-headings.

### Border-left accent for italic quotes

```css
.mquote, .csig {
  border-left: 2px solid var(--purple);
  padding-left: 2.2rem;
}
.csig::before {
  /* extra gradient bar overlay on the border-left */
  content: '';
  position: absolute; left: -1px; top: 50%;
  width: 3px; height: 36%;
  background: linear-gradient(180deg, var(--wa), var(--wb));
  transform: translateY(-50%);
  border-radius: 2px;
}
```

## CSS variable naming convention

Stick to anass.pro's two-letter abbreviations. They're terse, but they make the inline `<style>` block (which is large) much more readable. Don't rename them to `--brand-color` etc. — the patterns in `references/animation-patterns.md` reference these exact names.
