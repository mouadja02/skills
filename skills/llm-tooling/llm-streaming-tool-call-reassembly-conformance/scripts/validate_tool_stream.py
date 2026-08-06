#!/usr/bin/env python3
"""Fail-closed offline validator for streamed LLM tool-call fragments."""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROFILES = {"openai", "mistral", "anthropic"}
SCHEMA_KEYS = {
    "$schema", "title", "description", "type", "properties", "required",
    "additionalProperties", "enum", "items", "minItems", "maxItems",
    "minimum", "maximum",
}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str


@dataclass
class Call:
    scope: str
    slot: int
    call_id: str | None = None
    name: str | None = None
    fragments: list[str] = field(default_factory=list)
    terminal: bool = False


def reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value}")


def finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"number is outside finite range: {value}")
    return parsed


def strict_loads(value: str) -> Any:
    return json.loads(value, parse_constant=reject_constant, parse_float=finite_float)


def load_document(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=reject_constant, parse_float=finite_float)


def add(findings: list[Finding], code: str, path: str, message: str) -> None:
    findings.append(Finding("error", code, path, message))


def slot_value(value: Any, path: str, findings: list[Finding]) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        add(findings, "invalid_slot", path, "tool-call index must be a non-negative integer")
        return None
    return value


def get_call(calls: dict[str, Call], scope: str, slot: int) -> Call:
    key = f"{scope}/slot:{slot}"
    if key not in calls:
        calls[key] = Call(scope, slot)
    return calls[key]


def merge_identity(call: Call, call_id: Any, name: Any, path: str, findings: list[Finding]) -> None:
    if call_id is not None:
        if not isinstance(call_id, str) or not call_id:
            add(findings, "invalid_call_id", path, "call id must be a non-empty string")
        elif call.call_id is not None and call.call_id != call_id:
            add(findings, "identity_collision", path, f"slot {call.slot} changed id")
        else:
            call.call_id = call_id
    if name is not None:
        if not isinstance(name, str) or not name:
            add(findings, "invalid_tool_name", path, "tool name must be a non-empty string")
        elif call.name is not None and call.name != name:
            add(findings, "identity_collision", path, f"slot {call.slot} changed tool name")
        else:
            call.name = name


def append_fragment(call: Call, value: Any, path: str, findings: list[Finding]) -> None:
    if call.terminal:
        add(findings, "delta_after_terminal", path, f"slot {call.slot} received data after terminal state")
        return
    if value is None:
        return
    if not isinstance(value, str):
        add(findings, "invalid_arguments_delta", path, "arguments delta must be a string")
        return
    call.fragments.append(value)


def terminal(call: Call, path: str, findings: list[Finding]) -> None:
    if call.terminal:
        add(findings, "duplicate_terminal", path, f"slot {call.slot} ended more than once")
    call.terminal = True


def parse_openai_like(document: dict[str, Any], calls: dict[str, Call], findings: list[Finding]) -> bool:
    chunks = document.get("chunks")
    if not isinstance(chunks, list):
        add(findings, "invalid_chunks", "/chunks", "chunks must be an array")
        return False
    applicable = False
    for ci, chunk in enumerate(chunks):
        base = f"/chunks/{ci}"
        if not isinstance(chunk, dict) or not isinstance(chunk.get("choices"), list):
            add(findings, "invalid_chunk", base, "chunk must contain a choices array")
            continue
        for xi, choice in enumerate(chunk["choices"]):
            path = f"{base}/choices/{xi}"
            if not isinstance(choice, dict):
                add(findings, "invalid_choice", path, "choice must be an object")
                continue
            choice_index = slot_value(choice.get("index", xi), f"{path}/index", findings)
            if choice_index is None:
                continue
            scope = f"choice:{choice_index}"
            delta = choice.get("delta", {})
            if not isinstance(delta, dict):
                add(findings, "invalid_delta", f"{path}/delta", "delta must be an object")
                continue
            tool_calls = delta.get("tool_calls")
            if tool_calls is not None:
                applicable = True
                if not isinstance(tool_calls, list):
                    add(findings, "invalid_tool_calls", f"{path}/delta/tool_calls", "tool_calls must be an array")
                else:
                    for ti, item in enumerate(tool_calls):
                        tpath = f"{path}/delta/tool_calls/{ti}"
                        if not isinstance(item, dict):
                            add(findings, "invalid_tool_call", tpath, "tool call delta must be an object")
                            continue
                        slot = slot_value(item.get("index"), f"{tpath}/index", findings)
                        if slot is None:
                            continue
                        call = get_call(calls, scope, slot)
                        kind = item.get("type")
                        if kind not in (None, "function"):
                            add(findings, "unsupported_tool_type", f"{tpath}/type", "only function tool calls are supported")
                        function = item.get("function", {})
                        if not isinstance(function, dict):
                            add(findings, "invalid_function_delta", f"{tpath}/function", "function must be an object")
                            continue
                        merge_identity(call, item.get("id"), function.get("name"), tpath, findings)
                        append_fragment(call, function.get("arguments"), f"{tpath}/function/arguments", findings)
            finish = choice.get("finish_reason")
            if finish is not None:
                scoped = [call for call in calls.values() if call.scope == scope]
                if scoped and finish == "tool_calls":
                    for call in scoped:
                        terminal(call, f"{path}/finish_reason", findings)
                elif scoped:
                    add(findings, "wrong_terminal_reason", f"{path}/finish_reason", "tool-call choice must end with finish_reason=tool_calls")
                elif finish == "tool_calls":
                    add(findings, "terminal_without_call", f"{path}/finish_reason", "choice ended for tool calls without a tool-call delta")
    return applicable


def parse_anthropic(document: dict[str, Any], calls: dict[str, Call], findings: list[Finding]) -> bool:
    events = document.get("events")
    if not isinstance(events, list):
        add(findings, "invalid_events", "/events", "events must be an array")
        return False
    applicable = False
    for ei, event in enumerate(events):
        path = f"/events/{ei}"
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            add(findings, "invalid_event", path, "event must be an object with a type")
            continue
        kind = event["type"]
        if kind == "content_block_start":
            block = event.get("content_block")
            if not isinstance(block, dict):
                add(findings, "invalid_content_block", f"{path}/content_block", "content_block must be an object")
                continue
            if block.get("type") != "tool_use":
                continue
            applicable = True
            slot = slot_value(event.get("index"), f"{path}/index", findings)
            if slot is None:
                continue
            call = get_call(calls, "content-block", slot)
            if call.call_id is not None or call.name is not None or call.fragments:
                add(findings, "duplicate_start", path, f"slot {slot} started more than once")
            merge_identity(call, block.get("id"), block.get("name"), path, findings)
            initial = block.get("input", {})
            if initial not in ({}, None):
                add(findings, "unsupported_initial_input", f"{path}/content_block/input", "non-empty initial tool input cannot be combined safely with partial_json")
        elif kind == "content_block_delta":
            delta = event.get("delta")
            if not isinstance(delta, dict) or delta.get("type") != "input_json_delta":
                continue
            applicable = True
            slot = slot_value(event.get("index"), f"{path}/index", findings)
            if slot is None:
                continue
            key = f"content-block/slot:{slot}"
            if key not in calls:
                add(findings, "delta_before_start", path, f"slot {slot} received a delta before tool_use start")
            call = get_call(calls, "content-block", slot)
            append_fragment(call, delta.get("partial_json"), f"{path}/delta/partial_json", findings)
        elif kind == "content_block_stop":
            slot = slot_value(event.get("index"), f"{path}/index", findings)
            key = f"content-block/slot:{slot}"
            if slot is not None and key in calls:
                terminal(calls[key], path, findings)
    return applicable


def check_schema_shape(schema: Any, path: str, findings: list[Finding]) -> None:
    if not isinstance(schema, dict):
        add(findings, "invalid_schema", path, "schema must be an object")
        return
    unknown = sorted(set(schema) - SCHEMA_KEYS)
    if unknown:
        add(findings, "unsupported_schema_keyword", path, f"unsupported keywords: {', '.join(unknown)}")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        add(findings, "invalid_schema", f"{path}/properties", "properties must be an object")
    else:
        for key, child in properties.items():
            check_schema_shape(child, f"{path}/properties/{key}", findings)
    if "items" in schema:
        check_schema_shape(schema["items"], f"{path}/items", findings)
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required) or len(set(required)) != len(required):
        add(findings, "invalid_schema", f"{path}/required", "required must be an array of unique strings")
    if schema.get("additionalProperties", False) not in (True, False):
        add(findings, "invalid_schema", f"{path}/additionalProperties", "additionalProperties must be boolean")


def type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_value(value: Any, schema: dict[str, Any], path: str, findings: list[Finding]) -> None:
    if "enum" in schema and (not isinstance(schema["enum"], list) or value not in schema["enum"]):
        add(findings, "schema_enum", path, "value is not in enum")
    expected = schema.get("type")
    if expected is not None:
        if not isinstance(expected, str) or expected not in {"object", "array", "string", "integer", "number", "boolean", "null"}:
            add(findings, "invalid_schema", path, "type must be one supported string")
            return
        if not type_matches(value, expected):
            add(findings, "schema_type", path, f"expected {expected}")
            return
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required if isinstance(required, list) else []:
            if key not in value:
                add(findings, "schema_required", f"{path}/{key}", "required property is missing")
        for key, item in value.items():
            if key in properties and isinstance(properties[key], dict):
                validate_value(item, properties[key], f"{path}/{key}", findings)
            elif schema.get("additionalProperties", False) is False:
                add(findings, "schema_additional_property", f"{path}/{key}", "additional property is not allowed")
    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            add(findings, "schema_min_items", path, "array has too few items")
        if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]:
            add(findings, "schema_max_items", path, "array has too many items")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                validate_value(item, schema["items"], f"{path}/{index}", findings)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]:
            add(findings, "schema_minimum", path, "number is below minimum")
        if isinstance(schema.get("maximum"), (int, float)) and value > schema["maximum"]:
            add(findings, "schema_maximum", path, "number is above maximum")


def validate(document: Any) -> dict[str, Any]:
    findings: list[Finding] = []
    calls: dict[str, Call] = {}
    if not isinstance(document, dict):
        add(findings, "invalid_document", "/", "document must be an object")
        return result(False, calls, findings, {})
    profile = document.get("profile")
    if profile not in PROFILES:
        add(findings, "unknown_profile", "/profile", "profile must be openai, mistral, or anthropic")
        return result(False, calls, findings, {})
    schemas = document.get("tool_schemas", {})
    if not isinstance(schemas, dict):
        add(findings, "invalid_tool_schemas", "/tool_schemas", "tool_schemas must be an object")
        schemas = {}
    for name, schema in schemas.items():
        if not isinstance(name, str) or not name:
            add(findings, "invalid_tool_name", "/tool_schemas", "schema names must be non-empty strings")
        check_schema_shape(schema, f"/tool_schemas/{name}", findings)
    applicable = parse_anthropic(document, calls, findings) if profile == "anthropic" else parse_openai_like(document, calls, findings)
    if not applicable:
        return result(False, calls, findings, schemas)
    for key in sorted(calls):
        call = calls[key]
        path = f"/calls/{key}"
        if call.call_id is None:
            add(findings, "missing_call_id", path, "final call id is missing")
        if call.name is None:
            add(findings, "missing_tool_name", path, "final tool name is missing")
        if not call.terminal:
            add(findings, "missing_terminal", path, "provider terminal signal is missing")
        raw = "".join(call.fragments)
        try:
            arguments = strict_loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            add(findings, "invalid_arguments_json", path, f"arguments are not strict JSON: {exc}")
            continue
        if not isinstance(arguments, dict):
            add(findings, "arguments_not_object", path, "final arguments must be an object")
            continue
        if call.name not in schemas:
            add(findings, "unknown_tool", path, "no schema was supplied for the final tool name")
            continue
        schema = schemas[call.name]
        if isinstance(schema, dict):
            validate_value(arguments, schema, f"{path}/arguments", findings)
    return result(True, calls, findings, schemas)


def result(applicable: bool, calls: dict[str, Call], findings: list[Finding], schemas: dict[str, Any]) -> dict[str, Any]:
    errors = any(item.level == "error" for item in findings)
    if not applicable:
        status = "not_applicable" if not errors else "invalid"
    else:
        status = "fail" if errors else "pass"
    rendered = []
    for key in sorted(calls):
        call = calls[key]
        raw = "".join(call.fragments)
        arguments = None
        try:
            parsed = strict_loads(raw)
            if isinstance(parsed, dict):
                arguments = parsed
        except (json.JSONDecodeError, ValueError):
            pass
        rendered.append({"scope": call.scope, "slot": call.slot, "id": call.call_id, "name": call.name, "arguments": arguments, "terminal": call.terminal})
    return {
        "status": status,
        "applicable": applicable,
        "executable": status == "pass",
        "calls": rendered,
        "findings": [asdict(item) for item in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--report", choices=("human", "json"), default="human")
    args = parser.parse_args(argv)
    try:
        document = load_document(args.fixture)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    report = validate(document)
    if args.report == "json":
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    else:
        print(f"result: {report['status'].upper()}")
        print(f"executable: {'yes' if report['executable'] else 'no'}")
        for item in report["findings"]:
            print(f"{item['level'].upper()} {item['code']} {item['path']}: {item['message']}")
    if report["status"] == "pass":
        return 0
    if report["status"] in {"not_applicable", "invalid"} and not report["applicable"]:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
