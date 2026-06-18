---
name: nyt-data-viz
description: >
  NYT-discipline data visualization. Applies the design rules of The New York Times
  graphics desk + Upshot — color, typography, annotation, chart-type selection — to
  make any chart render at Times grade. Use whenever generating charts, dashboards,
  reports, or data-driven webpages. Triggers: "make this chart look professional",
  "NYT style", "editorial chart", "data viz", "dashboard design".
license: MIT
metadata:
  author: hyperagent
  version: "1.0.0"
  source: alexmcdonnell-airtable/hyperagent-public-skills
---

# NYT-discipline Data Visualization

Produce New York Times / Upshot–grade charts and dashboards: the typography, color restraint, chart-type judgment, and annotation discipline of the NYT graphics desk — for **both** static charts (Observable Plot) and hand-built **interactive** D3 dashboards.

## When to use

Any time you generate a chart, graph, dashboard, or data visualization and want it to read as editorial, trustworthy, and crafted — not a default library chart. Single charts, multi-panel dashboards, and scrollable data stories.

---

## The five core rules (every chart)

1. **Color.** One hero accent for the series that matters; everything else grey. Monotonic-luminance sequential ramps only — never rainbow/jet/HSV-equidistant. Diverging only with a meaningful zero. Categorical caps at ~7 hues; beyond that, small-multiple by category.
2. **Typography.** Playfair Display (display serif) + Libre Franklin (sans labels/annotation) + Source Serif 4 (body). `tabular-nums` on ALL numeric labels so digits don't jitter.
3. **Chart choice.** Line first for time; bar second; never pie; never dual y-axes; bars start at zero. Past ~5 series → small multiples.
4. **Annotation.** Declarative headline (a sentence, not a label) + subtitle naming unit & timeframe + source line. Label series DIRECTLY at endpoints (no legends). Annotate inflections in place. Humanized axis labels.
5. **Archie Tse rule.** Crucial info visible without interaction; mobile-test at 375px first.

---

## Chart-type selection (NYT patterns)

### Change over time
- **1 series** → line chart. One line, one accent color, direct end-of-line label. The dominant NYT chart.
- **2–5 series** → line chart with one hero series in accent + rest in grey. Color the line the story is about. Demote the rest to context.
- **>5 series** → small multiples (one panel per series, shared axes). Past ~5 lines, a single chart becomes spaghetti.

### Compare categories
- **Few (<15)** → horizontal bar chart, sorted by value. Labels fit horizontally; readers compare bar lengths effortlessly.
- **Many (>15)** → dot plot or small bar chart with named outliers. Annotate the head and tail; leave the middle as context.

### Show distribution
- Histogram or strip-plot (jittered dots). Don't use box plots in journalism — general readers don't read them.

### Show correlation
- Scatter plot with annotated outliers and a reference line. A naked cloud of dots tells nothing. Annotate 3-5 named points.

### Show composition
- Stacked bar (one bar per time-period or category). **NEVER pie.** NEVER 3D pie. NEVER donut unless the hole shows a total.
- Over time → stacked area chart with the most-changing component on top.

### Rank items
- Ranked horizontal bar chart, sorted descending. Sort by the variable being compared, not alphabetical.

---

## Color palette

```python
# Sequential ramps — ColorBrewer-derived, NYT-tuned. Monotonic luminance, colorblind-safe.
SEQUENTIAL = {
    "blue":   ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"],
    "red":    ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
    "green":  ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"],
    "grey":   ["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
}

# NYT-house accent palette
NYT_ACCENT = "#d62728"   # signature NYT red
NYT_BLUE   = "#1f77b4"
NYT_GREY   = "#bdbdbd"
NYT_BG     = "#ffffff"
NYT_GRID   = "#e9e9e9"
NYT_TEXT   = "#121212"

# Categorical — max 7 hues. Beyond 7, use small multiples.
CATEGORICAL = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1"]
```

## Typography CSS

```css
:root {
  --font-display: "Playfair Display", Georgia, serif;
  --font-body: "Source Serif 4", Georgia, serif;
  --font-sans: "Libre Franklin", Helvetica, Arial, sans-serif;
}
/* Numeric labels — tabular figures so transitions don't jitter */
.axis text, .value-label {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
}
/* Axis styling — minimal, no chart-junk */
.axis line, .axis path { stroke: #cccccc; shape-rendering: crispEdges; }
.axis .domain { display: none; }  /* no axis spine */
.gridline { stroke: #e9e9e9; stroke-dasharray: none; shape-rendering: crispEdges; }
```

## Google Fonts link

```html
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
```

---

## Interactive dashboards — cardinal interaction rules

Each rule prevents a real, observed bug.

### Rule A — Hit-layer coordinate space
The transparent hover `<rect>` MUST be appended to the SAME margin-translated `<g>` as the marks.

```js
// WRONG — overlay on svg root, marks in g(translate(m.left,m.top)) → off-by-margin
svg.append("rect").attr("x", m.left).attr("y", m.top) /* ... */;
// RIGHT — overlay in the same g as the marks; pointer == mark space
g.append("rect").attr("width", iw).attr("height", ih).attr("fill","transparent")
  .on("mousemove", function(ev){ const [mx,my] = d3.pointer(ev, this); /* find */ });
```

### Rule B — Proximity, not pixels
Never make the user hover a 2–3px dot. Build a Delaunay over the marks and snap to the nearest.

```js
const pts = data.map(d => [x(d.k), y(d.v), d]);
const del = d3.Delaunay.from(pts, p=>p[0], p=>p[1]);
// inside mousemove: const i = del.find(mx, my); const d = pts[i][2];
```

### Rule C — Gliding, anchored tooltip
Anchor the tooltip to the hovered mark's on-screen box and CSS-transition `left/top`.

```css
.tooltip{position:fixed;opacity:0;transform:translate(-50%,calc(-100% - 12px));
  transition:opacity 140ms ease, left 200ms cubic-bezier(.22,.61,.36,1),
  top 200ms cubic-bezier(.22,.61,.36,1);}
```
```js
function tipAtNode(node, html){
  const r = node.getBoundingClientRect();
  tip.innerHTML = html;
  tip.style.left = (r.left+r.width/2)+"px";
  tip.style.top = r.top+"px";
  tip.style.opacity = 1;
}
```

### Rule D — Domain covers the max
A hand-typed round cap pushes outliers off-canvas.

```js
// WRONG: const x = d3.scaleLinear().domain([0,10]);
const maxTotal = d3.max(data, d=>d.total);
const x = d3.scaleLinear().domain([0, maxTotal]).range([0, iw]);
```

### Rule E — Legible annotations
Give annotation text a paper-colored HALO.

```css
.anno,.anno-sub{paint-order:stroke fill;stroke:var(--panel);stroke-width:3px;stroke-linejoin:round}
```

## Reusable hover helper

```js
function voronoiHover(g, pts, nodes, w, h, onEnter, onLeave){
  const del = d3.Delaunay.from(pts, p=>p[0], p=>p[1]);
  g.append("rect").attr("width",w).attr("height",h).attr("fill","transparent")   // Rule A
    .on("mousemove", function(ev){ const [mx,my]=d3.pointer(ev,this);            // Rule B
      const i = del.find(mx,my); onEnter(pts[i][2], i, nodes ? nodes[i] : null); })
    .on("mouseleave", onLeave);
}
```

## Annotation linter checklist

Every chart should have:
- [ ] Declarative headline (a sentence: "COVID deaths fell in 2023")
- [ ] Subtitle naming unit + timeframe ("Weekly deaths, U.S., 2020-24")
- [ ] Source line ("Source: CDC. Note: ...")
- [ ] Direct labels at endpoints (no legends)
- [ ] Hero color for one series, grey for rest
- [ ] Y-axis starts at 0 for bar charts
- [ ] Pale gridlines (#e9e9e9), no axis spine
- [ ] Mobile-tested at 375px
- [ ] Crucial info visible without interaction

## Pre-publish checklist

1. Domain from `d3.max` (D).
2. Every hover rect in the marks' `<g>` (A).
3. Voronoi proximity (B).
4. Gliding anchored tooltip (C).
5. Halo + leader annotations (E).
6. Connected-scatter only if both axes monotonic.
7. Extract the inline `<script>`, run `node --check`, and `JSON.parse` the embedded data blob.
8. If a headless browser is reachable, screenshot at desktop + 375px and confirm every panel paints.
9. Cut editorial text to ~half the first-draft instinct.
