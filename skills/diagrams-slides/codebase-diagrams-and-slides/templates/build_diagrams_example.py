#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worked example: build two branded diagrams with svg_kit.

Run it to see the toolkit work, then copy this file to docs/diagrams/build_diagrams.py
and adapt it to the target codebase. Pass an output dir as the first arg.

    python -X utf8 build_diagrams_example.py [out_dir]

Patterns shown: (1) layered bands and (3) card grid. See
references/diagram_patterns.md for the rest.
"""
import os
import sys

# make svg_kit importable from the sibling scripts/ folder
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import svg_kit as k  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "_example_out")

k.use_palette(["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"])
th = k.TH


def layered():
    b = k.header("Example \u2014 Layered Architecture",
                 "A 4-band overview generated with svg_kit", "1 / 2  \u00b7  Architecture")
    bands = [
        ("Clients", "who calls in", th.cyan, ["Web UI", "CLI", "API consumers"]),
        ("Services", "application layer", th.blue, ["auth", "orders", "billing", "search"]),
        ("Core", "domain + rules", th.navy, ["domain model", "use-cases", "validation"]),
        ("Data", "persistence", th.cyan, ["Postgres", "Redis", "Object store"]),
    ]
    y = 120
    for i, (label, sub, accent, items) in enumerate(bands):
        h = 110
        emph = (label == "Core")
        b += k.card(60, y, 1160, h, fill=("url(#emph)" if emph else th.tint),
                    accent=(th.navy if emph else accent))
        tcol = "#ffffff" if emph else th.navy
        scol = th.pale if emph else th.muted
        b += k.T(86, y + h/2 - 4, label, 16, tcol, bold=True)
        b += k.T(86, y + h/2 + 16, sub, 10.5, scol)
        chip_kw = dict(fill=(th.paper if not emph else th.pale), stroke=th.light,
                       txt=th.navy, size=12.5, h=30)
        row, _ = k.chip_row(280, y + h/2 - 15, items, gap=12, **chip_kw)
        b += row
        if i < len(bands) - 1:
            b += k.line(640, y + h + 2, 640, y + h + 18, th.cyan, 2.4, marker="arrC")
        y += h + 20
    b += k.footer("example \u00b7 pattern 1")
    return b


def roster():
    b = k.header("Example \u2014 Service Roster",
                 "A 3-column card grid generated with svg_kit", "2 / 2  \u00b7  Services")
    items = [
        ("auth-svc", "Go", "Issues and verifies JWT sessions for every request.", "request", "session"),
        ("orders-svc", "Java", "Owns the order lifecycle and state machine.", "cart", "order"),
        ("billing-svc", "Python", "Charges, invoices and reconciles payments.", "order", "invoice"),
        ("search-svc", "Rust", "Indexes catalogue data and serves queries fast.", "catalogue", "results"),
        ("notify-svc", "Node", "Fans out email / push events to customers.", "events", "messages"),
        ("audit-svc", "Go", "Persists an immutable trail of every action.", "events", "audit log"),
    ]
    cw, chh, gx, gy = 372, 230, 26, 30
    left = (k.W - (3 * cw + 2 * gx)) / 2
    top = 122
    for i, (name, tag, role, sin, sout) in enumerate(items):
        x = left + (i % 3) * (cw + gx)
        y = top + (i // 3) * (chh + gy)
        b += k.card(x, y, cw, chh, r=13)
        b += k.rrect(x, y, cw, 46, 13, th.navy) + k.rrect(x, y + 30, cw, 16, 0, th.navy)
        b += k.T(x + 18, y + 29, name, 16, "#ffffff", bold=True, mono=True)
        b += k.badge(x + cw - k.tw(tag, 10.5, True) - 32, y + 13, tag, fill=th.cyan, txt=th.navy)
        b += k.Tlines(x + 18, y + 90, role, 12.5, th.navy, 17, cw - 36)
        fy = y + chh - 48
        b += k.line(x + 14, fy - 8, x + cw - 14, fy - 8, th.line_svg, 1.1)
        b += k.T(x + 18, fy + 10, "in", 10, th.muted, bold=True)
        b += k.chip(x + 42, fy, sin, size=10.5, h=22, mono=True, padx=9)[0]
        b += k.T(x + 18, fy + 34, "out", 10, th.muted, bold=True)
        b += k.chip(x + 46, fy + 24, sout, size=10.5, h=22, fill=th.tint,
                    stroke=th.cyan, txt=th.blue, mono=True, padx=9)[0]
    b += k.footer("example \u00b7 pattern 3")
    return b


if __name__ == "__main__":
    k.save("example_01_architecture.svg", layered(), outdir=OUT)
    k.save("example_02_roster.svg", roster(), outdir=OUT)
    print("done ->", OUT)
