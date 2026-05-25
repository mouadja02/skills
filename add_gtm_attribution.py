#!/usr/bin/env python3
"""Add standard source/attribution fields to GTM skills that have metadata.source instead."""
import os, re, glob

SRC = "https://github.com/beingsmit/technical-product-gtm"
ATTR = "beingsmit/technical-product-gtm"
CREATOR_URL = "https://linkedin.com/in/smitkpatel"
CREATOR = "Smit Patel"

blockquote = (f'\n> **Attribution:** Sourced from '
              f'[{ATTR}]({SRC}) by '
              f'[{CREATOR}]({CREATOR_URL}).\n')

GTM_DIR = r"C:\Users\mouad\Desktop\skills\skills\go-to-market"

for skill_dir in os.listdir(GTM_DIR):
    path = os.path.join(GTM_DIR, skill_dir, "SKILL.md")
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Already has top-level source:
    # We check for "^source:" at top level (not indented)
    if re.search(r'^source:', content, re.MULTILINE):
        print(f"SKIP (top-level source exists): {skill_dir}")
        continue

    # These have metadata.source - add proper top-level source
    fm_match = re.match(r'^(---\n)(.*?\n)(---\n)', content, re.DOTALL)
    if not fm_match:
        print(f"NO FM: {skill_dir}")
        continue

    fm_open = fm_match.group(1)
    fm_body = fm_match.group(2)
    fm_close = fm_match.group(3)
    rest = content[fm_match.end():]

    new_fm = (fm_open + fm_body
              + f'source: "{SRC}"\n'
              + f'attribution: "{ATTR} by {CREATOR}"\n'
              + fm_close)

    new_content = new_fm + blockquote + ('' if rest.startswith('\n') else '\n') + rest

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"OK: {skill_dir}")
