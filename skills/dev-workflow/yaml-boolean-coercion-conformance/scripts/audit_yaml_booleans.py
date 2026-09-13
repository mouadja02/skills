#!/usr/bin/env python3
"""Bounded lexical audit for YAML 1.1 boolean spellings."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
LEGACY = {"y", "yes", "n", "no", "on", "off"}
STABLE = {"true", "false"}
WORD = re.compile(r"[A-Za-z]+")


class AuditError(Exception):
    pass


def _visible_line(raw: str, line_no: int) -> tuple[str, list[int]]:
    chars = list(raw)
    depths = [0] * len(chars)
    depth = 0
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(chars):
        ch = chars[i]
        depths[i] = depth
        if quote == '"':
            chars[i] = " "
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quote = None
            i += 1
            continue
        if quote == "'":
            chars[i] = " "
            if ch == "'":
                if i + 1 < len(chars) and chars[i + 1] == "'":
                    chars[i + 1] = " "
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            chars[i] = " "
        elif ch == "#" and (i == 0 or raw[i - 1].isspace()):
            for j in range(i, len(chars)):
                chars[j] = " "
            break
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth = max(0, depth - 1)
        i += 1
    if quote is not None:
        raise AuditError(f"line {line_no}: unterminated quoted scalar")
    return "".join(chars), depths


def _is_block_marker(visible: str) -> bool:
    text = visible.strip()
    return bool(re.search(r"(?:^|:\s+|-\s+)[|>][+-]?[1-9]?$", text))


def audit(text: str) -> dict[str, object]:
    if "\x00" in text:
        raise AuditError("NUL byte is not supported")
    findings: list[dict[str, object]] = []
    flow_balance: list[str] = []
    block_parent_indent: int | None = None
    lines = text.splitlines()
    for line_no, raw in enumerate(lines, 1):
        leading = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in leading:
            raise AuditError(f"line {line_no}: tab indentation is not supported")
        indent = len(leading)
        if block_parent_indent is not None:
            if not raw.strip() or indent > block_parent_indent:
                continue
            block_parent_indent = None
        visible, depths = _visible_line(raw, line_no)
        # Validate flow delimiters across lines independently of candidate matching.
        quote_free = visible
        for ch in quote_free:
            if ch in "[{":
                flow_balance.append(ch)
            elif ch in "]}":
                wanted = "[" if ch == "]" else "{"
                if not flow_balance or flow_balance[-1] != wanted:
                    raise AuditError(f"line {line_no}: unmatched {ch!r}")
                flow_balance.pop()
        if _is_block_marker(visible):
            block_parent_indent = indent
        for match in WORD.finditer(visible):
            spelling = match.group(0)
            lowered = spelling.lower()
            if lowered not in LEGACY and lowered not in STABLE:
                continue
            start, end = match.span()
            p = start - 1
            while p >= 0 and visible[p].isspace():
                p -= 1
            n = end
            while n < len(visible) and visible[n].isspace():
                n += 1
            prev = visible[p] if p >= 0 else None
            nxt = visible[n] if n < len(visible) else None
            depth = depths[start] if start < len(depths) else 0
            left_ok = prev is None or prev in "[{,:?"
            if prev == "-":
                left_ok = not visible[:p].strip()
            if prev == ":" and depth == 0 and p == start - 1:
                left_ok = False
            right_ok = nxt is None or nxt in "]},:"
            if not (left_ok and right_ok):
                continue
            role = "key" if nxt == ":" else "value"
            findings.append(
                {
                    "line": line_no,
                    "column": start + 1,
                    "spelling": spelling,
                    "role": role,
                    "kind": "legacy_only_boolean" if lowered in LEGACY else "stable_boolean",
                    "yaml_1_1_type": "boolean",
                    "yaml_1_2_core_type": "string" if lowered in LEGACY else "boolean",
                }
            )
    if flow_balance:
        raise AuditError("unclosed flow collection")
    legacy_count = sum(f["kind"] == "legacy_only_boolean" for f in findings)
    return {
        "schema_version": 1,
        "classification": "yaml_boolean_audit",
        "finding_count": len(findings),
        "legacy_only_count": legacy_count,
        "conformant": legacy_count == 0,
        "findings": findings,
    }


def _write_report(report: dict[str, object], output: str | None) -> None:
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    try:
        if output:
            Path(output).write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
            sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"report write failed: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="YAML file to inspect without construction")
    parser.add_argument("--output", help="write JSON report to this path")
    args = parser.parse_args()
    try:
        path = Path(args.input)
        size = path.stat().st_size
        if size > MAX_BYTES:
            raise AuditError(f"input exceeds {MAX_BYTES} bytes")
        data = path.read_bytes()
        text = data.decode("utf-8", errors="strict")
        report = audit(text)
    except (OSError, UnicodeError, AuditError) as exc:
        print(json.dumps({"schema_version": 1, "error": str(exc)}), file=sys.stderr)
        return 2
    try:
        _write_report(report, args.output)
    except AuditError as exc:
        print(json.dumps({"schema_version": 1, "error": str(exc)}), file=sys.stderr)
        return 3
    return 1 if report["legacy_only_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
