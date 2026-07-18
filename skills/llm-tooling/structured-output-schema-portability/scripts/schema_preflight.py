#!/usr/bin/env python3
"""Offline JSON Schema preflight for selected LLM structured-output profiles.

No network calls or third-party dependencies. Profiles are conservative snapshots,
not substitutes for a provider's live schema compiler.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

PROFILE_DATES = {
    "generic": "draft-2020-12-structural-only",
    "openai": "2026-07-18",
    "bedrock": "2026-07-18",
    "gemini": "2026-07-07",
    "vllm": "2026-07-18",
}
TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
SCHEMA_MAP_KEYS = {"properties", "$defs", "definitions", "patternProperties", "dependentSchemas"}
SCHEMA_LIST_KEYS = {"allOf", "anyOf", "oneOf", "prefixItems"}
SCHEMA_SINGLE_KEYS = {"items", "contains", "additionalProperties", "propertyNames", "not", "if", "then", "else"}
OPENAI_FORBIDDEN = {"allOf", "not", "dependentRequired", "dependentSchemas", "if", "then", "else"}
BEDROCK_FORBIDDEN = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minLength", "maxLength"}
GEMINI_ALLOWED = {
    "$schema", "type", "title", "description", "properties", "required", "additionalProperties",
    "enum", "format", "minimum", "maximum", "items", "prefixItems", "minItems", "maxItems",
}
ANNOTATIONS = {"title", "description", "$comment", "examples", "default", "deprecated", "readOnly", "writeOnly"}


def pointer(path: tuple[Any, ...]) -> str:
    if not path:
        return "#"
    return "#/" + "/".join(str(x).replace("~", "~0").replace("/", "~1") for x in path)


def iter_nodes(schema: Any, path: tuple[Any, ...] = (), depth: int = 0) -> Iterable[tuple[dict[str, Any], tuple[Any, ...], int]]:
    if not isinstance(schema, dict):
        return
    yield schema, path, depth
    for key in SCHEMA_MAP_KEYS:
        value = schema.get(key)
        if isinstance(value, dict):
            for name, child in value.items():
                if isinstance(child, dict):
                    yield from iter_nodes(child, path + (key, name), depth + 1)
    for key in SCHEMA_LIST_KEYS:
        value = schema.get(key)
        if isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, dict):
                    yield from iter_nodes(child, path + (key, index), depth + 1)
    for key in SCHEMA_SINGLE_KEYS:
        child = schema.get(key)
        if isinstance(child, dict):
            yield from iter_nodes(child, path + (key,), depth + 1)


def issue(level: str, code: str, path: tuple[Any, ...], message: str) -> dict[str, str]:
    return {"level": level, "code": code, "path": pointer(path), "message": message}


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_json_constant)


def resolve_ref(root: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError("external reference")
    value: Any = root
    for raw in ref[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or token not in value:
            raise ValueError("unresolved reference")
        value = value[token]
    return value


def structural_checks(schema: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for node, path, _ in iter_nodes(schema):
        node_type = node.get("type")
        values = node_type if isinstance(node_type, list) else [node_type] if node_type is not None else []
        if not all(isinstance(v, str) and v in TYPES for v in values):
            out.append(issue("error", "invalid-type", path + ("type",), "type must contain only supported JSON Schema primitive names"))
        props = node.get("properties")
        if props is not None and not isinstance(props, dict):
            out.append(issue("error", "invalid-properties", path + ("properties",), "properties must be an object"))
        required = node.get("required")
        if "required" in node:
            if not isinstance(required, list) or not all(isinstance(v, str) for v in required):
                out.append(issue("error", "invalid-required", path + ("required",), "required must be an array of strings"))
            elif isinstance(props, dict):
                for name in required:
                    if name not in props:
                        out.append(issue("error", "unknown-required", path + ("required",), f"required property {name!r} is absent from properties"))
        if "enum" in node and (not isinstance(node["enum"], list) or not node["enum"]):
            out.append(issue("error", "invalid-enum", path + ("enum",), "enum must be a non-empty array"))
        for key in ("anyOf", "allOf", "oneOf"):
            if key in node and (not isinstance(node[key], list) or not node[key] or not all(isinstance(v, dict) for v in node[key])):
                out.append(issue("error", "invalid-composition", path + (key,), f"{key} must be a non-empty array of schemas"))
        for key in ("minItems", "maxItems", "minLength", "maxLength"):
            if key in node and (not isinstance(node[key], int) or isinstance(node[key], bool) or node[key] < 0):
                out.append(issue("error", "invalid-nonnegative-integer", path + (key,), f"{key} must be a non-negative integer"))
        for key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"):
            if key in node and (not isinstance(node[key], (int, float)) or isinstance(node[key], bool)):
                out.append(issue("error", "invalid-number", path + (key,), f"{key} must be numeric"))
        ref = node.get("$ref")
        if ref is not None:
            if not isinstance(ref, str):
                out.append(issue("error", "invalid-ref", path + ("$ref",), "$ref must be a string"))
            else:
                try:
                    resolve_ref(schema, ref)
                except ValueError as exc:
                    out.append(issue("error", "bad-ref", path + ("$ref",), str(exc)))
    return out


def effective_object_depth(node: dict[str, Any], root: dict[str, Any], refs: frozenset[str] = frozenset()) -> int:
    """Return maximum object nesting through applicable schemas and local refs."""
    referenced_depth = 0
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/") and ref not in refs:
        try:
            target = resolve_ref(root, ref)
        except ValueError:
            target = None
        if isinstance(target, dict):
            referenced_depth = effective_object_depth(target, root, refs | {ref})

    children: list[dict[str, Any]] = []
    # Definitions are declarations, not nested output positions; count them only through $ref.
    for key in ("properties", "patternProperties", "dependentSchemas"):
        value = node.get(key)
        if isinstance(value, dict):
            children.extend(v for v in value.values() if isinstance(v, dict))
    for key in SCHEMA_LIST_KEYS:
        value = node.get(key)
        if isinstance(value, list):
            children.extend(v for v in value if isinstance(v, dict))
    for key in SCHEMA_SINGLE_KEYS:
        value = node.get(key)
        if isinstance(value, dict):
            children.append(value)
    own = 1 if node.get("type") == "object" or "properties" in node else 0
    sibling_depth = own + max((effective_object_depth(child, root, refs) for child in children), default=0)
    return max(referenced_depth, sibling_depth)


def profile_checks(schema: dict[str, Any], profile: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    nodes = list(iter_nodes(schema))
    if profile == "openai":
        if schema.get("type") != "object" or "anyOf" in schema:
            out.append(issue("error", "openai-root-object", (), "root must be an object and must not use top-level anyOf"))
        for node, path, _ in nodes:
            for key in OPENAI_FORBIDDEN & node.keys():
                out.append(issue("error", "openai-unsupported", path + (key,), f"{key} is outside the documented strict subset"))
            if node.get("type") == "object" or "properties" in node:
                props = node.get("properties", {})
                if node.get("additionalProperties") is not False:
                    out.append(issue("error", "openai-closed-object", path, "every object must set additionalProperties to false"))
                if isinstance(props, dict):
                    required = node.get("required")
                    required_names = set(required) if isinstance(required, list) and all(isinstance(v, str) for v in required) else set()
                    missing = sorted(set(props) - required_names)
                    if missing:
                        out.append(issue("error", "openai-all-required", path + ("required",), "all properties must be required; missing: " + ", ".join(missing)))
        property_count = sum(len(n.get("properties", {})) for n, _, _ in nodes if isinstance(n.get("properties"), dict))
        max_depth = effective_object_depth(schema, schema)
        if property_count > 5000:
            out.append(issue("error", "openai-property-limit", (), f"{property_count} object properties exceeds 5000"))
        if max_depth > 10:
            out.append(issue("error", "openai-depth-limit", (), f"effective object nesting depth {max_depth} exceeds 10"))
    elif profile == "bedrock":
        for node, path, _ in nodes:
            for key in BEDROCK_FORBIDDEN & node.keys():
                out.append(issue("error", "bedrock-unsupported", path + (key,), f"{key} is outside the documented Bedrock subset"))
            if "additionalProperties" in node and node["additionalProperties"] is not False:
                out.append(issue("error", "bedrock-additional-properties", path + ("additionalProperties",), "Bedrock documents only additionalProperties: false"))
            if (node.get("type") == "object" or "properties" in node) and node.get("additionalProperties") is not False:
                out.append(issue("error", "bedrock-open-object", path, "close each object explicitly with additionalProperties: false"))
            if "minItems" in node and node["minItems"] not in (0, 1):
                out.append(issue("error", "bedrock-min-items", path + ("minItems",), "Bedrock documents minItems values 0 and 1 only"))
            ref = node.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#/"):
                out.append(issue("error", "bedrock-external-ref", path + ("$ref",), "external references are unsupported"))
        out.append(issue("warning", "bedrock-recursion-review", (), "the helper does not prove absence of recursive internal $ref cycles; review referenced definitions"))
    elif profile == "gemini":
        for node, path, _ in nodes:
            for key in node:
                if key not in GEMINI_ALLOWED:
                    level = "warning" if key in ANNOTATIONS else "error"
                    out.append(issue(level, "gemini-unlisted-keyword", path + (key,), f"{key} is not listed in the Gemini structured-output subset snapshot"))
        out.append(issue("warning", "gemini-complexity", (), "the provider documents that very large or deeply nested schemas may be rejected without a fixed public threshold"))
    elif profile == "vllm":
        out.append(issue("warning", "vllm-backend-dependent", (), "vLLM support depends on version, model, and guided-decoding backend; run the exact deployment's compile/request probe"))
    return out


def inventory(schema: dict[str, Any]) -> dict[str, Any]:
    nodes = list(iter_nodes(schema))
    keywords = sorted({key for node, _, _ in nodes for key in node})
    return {
        "schema_nodes": len(nodes),
        "object_properties": sum(len(n.get("properties", {})) for n, _, _ in nodes if isinstance(n.get("properties"), dict)),
        "max_schema_depth": max((d for _, _, d in nodes), default=0),
        "keywords": keywords,
    }


def tighten_objects(value: Any, path: tuple[Any, ...] = (), changes: list[str] | None = None) -> tuple[Any, list[str]]:
    """Close schema object nodes without treating arbitrary mapping values as schemas."""
    if changes is None:
        changes = []
    if not isinstance(value, dict):
        return value, changes
    if (value.get("type") == "object" or "properties" in value) and "additionalProperties" not in value:
        value["additionalProperties"] = False
        changes.append(pointer(path + ("additionalProperties",)))
    for key in SCHEMA_MAP_KEYS:
        mapping = value.get(key)
        if isinstance(mapping, dict):
            for name, child in mapping.items():
                if isinstance(child, dict):
                    tighten_objects(child, path + (key, name), changes)
    for key in SCHEMA_LIST_KEYS:
        sequence = value.get(key)
        if isinstance(sequence, list):
            for index, child in enumerate(sequence):
                if isinstance(child, dict):
                    tighten_objects(child, path + (key, index), changes)
    for key in SCHEMA_SINGLE_KEYS:
        child = value.get(key)
        if isinstance(child, dict):
            tighten_objects(child, path + (key,), changes)
    return value, changes


def is_type(value: Any, expected: str) -> bool:
    if expected == "null": return value is None
    if expected == "boolean": return isinstance(value, bool)
    if expected == "integer": return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number": return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "string": return isinstance(value, str)
    if expected == "array": return isinstance(value, list)
    if expected == "object": return isinstance(value, dict)
    return False


def validate_instance(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$", seen: frozenset[str] = frozenset()) -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or ref in seen:
            return [f"{path}: unresolved or recursive $ref {ref!r}"]
        try: target = resolve_ref(root, ref)
        except ValueError as exc: return [f"{path}: {exc}"]
        errors.extend(validate_instance(value, target, root, path, seen | {ref}))
        schema = {key: item for key, item in schema.items() if key != "$ref"}
    if "const" in schema and value != schema["const"]: errors.append(f"{path}: value does not equal const")
    if isinstance(schema.get("enum"), list) and value not in schema["enum"]: errors.append(f"{path}: value is not in enum")
    declared = schema.get("type")
    types = declared if isinstance(declared, list) else [declared] if isinstance(declared, str) else []
    if types and not any(is_type(value, t) for t in types):
        return errors + [f"{path}: expected type {types}, got {type(value).__name__}"]
    branches = schema.get("anyOf")
    if isinstance(branches, list) and not any(not validate_instance(value, b, root, path, seen) for b in branches if isinstance(b, dict)):
        errors.append(f"{path}: no anyOf branch matched")
    for branch in schema.get("allOf", []) if isinstance(schema.get("allOf"), list) else []:
        if isinstance(branch, dict): errors.extend(validate_instance(value, branch, root, path, seen))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []) if isinstance(schema.get("required"), list) else []:
            if name not in value: errors.append(f"{path}: missing required property {name!r}")
        if isinstance(props, dict):
            for name, child in props.items():
                if name in value and isinstance(child, dict): errors.extend(validate_instance(value[name], child, root, f"{path}.{name}", seen))
            if schema.get("additionalProperties") is False:
                for name in value.keys() - props.keys(): errors.append(f"{path}: unexpected property {name!r}")
    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]: errors.append(f"{path}: fewer than minItems")
        if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]: errors.append(f"{path}: more than maxItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(value): errors.extend(validate_instance(item, item_schema, root, f"{path}[{i}]", seen))
    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]: errors.append(f"{path}: shorter than minLength")
        if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]: errors.append(f"{path}: longer than maxLength")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]: errors.append(f"{path}: below minimum")
        if isinstance(schema.get("maximum"), (int, float)) and value > schema["maximum"]: errors.append(f"{path}: above maximum")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    parser.add_argument("--profile", choices=PROFILE_DATES, default="generic")
    parser.add_argument("--fixture", action="append", default=[], type=Path, help="JSON instance expected to pass the original schema; repeatable")
    parser.add_argument("--invalid-fixture", action="append", default=[], type=Path, help="JSON instance expected to fail the original schema; repeatable")
    parser.add_argument("--write-tightened", type=Path, help="write a copy with missing object additionalProperties set to false")
    parser.add_argument("--report", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        schema = load_json(args.schema)
        if not isinstance(schema, dict): raise ValueError("schema root must be a JSON object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"schema_preflight: {exc}", file=sys.stderr); return 2
    issues = structural_checks(schema) + profile_checks(schema, args.profile)
    fixture_results = []
    fixture_expectations = [(path, True) for path in args.fixture] + [(path, False) for path in args.invalid_fixture]
    for fixture_path, expected_valid in fixture_expectations:
        load_error = None
        try:
            value = load_json(fixture_path)
            errors = validate_instance(value, schema, schema)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            load_error = str(exc)
            errors = []
        observed_valid = not errors if load_error is None else None
        fixture_results.append({
            "path": str(fixture_path),
            "expected_valid": expected_valid,
            "observed_valid": observed_valid,
            "expectation_met": load_error is None and observed_valid == expected_valid,
            "load_error": load_error,
            "errors": errors,
        })
    changes: list[str] = []
    if args.write_tightened:
        candidate, changes = tighten_objects(copy.deepcopy(schema))
        try:
            args.write_tightened.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"schema_preflight: cannot write tightened schema: {exc}", file=sys.stderr); return 2
    report = {
        "profile": args.profile,
        "profile_snapshot": PROFILE_DATES[args.profile],
        "inventory": inventory(schema),
        "issues": issues,
        "fixtures": fixture_results,
        "tightened_changes": changes,
        "result": "fail" if any(x["level"] == "error" for x in issues) or any(not x["expectation_met"] for x in fixture_results) else "pass",
    }
    if args.report == "json": print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"profile={args.profile} snapshot={PROFILE_DATES[args.profile]} result={report['result']}")
        print(f"nodes={report['inventory']['schema_nodes']} properties={report['inventory']['object_properties']} depth={report['inventory']['max_schema_depth']}")
        for item in issues: print(f"{item['level'].upper()} {item['code']} {item['path']}: {item['message']}")
        for item in fixture_results:
            expected = "valid" if item["expected_valid"] else "invalid"
            observed = "unreadable" if item["observed_valid"] is None else "valid" if item["observed_valid"] else "invalid"
            details = [item["load_error"]] if item["load_error"] else item["errors"]
            print(f"FIXTURE {'PASS' if item['expectation_met'] else 'FAIL'} {item['path']} expected={expected} observed={observed}" + (": " + "; ".join(details) if details else ""))
        if changes: print("TIGHTENED " + ", ".join(changes))
    return 1 if report["result"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
