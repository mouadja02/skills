#!/usr/bin/env python3
"""Detect high-risk information loss in durable context rewrites."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TOKEN_PATTERNS = {
    "commands": re.compile(r"`([^`]+)`"),
    "paths": re.compile(r"\b[\w.-]+(?:/|\\)[\w./\\.-]+\b"),
    "urls": re.compile(r"https?://[^\s)]+"),
    "metrics": re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|ms|s|x|tokens|requests|QPS|GiB|MiB)\b"),
    "ids": re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b"),
}


def extract(text: str) -> dict[str, set[str]]:
    return {name: set(pattern.findall(text)) for name, pattern in TOKEN_PATTERNS.items()}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: context_update_guard.py OLD.md NEW.md", file=sys.stderr)
        return 2

    old = Path(sys.argv[1]).read_text(encoding="utf-8")
    new = Path(sys.argv[2]).read_text(encoding="utf-8")
    old_items = extract(old)
    new_items = extract(new)

    failed = False
    for name, values in old_items.items():
        dropped = sorted(values - new_items[name])
        if not dropped:
            continue
        failed = True
        print(f"\nDropped {name}:")
        for item in dropped[:50]:
            print(f"  - {item}")
        if len(dropped) > 50:
            print(f"  ... {len(dropped) - 50} more")

    if failed:
        print("\nReview required: preserve, supersede, or document why each dropped item is obsolete.")
        return 1

    print("No high-signal context tokens dropped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
