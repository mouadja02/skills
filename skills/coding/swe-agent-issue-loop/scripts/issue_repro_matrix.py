#!/usr/bin/env python3
"""Create a reproducibility matrix from issue or bug-report text."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


COMMAND_RE = re.compile(r"(?m)^(?:\$|>)\s*(.+)$|`([^`\n]*(?:test|pytest|npm|pnpm|yarn|cargo|go test|dotnet)[^`\n]*)`")


def read_text(path: str | None) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def find_commands(text: str) -> list[str]:
    commands: list[str] = []
    for match in COMMAND_RE.finditer(text):
        command = match.group(1) or match.group(2)
        if command and command not in commands:
            commands.append(command.strip())
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", nargs="?", help="Issue text file, or '-' for stdin")
    args = parser.parse_args()

    text = read_text(args.issue)
    commands = find_commands(text)

    print("# Issue Reproducibility Matrix\n")
    print("## Facts To Extract")
    print("- Observed behavior:")
    print("- Expected behavior:")
    print("- Environment:")
    print("- Affected files/modules:")
    print("- Acceptance criteria:\n")

    print("## Candidate Reproduction Commands")
    if commands:
        for command in commands:
            print(f"- `{command}`")
    else:
        print("- Add the smallest failing command before editing.")

    print("\n## Verification Ladder")
    print("| Step | Command | Expected Signal | Result |")
    print("| --- | --- | --- | --- |")
    first = commands[0] if commands else "<focused failing command>"
    print(f"| Reproduce | `{first}` | Fails before patch | pending |")
    print("| Fix check | `<same command>` | Passes after patch | pending |")
    print("| Regression | `<adjacent test command>` | No nearby breakage | pending |")
    print("| Hygiene | `<lint/type/build if relevant>` | No mechanical regression | pending |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

