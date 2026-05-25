#!/usr/bin/env python3
"""Add attribution to all Alireza Rezvani skills that lack top-level source:"""
import os, re, subprocess

SRC = "https://github.com/alirezarezvani/claude-skills"
ATTR = "alirezarezvani/claude-skills"
CREATOR_URL = "https://github.com/alirezarezvani"
CREATOR = "Alireza Rezvani"

BASE = r"C:\Users\mouad\Desktop\skills\skills"

blockquote = (f'\n> **Attribution:** Sourced from '
              f'[{ATTR}]({SRC}) by '
              f'[{CREATOR}]({CREATOR_URL}).\n')

updated = 0
skipped = 0

for root, dirs, files in os.walk(BASE):
    for fname in files:
        if fname != "SKILL.md":
            continue
        path = os.path.join(root, fname)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception:
                print(f"SKIP (encoding error): {path}")
                skipped += 1
                continue

        # Must have Alireza/Reza Rezvani author
        if not re.search(r'author: (?:Alireza|Reza) Rezvani', content):
            continue

        # Skip if already has top-level source:
        if re.search(r'^source:', content, re.MULTILINE):
            skipped += 1
            continue

        fm_match = re.match(r'^(---\n)(.*?\n)(---\n)', content, re.DOTALL)
        if not fm_match:
            print(f"NO FM: {path}")
            skipped += 1
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
        print(f"OK: {os.path.relpath(path, BASE)}")
        updated += 1

print(f"\nDone. Updated: {updated}, Skipped: {skipped}")
