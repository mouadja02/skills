#!/usr/bin/env python3
"""Fail-closed JSON duplicate-member analyzer using only the Python standard library."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
WS = " \t\r\n"

class InputError(Exception):
    pass

@dataclass
class Limits:
    max_bytes: int = 1_048_576
    max_depth: int = 128
    max_members: int = 100_000

class Parser:
    def __init__(self, raw: bytes, limits: Limits):
        if len(raw) > limits.max_bytes:
            raise InputError(f"input exceeds max_bytes ({limits.max_bytes})")
        if raw.startswith(b"\xef\xbb\xbf"):
            raise InputError("UTF-8 BOM is not accepted")
        try:
            self.text = raw.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise InputError(f"invalid UTF-8 at byte {exc.start}") from exc
        self.raw = raw
        self.limits = limits
        self.byte_offsets = [0]
        for char in self.text:
            self.byte_offsets.append(self.byte_offsets[-1] + len(char.encode("utf-8")))
        self.i = 0
        self.members = 0
        self.duplicates: list[dict[str, Any]] = []

    def byte_offset(self, char_offset: int) -> int:
        return self.byte_offsets[char_offset]

    @staticmethod
    def pointer(parts: list[str]) -> str:
        return "" if not parts else "/" + "/".join(p.replace("~", "~0").replace("/", "~1") for p in parts)

    @staticmethod
    def ensure_unicode(value: str, at: int) -> None:
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise InputError(f"unpaired Unicode surrogate in string at character {at}")

    def skip_ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i] in WS:
            self.i += 1

    def string(self) -> tuple[str, int]:
        start = self.i
        if self.i >= len(self.text) or self.text[self.i] != '"':
            raise InputError(f"expected string at character {self.i}")
        self.i += 1
        escaped = False
        while self.i < len(self.text):
            ch = self.text[self.i]
            if ord(ch) < 0x20:
                raise InputError(f"unescaped control character at character {self.i}")
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                self.i += 1
                token = self.text[start:self.i]
                try:
                    value = json.loads(token)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise InputError(f"invalid JSON string at character {start}: {exc}") from exc
                self.ensure_unicode(value, start)
                return value, start
            self.i += 1
        raise InputError(f"unterminated string at character {start}")

    def value(self, depth: int, path: list[str]) -> None:
        if depth > self.limits.max_depth:
            raise InputError(f"nesting exceeds max_depth ({self.limits.max_depth})")
        self.skip_ws()
        if self.i >= len(self.text):
            raise InputError(f"expected value at character {self.i}")
        ch = self.text[self.i]
        if ch == "{":
            self.object(depth, path)
        elif ch == "[":
            self.array(depth, path)
        elif ch == '"':
            self.string()
        elif self.text.startswith("true", self.i):
            self.i += 4
        elif self.text.startswith("false", self.i):
            self.i += 5
        elif self.text.startswith("null", self.i):
            self.i += 4
        else:
            match = NUMBER.match(self.text, self.i)
            if not match:
                raise InputError(f"invalid value at character {self.i}")
            token = match.group(0)
            self.i = match.end()
            try:
                number = float(token) if any(c in token for c in ".eE") else int(token)
            except ValueError as exc:
                raise InputError(f"invalid number at character {match.start()}") from exc
            if isinstance(number, float) and not math.isfinite(number):
                raise InputError(f"non-finite number at character {match.start()}")

    def object(self, depth: int, path: list[str]) -> None:
        self.i += 1
        self.skip_ws()
        seen: dict[str, list[int]] = {}
        findings: dict[str, dict[str, Any]] = {}
        if self.i < len(self.text) and self.text[self.i] == "}":
            self.i += 1
            return
        while True:
            self.skip_ws()
            name, start = self.string()
            self.members += 1
            if self.members > self.limits.max_members:
                raise InputError(f"member count exceeds max_members ({self.limits.max_members})")
            offsets = seen.setdefault(name, [])
            offsets.append(start)
            if len(offsets) == 2:
                finding = {
                    "object_path": self.pointer(path),
                    "member_path": self.pointer(path + [name]),
                    "decoded_name": name,
                    "occurrence_char_offsets": offsets.copy(),
                    "occurrence_byte_offsets": [self.byte_offset(x) for x in offsets],
                    "parser_policy_projection": {"first_wins": 1, "last_wins": 2, "preserve_all": [1, 2]},
                }
                self.duplicates.append(finding)
                findings[name] = finding
            elif len(offsets) > 2:
                finding = findings[name]
                finding["occurrence_char_offsets"].append(start)
                finding["occurrence_byte_offsets"].append(self.byte_offset(start))
                finding["parser_policy_projection"]["last_wins"] = len(offsets)
                finding["parser_policy_projection"]["preserve_all"].append(len(offsets))
            self.skip_ws()
            if self.i >= len(self.text) or self.text[self.i] != ":":
                raise InputError(f"expected ':' at character {self.i}")
            self.i += 1
            self.value(depth + 1, path + [name])
            self.skip_ws()
            if self.i < len(self.text) and self.text[self.i] == ",":
                self.i += 1
                continue
            if self.i < len(self.text) and self.text[self.i] == "}":
                self.i += 1
                return
            raise InputError(f"expected ',' or '}}' at character {self.i}")

    def array(self, depth: int, path: list[str]) -> None:
        self.i += 1
        self.skip_ws()
        if self.i < len(self.text) and self.text[self.i] == "]":
            self.i += 1
            return
        index = 0
        while True:
            self.value(depth + 1, path + [str(index)])
            index += 1
            self.skip_ws()
            if self.i < len(self.text) and self.text[self.i] == ",":
                self.i += 1
                continue
            if self.i < len(self.text) and self.text[self.i] == "]":
                self.i += 1
                return
            raise InputError(f"expected ',' or ']' at character {self.i}")

    def analyze(self) -> dict[str, Any]:
        self.skip_ws()
        self.value(0, [])
        self.skip_ws()
        if self.i != len(self.text):
            raise InputError(f"trailing data at character {self.i}")
        blocked = bool(self.duplicates)
        return {
            "schema_version": 1,
            "control": "blocked" if blocked else "ready",
            "valid_json": True,
            "violation": "duplicate_object_member" if blocked else None,
            "duplicate_count": len(self.duplicates),
            "duplicates": self.duplicates,
            "observations": {"members_inspected": self.members, "input_bytes": len(self.raw)},
        }

def analyze_bytes(raw: bytes, limits: Limits | None = None) -> dict[str, Any]:
    try:
        return Parser(raw, limits or Limits()).analyze()
    except InputError as exc:
        return {"schema_version": 1, "control": "blocked", "valid_json": False, "violation": "invalid_or_unprovable_json", "duplicate_count": 0, "duplicates": [], "error": str(exc)}

def write_report(report: dict[str, Any], stream: TextIO) -> None:
    json.dump(report, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
    stream.flush()

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="JSON file path, or - for stdin")
    ap.add_argument("--max-bytes", type=int, default=Limits.max_bytes)
    ap.add_argument("--max-depth", type=int, default=Limits.max_depth)
    ap.add_argument("--max-members", type=int, default=Limits.max_members)
    ns = ap.parse_args(argv)
    if min(ns.max_bytes, ns.max_depth, ns.max_members) < 1:
        ap.error("limits must be positive")
    try:
        raw = sys.stdin.buffer.read(ns.max_bytes + 1) if ns.input == "-" else Path(ns.input).read_bytes()
        report = analyze_bytes(raw, Limits(ns.max_bytes, ns.max_depth, ns.max_members))
        write_report(report, sys.stdout)
    except (OSError, BrokenPipeError) as exc:
        print(f"analyzer I/O failure: {exc}", file=sys.stderr)
        return 3
    return 0 if report["control"] == "ready" else 2

if __name__ == "__main__":
    raise SystemExit(main())
