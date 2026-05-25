#!/usr/bin/env python3
"""Add attribution to Qdrant sub-skill files that were missed."""
import os, re

QDRANT_SRC = "https://github.com/qdrant/skills"
QDRANT_ATTR = "qdrant/skills"
QDRANT_CREATOR_URL = "https://qdrant.tech"
QDRANT_CREATOR = "Qdrant"

MISSED = [
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-monitoring\debugging\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-monitoring\setup\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-performance-optimization\indexing-performance-optimization\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-performance-optimization\memory-usage-optimization\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-performance-optimization\search-speed-optimization\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\minimize-latency\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-data-volume\horizontal-scaling\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-data-volume\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-data-volume\sliding-time-window\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-data-volume\tenant-scaling\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-data-volume\vertical-scaling\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-qps\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-scaling\scaling-query-volume\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-search-quality\diagnosis\SKILL.md",
    r"C:\Users\mouad\Desktop\skills\skills\llm-tooling\qdrant-search-quality\search-strategies\SKILL.md",
]

blockquote = (f'\n> **Attribution:** Sourced from '
              f'[{QDRANT_ATTR}]({QDRANT_SRC}) by '
              f'[{QDRANT_CREATOR}]({QDRANT_CREATOR_URL}).\n')

for path in MISSED:
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    if "source:" in content:
        print(f"SKIP: {path}")
        continue
    fm_match = re.match(r'^(---\n)(.*?\n)(---\n)', content, re.DOTALL)
    if not fm_match:
        print(f"NO FM: {path}")
        continue
    fm_open = fm_match.group(1)
    fm_body = fm_match.group(2)
    fm_close = fm_match.group(3)
    rest = content[fm_match.end():]
    new_fm = (fm_open + fm_body
              + f'source: "{QDRANT_SRC}"\n'
              + f'attribution: "{QDRANT_ATTR} by {QDRANT_CREATOR}"\n'
              + fm_close)
    new_content = new_fm + blockquote + ('' if rest.startswith('\n') else '\n') + rest
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"OK: {os.path.basename(os.path.dirname(path))}/SKILL.md")
