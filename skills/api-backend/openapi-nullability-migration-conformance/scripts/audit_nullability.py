#!/usr/bin/env python3
"""Offline OpenAPI 3.0/3.1 nullability inventory. Never rewrites input."""
from __future__ import annotations
import argparse, json, math, sys
from typing import Any

SCHEMA_CHILDREN = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas")
COMPOSITIONS = ("allOf", "anyOf", "oneOf", "prefixItems")

def ptr(parts: list[str]) -> str:
    return "#" + "".join("/" + x.replace("~", "~0").replace("/", "~1") for x in parts)

def finite_tree(value: Any) -> bool:
    if isinstance(value, float): return math.isfinite(value)
    if isinstance(value, list): return all(finite_tree(v) for v in value)
    if isinstance(value, dict): return all(isinstance(k, str) and finite_tree(v) for k, v in value.items())
    return True

def allows_null(schema: dict[str, Any], dialect: str) -> bool:
    t = schema.get("type")
    typed = t == "null" or (isinstance(t, list) and "null" in t)
    if dialect == "3.0" and schema.get("nullable") is True and isinstance(t, str): typed = True
    branches = schema.get("anyOf") or schema.get("oneOf")
    composed = isinstance(branches, list) and any(isinstance(x, dict) and allows_null(x, dialect) for x in branches)
    return typed or composed

def audit(doc: Any) -> dict[str, Any]:
    if not isinstance(doc, dict): raise ValueError("top-level input must be an object")
    if not finite_tree(doc): raise ValueError("non-finite numbers are not allowed")
    version = doc.get("openapi")
    if not isinstance(version, str): raise ValueError("openapi must be a string")
    if version.startswith("3.0."): dialect = "3.0"
    elif version.startswith("3.1."): dialect = "3.1"
    else: raise ValueError("only OpenAPI 3.0.x and 3.1.x are supported")
    findings: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    schemas = doc.get("components", {}).get("schemas", {}) if isinstance(doc.get("components"), dict) else {}
    if not isinstance(schemas, dict): raise ValueError("components.schemas must be an object")

    def add(code: str, severity: str, path: list[str], message: str) -> None:
        findings.append({"code": code, "severity": severity, "pointer": ptr(path), "message": message})

    def visit(schema: Any, path: list[str], required: bool | None = None) -> None:
        if not isinstance(schema, dict):
            add("SCHEMA_NOT_OBJECT", "error", path, "schema position must contain an object")
            return
        t = schema.get("type")
        if isinstance(t, list):
            if not t or any(not isinstance(x, str) for x in t) or len(set(t)) != len(t):
                add("TYPE_ARRAY_INVALID", "error", path + ["type"], "type array must contain unique strings")
            if dialect == "3.0": add("TYPE_ARRAY_NOT_OAS30", "error", path + ["type"], "OpenAPI 3.0 type must be a single string")
        elif t is not None and not isinstance(t, str):
            add("TYPE_INVALID", "error", path + ["type"], "type must be a string, or an array in OpenAPI 3.1")
        nullable = schema.get("nullable")
        if nullable is not None and not isinstance(nullable, bool):
            add("NULLABLE_NOT_BOOLEAN", "error", path + ["nullable"], "nullable must be boolean")
        if dialect == "3.1" and "nullable" in schema:
            add("NULLABLE_KEYWORD_OAS31", "error", path + ["nullable"], "nullable is not an OpenAPI 3.1 Schema Object keyword; use a JSON Schema null union")
        if dialect == "3.0" and nullable is True:
            if "$ref" in schema:
                add("NULLABLE_REF_SIBLING_IGNORED", "error", path, "a Reference Object cannot be made nullable by a sibling in OpenAPI 3.0")
            elif not isinstance(t, str):
                add("NULLABLE_WITHOUT_LOCAL_TYPE", "warning", path, "OpenAPI 3.0 nullable only modifies a type defined in this Schema Object; composition behavior is not portable")
        if isinstance(schema.get("enum"), list) and None in schema["enum"] and not allows_null(schema, dialect):
            add("ENUM_NULL_WITHOUT_NULL_TYPE", "error", path + ["enum"], "enum contains null but the schema does not allow the null type")
        if required is not None:
            states.append({"pointer": ptr(path), "required": required, "nullable": allows_null(schema, dialect), "missing_allowed": not required, "null_allowed": allows_null(schema, dialect)})
        req = schema.get("required", [])
        if req is not None and (not isinstance(req, list) or any(not isinstance(x, str) for x in req) or len(set(req)) != len(req)):
            add("REQUIRED_INVALID", "error", path + ["required"], "required must be an array of unique strings")
            reqset: set[str] = set()
        else: reqset = set(req or [])
        props = schema.get("properties", {})
        if props is not None and not isinstance(props, dict):
            add("PROPERTIES_INVALID", "error", path + ["properties"], "properties must be an object")
        elif isinstance(props, dict):
            for name, child in props.items(): visit(child, path + ["properties", name], name in reqset)
        for key in SCHEMA_CHILDREN[1:]:
            childmap = schema.get(key)
            if childmap is not None:
                if not isinstance(childmap, dict): add("SCHEMA_MAP_INVALID", "error", path + [key], f"{key} must be an object")
                else:
                    for name, child in childmap.items(): visit(child, path + [key, name])
        for key in COMPOSITIONS:
            children = schema.get(key)
            if children is not None:
                if not isinstance(children, list) or not children: add("COMPOSITION_INVALID", "error", path + [key], f"{key} must be a non-empty array")
                else:
                    for i, child in enumerate(children): visit(child, path + [key, str(i)])
        for key in ("items", "not", "contains", "if", "then", "else", "additionalProperties"):
            child = schema.get(key)
            if isinstance(child, dict): visit(child, path + [key])

    for name, schema in schemas.items(): visit(schema, ["components", "schemas", name])

    # Every non-component Schema Object in OpenAPI is reached through a
    # field named "schema" (parameters, headers, media types, callbacks, and
    # path operations). Keep this discovery separate from Schema Object
    # recursion so a property literally named "schema" is not double-counted.
    def discover(value: Any, path: list[str]) -> None:
        if path == ["components", "schemas"]:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = path + [key]
                if key == "schema": visit(child, child_path)
                else: discover(child, child_path)
        elif isinstance(value, list):
            for i, child in enumerate(value): discover(child, path + [str(i)])

    discover(doc, [])
    findings.sort(key=lambda x: (x["pointer"], x["code"]))
    states.sort(key=lambda x: x["pointer"])
    return {"schema_version": 1, "offline": True, "input_openapi": version, "dialect": dialect, "modified": False, "summary": {"schemas": len(schemas), "properties": len(states), "errors": sum(x["severity"] == "error" for x in findings), "warnings": sum(x["severity"] == "warning" for x in findings)}, "property_states": states, "findings": findings}

def parse(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"invalid JSON constant {x}")))

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("input"); ns = ap.parse_args(argv)
    try:
        report = audit(parse(ns.input))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr); return 2
    try:
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"); sys.stdout.flush()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"output error: {exc}", file=sys.stderr); return 3
    return 1 if report["summary"]["errors"] else 0
if __name__ == "__main__": raise SystemExit(main())
