#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
svg_kit - reusable primitives for branded, presentation-ready SVG diagrams.

Canvas is 1280x720 (16:9) by default, so each SVG maps 1:1 onto a PowerPoint slide.
Colours are derived from a 5-colour brand palette (darkest -> lightest). Fonts are
system-safe so the SVGs render identically inside PowerPoint.

Typical use from a build script::

    import svg_kit as k
    k.use_palette(["#03045e","#0077b6","#00b4d8","#90e0ef","#caf0f8"])  # optional
    th = k.TH

    body  = k.header("My Architecture", "subtitle here", "1 / 4")
    body += k.rrect(60, 120, 400, 80, 12, th.pale, th.line_svg, 1.4)
    body += k.T(80, 165, "Hello", 18, th.navy, bold=True)
    body += k.footer("light - 16:9 - vector")
    k.save("01_architecture.svg", body, outdir="docs/diagrams")

See references/diagram_patterns.md for full layout recipes.
"""
from dataclasses import dataclass
import os

DEFAULT_PALETTE = ["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"]

# canvas (override via use_palette(..., w=, h=))
W, H = 1280, 720


# ----------------------------------------------------------------- colour ----
def _hex(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mix(c1, c2, t):
    """Blend two hex colours. t=0 -> c1, t=1 -> c2."""
    r1, g1, b1 = _hex(c1)
    r2, g2, b2 = _hex(c2)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return "#%02x%02x%02x" % (r, g, b)


@dataclass
class Theme:
    """Palette-driven colour roles. Build with Theme.from_palette([...])."""
    navy: str   # darkest  - headings, emphasis fills (white text on it)
    blue: str   # mid      - section accents, arrows, links
    cyan: str   # bright   - accents, highlights, guard/dashed elements
    light: str  # light    - chip / box fills
    pale: str   # palest   - backgrounds, subtle fills
    # derived (computed in from_palette)
    ink: str = "#0c2238"
    muted: str = "#5b7488"
    paper: str = "#ffffff"
    tint: str = "#f4fbfe"
    line_svg: str = "#d9eef8"
    header_bg: str = "#f7fcff"
    font: str = "'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
    mono: str = "'Cascadia Code', 'Consolas', 'SF Mono', ui-monospace, monospace"

    @classmethod
    def from_palette(cls, palette=None):
        p = list(palette or DEFAULT_PALETTE)
        while len(p) < 5:                       # pad short palettes
            p.append(DEFAULT_PALETTE[len(p)])
        navy, blue, cyan, light, pale = p[:5]
        return cls(
            navy=navy, blue=blue, cyan=cyan, light=light, pale=pale,
            ink=navy,
            muted=mix(navy, "#ffffff", 0.50),
            paper="#ffffff",
            tint=mix(pale, "#ffffff", 0.55),
            line_svg=mix(navy, "#ffffff", 0.86),
            header_bg=mix(pale, "#ffffff", 0.70),
        )


TH = Theme.from_palette()


def use_palette(palette=None, w=None, h=None):
    """Reset the active theme (and optionally the canvas size)."""
    global TH, W, H
    TH = Theme.from_palette(palette)
    if w:
        W = w
    if h:
        H = h
    return TH


# ------------------------------------------------------------------ text -----
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def tw(s, size, bold=False, mono=False):
    """Approximate text width (px). Padded generously to avoid overflow."""
    f = 0.62 if mono else (0.60 if bold else 0.56)
    return len(str(s)) * size * f


def T(x, y, s, size=13, fill=None, anchor="start", bold=False, mono=False,
      italic=False, ls=None):
    fill = fill or TH.navy
    fam = TH.mono if mono else TH.font
    wt = 700 if bold else 400
    extra = ""
    if italic:
        extra += ' font-style="italic"'
    if ls is not None:
        extra += f' letter-spacing="{ls}"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{wt}"{extra}>{esc(s)}</text>')


def wrap(s, size, maxw, bold=False, mono=False):
    words, lines, cur = str(s).split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(t, size, bold, mono) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def Tlines(x, y, s, size, fill, lh, maxw, anchor="start", bold=False, mono=False,
           italic=False):
    out = []
    for i, ln in enumerate(wrap(s, size, maxw, bold, mono)):
        out.append(T(x, y + i * lh, ln, size, fill, anchor, bold, mono, italic))
    return "".join(out)


# ----------------------------------------------------------------- shapes ----
def rrect(x, y, w, h, r, fill, stroke="none", sw=0.0, dash=None, opacity=None, filt=None):
    s = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
         f'rx="{r:.1f}" ry="{r:.1f}" fill="{fill}"')
    if stroke != "none":
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    if filt:
        s += f' filter="url(#{filt})"'
    return s + "/>"


def line(x1, y1, x2, y2, stroke, sw=1.5, dash=None, marker=None, cap="round"):
    s = (f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" fill="none" '
         f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if marker:
        s += f' marker-end="url(#{marker})"'
    return s + "/>"


def path(d, stroke, sw=1.6, fill="none", dash=None, marker=None):
    s = (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
         f'stroke-linejoin="round" stroke-linecap="round"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if marker:
        s += f' marker-end="url(#{marker})"'
    return s + "/>"


def cyl(cx, top, w, h, fill, stroke, sw=1.6):
    """A database cylinder centred on cx, starting at y=top."""
    rx, ry = w / 2, 9
    left, right, bot = cx - rx, cx + rx, top + h
    body = (f'<path d="M{left:.1f},{top:.1f} L{left:.1f},{bot:.1f} '
            f'A{rx:.1f},{ry:.1f} 0 0 0 {right:.1f},{bot:.1f} '
            f'L{right:.1f},{top:.1f} Z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    topell = (f'<ellipse cx="{cx:.1f}" cy="{top:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
              f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    return body + topell


# ------------------------------------------------------------- components ----
def chip(x, y, label, size=12.5, h=30, fill=None, stroke=None, txt=None, bold=False,
         mono=False, sw=1.4, padx=13, r=None):
    """A pill/chip auto-sized to its text. Returns (markup, width)."""
    fill = TH.paper if fill is None else fill
    stroke = TH.light if stroke is None else stroke
    txt = TH.navy if txt is None else txt
    w = tw(label, size, bold, mono) + 2 * padx
    rad = (h / 2) if r is None else r
    m = rrect(x, y, w, h, rad, fill, stroke, sw)
    m += T(x + w / 2, y + h / 2 + size * 0.34, label, size, txt, "middle", bold, mono)
    return m, w


def chip_row(x0, y, labels, gap=12, **kw):
    """Lay chips left-to-right. Returns (markup, total_width)."""
    out, x = [], x0
    for lb in labels:
        m, w = chip(x, y, lb, **kw)
        out.append(m)
        x += w + gap
    return "".join(out), (x - gap - x0 if labels else 0)


def badge(x, y, label, fill=None, txt="#ffffff", size=11, h=20, padx=9, bold=True, r=None):
    fill = TH.navy if fill is None else fill
    return chip(x, y, label, size=size, h=h, fill=fill, stroke="none", txt=txt,
                bold=bold, sw=0, padx=padx, r=(h / 2 if r is None else r))[0]


def card(x, y, w, h, fill=None, stroke=None, sw=1.5, r=14, accent=None, filt="soft"):
    """A rounded card, optional left accent stripe. Returns markup."""
    fill = TH.paper if fill is None else fill
    stroke = TH.line_svg if stroke is None else stroke
    m = rrect(x, y, w, h, r, fill, stroke, sw, filt=filt)
    if accent:
        m += rrect(x, y + 8, 6, h - 16, 3, accent)
    return m


# ----------------------------------------------------------------- frame -----
def defs():
    th = TH
    return f'''<defs>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{th.navy}"/><stop offset="0.5" stop-color="{th.blue}"/><stop offset="1" stop-color="{th.cyan}"/>
  </linearGradient>
  <linearGradient id="emph" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{th.blue}"/><stop offset="1" stop-color="{mix(th.blue, th.cyan, 0.5)}"/>
  </linearGradient>
  <filter id="soft" x="-10%" y="-10%" width="120%" height="125%">
    <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="{th.navy}" flood-opacity="0.10"/>
  </filter>
  <marker id="arrB" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{th.blue}"/></marker>
  <marker id="arrC" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{th.cyan}"/></marker>
  <marker id="arrN" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{th.navy}"/></marker>
  <marker id="arrS" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{th.muted}"/></marker>
</defs>'''


def header(title, subtitle, idx="", title_size=27):
    """Standard top band: accent rule, title, subtitle, palette strip, divider."""
    th = TH
    s = [rrect(0, 0, W, H, 0, th.paper),
         rrect(0, 0, W, 104, 0, th.header_bg),
         f'<rect x="0" y="0" width="{W}" height="6" fill="url(#accent)"/>']
    px = W - 60 - 5 * 20
    for i, c in enumerate([th.navy, th.blue, th.cyan, th.light, th.pale]):
        s.append(rrect(px + i * 20, 30, 16, 16, 3, c, th.line_svg, 1))
    if idx:
        s.append(T(W - 60, 70, idx, 12, th.muted, "end"))
    s.append(rrect(60, 34, 7, 40, 3.5, th.cyan))
    s.append(T(80, 56, title, title_size, th.navy, "start", bold=True))
    s.append(T(80, 83, subtitle, 14.5, th.muted))
    s.append(line(60, 100, W - 60, 100, th.line_svg, 1.4))
    return "".join(s)


def footer(note="", brand="Codebase \u2192 Diagrams"):
    th = TH
    s = [line(60, H - 38, W - 60, H - 38, th.line_svg, 1.2),
         T(60, H - 18, brand, 12, th.muted, bold=True)]
    if note:
        s.append(T(W - 60, H - 18, note, 12, th.muted, "end"))
    return "".join(s)


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{TH.font}">\n{defs()}\n{body}\n</svg>\n')


def save(name, body, outdir="docs/diagrams"):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg(body))
    print("wrote", p)
    return p
