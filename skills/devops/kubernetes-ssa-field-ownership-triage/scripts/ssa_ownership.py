#!/usr/bin/env python3
"""Offline inventory for Kubernetes SSA managedFields and conflict text."""

import argparse
import json
import math
import re
import sys
from pathlib import Path

CONFLICT_RE = re.compile(
    r'conflict with ["\'](?P<manager>[^"\']+)["\'](?:\s+using\s+(?P<api>[^:]+))?:\s*(?P<paths>\.[^\n]+)',
    re.IGNORECASE,
)


def reject_constant(value):
    raise ValueError(f"non-standard JSON constant: {value}")


def load_object(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("resource JSON root must be an object")
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("resource metadata must be an object")
    managed = metadata.get("managedFields", [])
    if not isinstance(managed, list):
        raise ValueError("metadata.managedFields must be an array")
    return value, managed


def selector_segment(raw):
    try:
        value = json.loads(raw, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid managedFields selector {raw!r}: {exc}") from exc
    if not isinstance(value, dict) or not value:
        raise ValueError("managedFields k: selector must be a non-empty object")
    pairs = []
    for key in sorted(value):
        item = value[key]
        if isinstance(item, (dict, list)) or (isinstance(item, float) and not math.isfinite(item)):
            raise ValueError("managedFields selector values must be finite scalars")
        pairs.append(f"{key}={json.dumps(item, ensure_ascii=False, separators=(',', ':'))}")
    return "[" + ",".join(pairs) + "]"


def flatten_fields(node, prefix=""):
    if not isinstance(node, dict):
        raise ValueError("fieldsV1 nodes must be objects")
    paths = []
    for key in sorted(node):
        child = node[key]
        if key == ".":
            if child != {}:
                raise ValueError("fieldsV1 '.' marker must contain an empty object")
            if prefix:
                paths.append(prefix)
            continue
        if key.startswith("f:"):
            name = key[2:]
            if not name:
                raise ValueError("empty fieldsV1 field name")
            next_prefix = f"{prefix}.{name}" if prefix else f".{name}"
        elif key.startswith("k:"):
            next_prefix = prefix + selector_segment(key[2:])
        elif key.startswith("i:"):
            index = key[2:]
            if not index.isdigit():
                raise ValueError(f"invalid fieldsV1 list index: {index!r}")
            next_prefix = f"{prefix}[{index}]"
        elif key.startswith("v:"):
            next_prefix = f"{prefix}[value={key[2:]}]"
        else:
            raise ValueError(f"unknown fieldsV1 key prefix: {key!r}")
        if not isinstance(child, dict):
            raise ValueError(f"fieldsV1 child for {key!r} must be an object")
        if child:
            paths.extend(flatten_fields(child, next_prefix))
        else:
            paths.append(next_prefix)
    return sorted(set(paths))


def inventory(path):
    resource, managed = load_object(path)
    rows = []
    for index, entry in enumerate(managed):
        if not isinstance(entry, dict):
            raise ValueError(f"managedFields[{index}] must be an object")
        fields_type = entry.get("fieldsType")
        fields = entry.get("fieldsV1", {})
        if fields_type not in (None, "FieldsV1"):
            raise ValueError(f"unsupported fieldsType at managedFields[{index}]: {fields_type!r}")
        if not isinstance(fields, dict):
            raise ValueError(f"managedFields[{index}].fieldsV1 must be an object")
        rows.append({
            "manager": entry.get("manager", "<unknown>"),
            "operation": entry.get("operation", "<unknown>"),
            "apiVersion": entry.get("apiVersion"),
            "subresource": entry.get("subresource"),
            "time": entry.get("time"),
            "paths": flatten_fields(fields),
        })
    metadata = resource["metadata"]
    return {
        "resource": {
            "apiVersion": resource.get("apiVersion"),
            "kind": resource.get("kind"),
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "resourceVersion": metadata.get("resourceVersion"),
        },
        "managers": rows,
    }


def conflicts(path):
    text = Path(path).read_text(encoding="utf-8")
    findings = []
    for match in CONFLICT_RE.finditer(text):
        paths = [item.strip().rstrip(",") for item in re.split(r",\s*(?=\.)", match.group("paths"))]
        findings.append({"manager": match.group("manager"), "apiVersion": match.group("api"), "paths": paths})
    if not findings:
        raise ValueError("no recognized SSA conflict records found")
    return {"conflicts": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inventory", "conflicts"):
        item = sub.add_parser(name)
        item.add_argument("input")
        item.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inventory(args.input) if args.command == "inventory" else conflicts(args.input)
        json.dump(result, sys.stdout, indent=2 if args.pretty else None, ensure_ascii=False, allow_nan=False)
        sys.stdout.write("\n")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
