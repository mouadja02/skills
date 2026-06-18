# Diagram Patterns

Six reusable layouts that cover almost any codebase. Canvas is **1280×720**. All use
`svg_kit` (`import svg_kit as k; th = k.TH`). Always finish a diagram with
`k.header(...)` first and `k.footer(...)` last, then `k.save(name, body)`.

General rules:
- Content area: `x = 60 … 980` for a main band + optional right rail `1000 … 1230`,
  or full width `60 … 1220`.
- Size chips/cards from text using `k.tw()` / `k.chip()` — never guess widths.
- Centre multi-column groups: `left = (W - (n*cw + (n-1)*gap)) / 2`.
- After building, **render and look** (`scripts/render.py`). Fix overlaps.

Pick patterns from the archetype map in `SKILL.md`. A typical set mixes 1 (overview),
2 (process), 3 (inventory), and one of 4/5/6 (detail).

---

## 1 · Layered bands — "system architecture"

Stacked full-width bands (top→bottom = user→storage), each with a left accent stripe,
a label zone, and chips; optional right "rules/standards" rail. Connect bands with
short vertical arrows.

```python
y, h = 112, 66
body += k.card(60, y, 920, h, fill=th.tint, accent=th.blue)      # band
body += k.T(86, y + h/2 - 3, "Slash Commands", 15.5, th.navy, bold=True)
body += k.T(86, y + h/2 + 16, "thin orchestrators", 10.5, th.muted)
row, _ = k.chip_row(268, y + h/2 - 15, ["/migrate", "/validate", "/status"],
                    gap=11, fill=th.paper, stroke=th.blue, bold=True)
body += row
# arrow into the next band (centre x = 520)
body += k.line(520, y + h + 3, 520, y + h + 20, th.cyan, 2.4, marker="arrC")
```

Emphasise the core band (e.g. the orchestrator) with `fill="url(#emph)"` and white
text. Use 5–6 bands max. Right rail = `k.card(1000, 112, 230, 566, accent=th.blue)`.

## 2 · Phase / snake flow — "how it runs"

Phase cards with arrows. For >5 phases use a snake: row 1 left→right, elbow down,
row 2 right→left. Colour-code kinds (parent / agent / guard); guards get a dashed
border + cyan.

```python
cw, ch = 270, 122
left = (k.W - (4*cw + 3*22)) / 2
xs = [left + i*(cw+22) for i in range(4)]
def phase(x, y, ph, name, owner, out, hdr, body_fill, dashed=False):
    s  = k.rrect(x, y, cw, ch, 12, body_fill, hdr, 1.8,
                 dash="6 4" if dashed else None, filt="soft")
    s += k.rrect(x, y, cw, 34, 12, hdr) + k.rrect(x, y+22, cw, 12, 0, hdr)
    s += k.T(x+14, y+22, "PHASE "+ph, 12.5, "#ffffff", bold=True)
    s += k.T(x+16, y+60, name, 16.5, th.navy, bold=True)
    s += k.T(x+16, y+83, owner, 11.5, th.muted)
    s += k.Tlines(x+16, y+104, "\u2192 "+out, 11.5, th.blue, 14, cw-30)
    return s
# arrows: k.line(x1, ymid, x2, ymid, th.blue, 2.6, marker="arrB")
# elbow:  k.path(f"M{xc},{y1bottom} L{xc},{y2top}", th.blue, 2.6, marker="arrB")
```

Add a side note callout (light box + accent stripe) for retries/rules, and a slim
KPI/logging band underneath if relevant.

## 3 · Card grid — "roster / inventory"

N items (agents, modules, services) as a 2- or 3-column grid. Header strip with name
+ a status pill; body with one-line role; `in → out` footer chips.

```python
cw, chh, gx, gy = 372, 238, 26, 30
left = (k.W - (3*cw + 2*gx)) / 2
for i, item in enumerate(items):
    x = left + (i % 3)*(cw+gx); y = 122 + (i//3)*(chh+gy)
    body += k.card(x, y, cw, chh, r=13)
    body += k.rrect(x, y, cw, 46, 13, th.navy) + k.rrect(x, y+30, cw, 16, 0, th.navy)
    body += k.T(x+18, y+29, item["name"], 16, "#ffffff", bold=True, mono=True)
    body += k.badge(x+cw-86, y+13, item["tag"], fill=th.cyan, txt=th.navy)  # pill
    body += k.Tlines(x+18, y+100, item["role"], 12.5, th.navy, 17, cw-36)
    body += k.chip(x+40, y+chh-44, item["in"], size=10.5, h=22, mono=True)[0]
    body += k.chip(x+44, y+chh-20, item["out"], size=10.5, h=22,
                   fill=th.tint, stroke=th.cyan, txt=th.blue, mono=True)[0]
```

Keep role text to ≤2 lines. Verify the last row clears the footer.

## 4 · Mapping rows — "X → Y"

One row per item: a fixed left pill (e.g. a command), a purpose line, and right-side
chips (what it triggers). Alternate row tints for rhythm.

```python
rowh, gap, top = 66, 13, 120
for i, r in enumerate(rows):
    y = top + i*(rowh+gap)
    body += k.rrect(60, y, k.W-120, rowh, 11, th.tint if i%2==0 else th.paper,
                    th.line_svg, 1.3, filt="soft")
    body += k.rrect(76, y+rowh/2-17, 142, 34, 9, th.navy)
    body += k.T(76+71, y+rowh/2+5, r["cmd"], 14.5, "#ffffff", "middle", bold=True, mono=True)
    body += k.Tlines(262, y+rowh/2-4, r["purpose"], 12, th.navy, 15, 280)
    x = 560
    for label, kind in r["chips"]:
        fill, stroke, txt = {
            "phase": (th.tint, th.light, th.blue),
            "gate":  (th.pale, th.cyan, th.navy),
            "none":  ("#eef2f5", "#d6e0e7", "#6b7f8e"),
        }[kind]
        m, w = k.chip(x, y+rowh/2-13, label, size=11, h=26, fill=fill, stroke=stroke, txt=txt)
        body += m; x += w + 9
```

## 5 · Themed column cards — "guards / policies / rules"

Group small cards under 3 column headers. Each card: an id badge, a tag (HARD/WARN…),
a title, a wrapped one-liner, and an optional mono reference.

```python
cw, gap = 372, 26
left = (k.W - (3*cw + 2*gap)) / 2
for ci, (title, color, items) in enumerate(columns):
    x = left + ci*(cw+gap)
    body += k.rrect(x, 128, cw, 32, 9, color) + k.T(x+cw/2, 149, title, 14, "#ffffff", "middle", bold=True)
    for ri, it in enumerate(items):
        y = 172 + ri*(112+13)
        body += k.card(x, y, cw, 112, r=11) + k.rrect(x, y, 5, 112, 2.5, color)
        body += k.badge(x+16, y+14, it["id"], fill=th.navy)
        body += k.T(x+74, y+30, it["name"], 14.5, th.navy, bold=True)
        body += k.Tlines(x+18, y+56, it["text"], 11.5, th.muted, 15.5, cw-36)
        if it.get("ref"):
            body += k.T(x+18, y+112-12, it["ref"], 10.5, th.blue, mono=True)
```

## 6 · Node / handoff flow — "data & state"

Horizontal node chain with labelled arrows (the agent/step on the arrow), plus a
central state card and a DB cylinder for stores. Use lanes (chain / state / KPI).

```python
nw, gap = 138, 78
n = len(nodes)
left = (k.W - (n*nw + (n-1)*gap)) / 2
xs = [left + i*(nw+gap) for i in range(n)]
for i, nd in enumerate(nodes):
    body += k.card(xs[i], 156, nw, 74, fill=nd["fill"], stroke=th.light, r=11)
    body += k.T(xs[i]+nw/2, 186, nd["title"], 13, th.navy, "middle", bold=True)
    body += k.T(xs[i]+nw/2, 206, nd["sub"], 9.3, th.muted, "middle", mono=True)
    if i < n-1:
        body += k.line(xs[i]+nw+3, 193, xs[i+1]-3, 193, th.blue, 2.4, marker="arrB")
        body += k.T((xs[i]+nw+xs[i+1])/2, 184, labels[i], 9.6, th.cyan, "middle", bold=True, italic=True)
# DB store:  body += k.cyl(cx, top, 150, 56, th.tint, th.cyan)
```

Keep arrow gaps wider than the longest arrow label so text never overlaps nodes.

---

## Layout math cheatsheet

- centre n columns: `left = (W - (n*cw + (n-1)*gap)) / 2`; `x_i = left + i*(cw+gap)`.
- vertical arrow in a gap: `k.line(cx, y_end+3, cx, y_next-2, th.cyan, 2.4, marker="arrC")`.
- elbow: `k.path("M{x},{y1} L{x},{y2}", th.blue, 2.6, marker="arrB")`.
- a chip auto-sizes; read its width: `m, w = k.chip(x, y, label)`.
- wrap into a width: `k.Tlines(x, y, text, size, fill, line_height, max_width)`.

## Common fixes (seen in QA)

- **Label overlaps a box** → widen the gap or shorten the label.
- **Last grid row hits the footer** → reduce card height or row gap.
- **A callout overlaps cards** → move it into empty margin (top-right) or shift rows.
- **Text overflows a chip** → it won't if you size with `k.chip()`; check manual rects.
- **Redundant legend** → if items are self-labeled, drop the legend.
