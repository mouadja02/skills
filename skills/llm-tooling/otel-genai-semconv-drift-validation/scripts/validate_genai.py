#!/usr/bin/env python3
"""Offline, fail-closed validator for normalized OpenTelemetry GenAI records."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, TypeGuard


def reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=reject_constant)


def finding(severity: str, code: str, message: str, record: int | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if record is not None:
        item["record"] = record
    return item


def strict_nonnegative_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate(document: Any, profiles: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("input root must be an object")
    allowed_root = {"schema_version", "profile", "content_capture", "records"}
    unknown = sorted(set(document) - allowed_root)
    if unknown:
        raise ValueError(f"unknown root keys: {', '.join(unknown)}")
    if document.get("schema_version") != 1:
        raise ValueError("schema_version must be integer 1")
    profile_name = document.get("profile")
    if not isinstance(profile_name, str) or profile_name not in profiles.get("profiles", {}):
        raise ValueError("profile must name a bundled, pinned profile")
    records = document.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    capture = document.get("content_capture")
    if not isinstance(capture, dict) or set(capture) != {"opt_in", "redaction_verified", "truncation_limit"}:
        raise ValueError("content_capture must contain exactly opt_in, redaction_verified, and truncation_limit")
    if not isinstance(capture["opt_in"], bool) or not isinstance(capture["redaction_verified"], bool):
        raise ValueError("content_capture opt_in and redaction_verified must be booleans")
    limit = capture["truncation_limit"]
    if limit is not None and (not strict_nonnegative_int(limit) or limit == 0):
        raise ValueError("truncation_limit must be null or a positive integer")

    profile = profiles["profiles"][profile_name]
    findings: list[dict[str, Any]] = []
    applicable = False
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {"kind", "name", "attributes"}:
            raise ValueError(f"record {index} must contain exactly kind, name, and attributes")
        kind, name, attrs = record["kind"], record["name"], record["attributes"]
        if kind not in {"span", "event"} or not isinstance(name, str) or not isinstance(attrs, dict):
            raise ValueError(f"record {index} has invalid kind, name, or attributes")
        if not all(isinstance(key, str) for key in attrs):
            raise ValueError(f"record {index} attribute keys must be strings")
        is_genai = name.startswith("gen_ai.") or any(key.startswith("gen_ai.") for key in attrs)
        if not is_genai:
            continue
        applicable = True

        for old, new in profile["legacy_attributes"].items():
            if old in attrs:
                findings.append(finding("error", "legacy_attribute", f"{old} is legacy in this profile; review migration to {new}", index))
        if kind == "event" and name in profile["legacy_events"]:
            findings.append(finding("error", "legacy_event", f"{name} is legacy; use {profile['legacy_events'][name]}", index))

        operation = attrs.get("gen_ai.operation.name")
        if not isinstance(operation, str) or not operation:
            findings.append(finding("error", "missing_operation", "gen_ai.operation.name is required for a GenAI record", index))
        elif kind == "span":
            expected = None
            if operation == "execute_tool" and isinstance(attrs.get("gen_ai.tool.name"), str):
                expected = f"execute_tool {attrs['gen_ai.tool.name']}"
            elif operation == "invoke_agent":
                agent = attrs.get("gen_ai.agent.name")
                expected = f"invoke_agent {agent}" if isinstance(agent, str) and agent else "invoke_agent"
            elif isinstance(attrs.get("gen_ai.request.model"), str):
                expected = f"{operation} {attrs['gen_ai.request.model']}"
            if operation == "execute_tool" and not isinstance(attrs.get("gen_ai.tool.name"), str):
                findings.append(finding("error", "missing_tool_name", "execute_tool span requires gen_ai.tool.name", index))
            if expected and name != expected:
                findings.append(finding("warning", "span_name_drift", f"expected span name {expected!r}, observed {name!r}", index))

        token_keys = (
            "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens",
            "gen_ai.usage.cache_read.input_tokens", "gen_ai.usage.cache_creation.input_tokens",
            "gen_ai.usage.reasoning.output_tokens",
        )
        for key in token_keys:
            if key in attrs and not strict_nonnegative_int(attrs[key]):
                findings.append(finding("error", "invalid_token_count", f"{key} must be a non-negative integer", index))
        total = attrs.get("gen_ai.usage.input_tokens")
        cache_values = [attrs.get("gen_ai.usage.cache_read.input_tokens", 0), attrs.get("gen_ai.usage.cache_creation.input_tokens", 0)]
        if strict_nonnegative_int(total) and all(strict_nonnegative_int(v) for v in cache_values) and int(total) < sum(int(v) for v in cache_values):
            findings.append(finding("error", "input_token_total_too_small", "input token total must include cache-read and cache-creation token counts", index))
        output = attrs.get("gen_ai.usage.output_tokens")
        reasoning = attrs.get("gen_ai.usage.reasoning.output_tokens", 0)
        if strict_nonnegative_int(output) and strict_nonnegative_int(reasoning) and int(output) < int(reasoning):
            findings.append(finding("error", "output_token_total_too_small", "output token total must include reasoning tokens", index))

        content_present = sorted(key for key in profile["content_attributes"] if key in attrs)
        if content_present:
            if not capture["opt_in"]:
                findings.append(finding("error", "content_without_opt_in", f"content attributes present without explicit opt-in: {', '.join(content_present)}", index))
            if not capture["redaction_verified"]:
                findings.append(finding("error", "content_redaction_unverified", "content capture requires a verified redaction policy", index))
            if limit is None:
                findings.append(finding("warning", "content_unbounded", "content capture has no truncation limit", index))
        for key, value in attrs.items():
            if isinstance(value, float) and not math.isfinite(value):
                findings.append(finding("error", "non_finite_number", f"{key} is not finite", index))

    if not applicable:
        status = "not_applicable"
    elif any(item["severity"] == "error" for item in findings):
        status = "fail"
    elif findings:
        status = "review"
    else:
        status = "pass"
    return {"schema_version": 1, "profile": profile_name, "status": status, "mutation_permitted": False, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        profiles = load_json(Path(__file__).resolve().parent.parent / "references" / "profiles.json")
        result = validate(load_json(args.input), profiles)
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        return 1 if result["status"] == "fail" else 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        try:
            sys.stderr.write(f"validation error: {exc}\n")
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
