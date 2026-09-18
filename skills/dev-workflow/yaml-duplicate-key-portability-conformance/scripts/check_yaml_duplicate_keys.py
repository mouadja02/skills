#!/usr/bin/env python3
"""Fail-closed duplicate mapping key scanner for YAML representation graphs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

MAX_BYTES = 8 * 1024 * 1024
STANDARD_TAGS = {
    "tag:yaml.org,2002:null",
    "tag:yaml.org,2002:bool",
    "tag:yaml.org,2002:int",
    "tag:yaml.org,2002:float",
    "tag:yaml.org,2002:str",
    "tag:yaml.org,2002:seq",
    "tag:yaml.org,2002:map",
    "tag:yaml.org,2002:merge",
    "tag:yaml.org,2002:timestamp",
    "tag:yaml.org,2002:binary",
    "tag:yaml.org,2002:set",
    "tag:yaml.org,2002:omap",
    "tag:yaml.org,2002:pairs",
}
class InputFailure(Exception):
    pass


def location(node: Node) -> dict[str, int]:
    return {"line": node.start_mark.line + 1, "column": node.start_mark.column + 1}


def scalar_identity(node: ScalarNode) -> tuple[str, Any]:
    loader = yaml.SafeLoader("")
    try:
        value = loader.construct_object(node, deep=True)
    except yaml.YAMLError as exc:
        raise InputFailure(f"unsupported scalar at line {node.start_mark.line + 1}: {exc}") from exc
    finally:
        loader.dispose()
    if isinstance(value, float) and value != value:
        value = ("nonfinite", "nan")
    return ("resolved", value)


def node_identity(node: Node, active: set[int]) -> tuple[Any, ...]:
    if node.tag not in STANDARD_TAGS:
        raise InputFailure(f"unsupported tag {node.tag!r} at line {node.start_mark.line + 1}")
    marker = id(node)
    if marker in active:
        raise InputFailure(f"cyclic alias used as mapping key at line {node.start_mark.line + 1}")
    active.add(marker)
    try:
        if isinstance(node, ScalarNode):
            tag, value = scalar_identity(node)
            return ("scalar", value)
        if isinstance(node, SequenceNode):
            return ("sequence", node.tag, tuple(node_identity(child, active) for child in node.value))
        if isinstance(node, MappingNode):
            pairs = tuple((node_identity(k, active), node_identity(v, active)) for k, v in node.value)
            return ("mapping", node.tag, pairs)
        raise InputFailure(f"unsupported key node at line {node.start_mark.line + 1}")
    finally:
        active.remove(marker)


def display_key(node: Node) -> str:
    if isinstance(node, ScalarNode):
        return node.value
    return f"<{node.id}>"


def walk(node: Node, document: int, path: str, merge_policy: str, findings: list[dict[str, Any]], active: set[int]) -> None:
    marker = id(node)
    if marker in active:
        return
    active.add(marker)
    try:
        if node.tag not in STANDARD_TAGS:
            raise InputFailure(f"unsupported tag {node.tag!r} at line {node.start_mark.line + 1}")
        if isinstance(node, MappingNode):
            seen: dict[tuple[Any, ...], Node] = {}
            for index, (key, value) in enumerate(node.value):
                child_path = f"{path}/<key:{index}>"
                is_merge = isinstance(key, ScalarNode) and key.tag == "tag:yaml.org,2002:merge"
                if is_merge:
                    if merge_policy == "forbid":
                        findings.append({
                            "reason": "merge_key_forbidden",
                            "document": document,
                            "path": path,
                            "key": key.value,
                            "duplicate": location(key),
                            "first": None,
                        })
                else:
                    identity = node_identity(key, set())
                    if identity in seen:
                        first = seen[identity]
                        reason = "duplicate_explicit_key"
                        if isinstance(key, ScalarNode) and isinstance(first, ScalarNode) and (key.value != first.value or key.style != first.style):
                            reason = "duplicate_resolved_key"
                        findings.append({
                            "reason": reason,
                            "document": document,
                            "path": path,
                            "key": display_key(key),
                            "duplicate": location(key),
                            "first": location(first),
                        })
                    else:
                        seen[identity] = key
                walk(key, document, child_path, merge_policy, findings, active)
                value_segment = display_key(key).replace("~", "~0").replace("/", "~1")
                walk(value, document, f"{path}/{value_segment}", merge_policy, findings, active)
        elif isinstance(node, SequenceNode):
            for index, child in enumerate(node.value):
                walk(child, document, f"{path}/{index}", merge_policy, findings, active)
    finally:
        active.remove(marker)


def scan(data: bytes, merge_policy: str) -> dict[str, Any]:
    if b"\x00" in data:
        raise InputFailure("NUL byte is not permitted")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputFailure("input is not valid UTF-8") from exc
    try:
        documents = list(yaml.compose_all(text, Loader=yaml.SafeLoader))
    except yaml.YAMLError as exc:
        raise InputFailure(f"malformed YAML: {exc}") from exc
    findings: list[dict[str, Any]] = []
    for number, document in enumerate(documents, start=1):
        if document is not None:
            walk(document, number, "", merge_policy, findings, set())
    findings.sort(key=lambda item: (item["document"], item["duplicate"]["line"], item["duplicate"]["column"], item["reason"]))
    return {
        "schema_version": 1,
        "kind": "yaml_duplicate_key_report",
        "profile": "pyyaml-safe-loader",
        "merge_policy": merge_policy,
        "document_count": len(documents),
        "finding_count": len(findings),
        "findings": findings,
    }


def write_report(report: dict[str, Any], output: str | None) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        if output:
            with open(output, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
        else:
            sys.stdout.write(payload)
            sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise BrokenPipeError(str(exc)) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="YAML file (.yaml or .yml)")
    parser.add_argument("--merge-policy", choices=("allow", "forbid"), default="forbid")
    parser.add_argument("--output", help="write JSON report to this path")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.input)
    if path.suffix.lower() not in {".yaml", ".yml"}:
        print("error: input must use a .yaml or .yml extension", file=sys.stderr)
        return 2
    if args.max_bytes < 1 or args.max_bytes > MAX_BYTES:
        print(f"error: --max-bytes must be between 1 and {MAX_BYTES}", file=sys.stderr)
        return 2
    try:
        size = path.stat().st_size
        if size > args.max_bytes:
            raise InputFailure(f"input exceeds {args.max_bytes} bytes")
        data = path.read_bytes()
        if len(data) > args.max_bytes:
            raise InputFailure(f"input exceeds {args.max_bytes} bytes")
        report = scan(data, args.merge_policy)
    except (OSError, InputFailure) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        write_report(report, args.output)
    except BrokenPipeError as exc:
        print(f"error: unable to write report: {exc}", file=sys.stderr)
        return 3
    return 1 if report["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
