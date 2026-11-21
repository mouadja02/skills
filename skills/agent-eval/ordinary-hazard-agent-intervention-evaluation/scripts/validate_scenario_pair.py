#!/usr/bin/env python3
"""Validate the structural minimal difference of an offline hazard scenario pair."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    raise ValueError(message)


def reject_constant(value: str) -> None:
    fail(f"non-standard JSON constant is not allowed: {value}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data: Any = json.load(handle, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON: {exc}")
        raise AssertionError("unreachable") from exc
    if not isinstance(data, dict):
        fail("document root must be an object")
    return data


def finite_tree(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        fail(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail(f"non-string object key at {path}")
            finite_tree(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            finite_tree(item, f"{path}[{index}]")


def differences(left: Any, right: Any, path: str = "$") -> set[str]:
    if type(left) is not type(right):
        return {path}
    if isinstance(left, dict):
        found: set[str] = set()
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                found.add(child)
            else:
                found |= differences(left[key], right[key], child)
        return found
    if isinstance(left, list):
        if len(left) != len(right):
            return {path}
        found: set[str] = set()
        for index, (a, b) in enumerate(zip(left, right)):
            found |= differences(a, b, f"{path}[{index}]")
        return found
    return set() if left == right else {path}


def validate(data: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "pair_id", "source_claim", "incident_world",
        "control_world", "allowed_differences", "harm_oracle", "reachability_checks"
    }
    missing = sorted(required - set(data))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if data["schema_version"] != 1:
        fail("schema_version must equal 1")
    if not isinstance(data["pair_id"], str) or not data["pair_id"].strip():
        fail("pair_id must be a non-empty string")
    claim = data["source_claim"]
    if not isinstance(claim, dict) or not isinstance(claim.get("urls"), list) or not claim["urls"]:
        fail("source_claim.urls must be a non-empty array")
    if not all(isinstance(url, str) and url.startswith(("https://", "http://")) for url in claim["urls"]):
        fail("every source_claim URL must be an HTTP(S) URL")
    incident, control = data["incident_world"], data["control_world"]
    if not isinstance(incident, dict) or not isinstance(control, dict):
        fail("incident_world and control_world must be objects")
    finite_tree(incident, "$.incident_world")
    finite_tree(control, "$.control_world")
    allowed = data["allowed_differences"]
    if not isinstance(allowed, list) or not allowed or not all(isinstance(x, str) and x.startswith("$.") for x in allowed):
        fail("allowed_differences must be a non-empty array of $. paths")
    if len(allowed) != len(set(allowed)):
        fail("allowed_differences contains duplicates")
    actual = differences(incident, control)
    expected = set(allowed)
    if actual != expected:
        fail(f"world difference mismatch: actual={sorted(actual)} allowed={sorted(expected)}")
    oracle = data["harm_oracle"]
    if not isinstance(oracle, dict) or oracle.get("type") != "final_state":
        fail("harm_oracle.type must be final_state")
    observed = oracle.get("observed_paths")
    if not isinstance(observed, list) or not observed or not all(isinstance(x, str) and x for x in observed):
        fail("harm_oracle.observed_paths must be a non-empty string array")
    if not isinstance(oracle.get("harmful_when"), str) or not oracle["harmful_when"].strip():
        fail("harm_oracle.harmful_when must be a non-empty string")
    checks = data["reachability_checks"]
    if not isinstance(checks, list) or len(checks) < 4:
        fail("reachability_checks must contain at least four checks")
    names = {item.get("name") for item in checks if isinstance(item, dict)}
    needed = {"incident_harm_reachable", "control_safe", "known_harm_oracle", "known_safe_oracle"}
    if not needed <= names:
        fail(f"reachability_checks missing: {', '.join(sorted(needed - names))}")
    return {
        "valid": True,
        "pair_id": data["pair_id"],
        "difference_count": len(actual),
        "differences": sorted(actual),
        "oracle_type": "final_state",
        "reachability_checks": len(checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_pair", type=Path)
    args = parser.parse_args()
    try:
        result = validate(load_json(args.scenario_pair))
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
