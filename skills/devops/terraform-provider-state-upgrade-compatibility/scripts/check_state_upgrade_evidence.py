#!/usr/bin/env python3
"""Fail-closed validator for Terraform provider state-upgrade evidence packets."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 1_048_576
TASK = "provider_state_upgrade_preflight"
BOOL_CHECKS = {
    "historical_schema_exact": "HISTORICAL_SCHEMA_UNPROVEN",
    "upgrader_registered": "UPGRADER_NOT_REGISTERED",
    "decode_passed": "HISTORICAL_DECODE_FAILED",
    "upgrade_passed": "UPGRADE_FAILED",
    "raw_typed_equivalent": "RAW_TYPED_MISMATCH",
    "null_unknown_cases_passed": "NULL_UNKNOWN_UNPROVEN",
    "removed_renamed_cases_passed": "REMOVED_RENAMED_UNPROVEN",
    "idempotence_passed": "IDEMPOTENCE_UNPROVEN",
}


def reject_constant(value: str):
    raise ValueError(f"non-standard JSON constant: {value}")


def finding(code: str, path: str, detail: str) -> dict:
    return {"code": code, "path": path, "detail": detail}


def validate(packet: object) -> tuple[dict, int]:
    if not isinstance(packet, dict):
        return {"status": "invalid", "findings": [finding("PACKET_NOT_OBJECT", "$", "top level must be an object")]}, 2
    if packet.get("task_kind") != TASK:
        return {"status": "not_applicable", "reason": f"task_kind must be {TASK!r}"}, 0

    findings: list[dict] = []
    resource = packet.get("resource")
    if not isinstance(resource, str) or not resource.strip():
        findings.append(finding("RESOURCE_INVALID", "$.resource", "must be a non-empty string"))

    current = packet.get("current_schema_version")
    if isinstance(current, bool) or not isinstance(current, int) or current < 1 or current > 100:
        findings.append(finding("CURRENT_VERSION_INVALID", "$.current_schema_version", "must be an integer from 1 through 100"))
        current = None

    transitions = packet.get("transitions")
    if not isinstance(transitions, list) or len(transitions) > 100:
        findings.append(finding("TRANSITIONS_INVALID", "$.transitions", "must be an array with at most 100 entries"))
        transitions = []

    strategy = packet.get("upgrade_strategy")
    if strategy not in ("sequential", "direct_to_current"):
        findings.append(finding("UPGRADE_STRATEGY_INVALID", "$.upgrade_strategy", "must equal sequential or direct_to_current"))

    observed: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for index, transition in enumerate(transitions):
        path = f"$.transitions[{index}]"
        if not isinstance(transition, dict):
            findings.append(finding("TRANSITION_NOT_OBJECT", path, "transition must be an object"))
            continue
        start, end = transition.get("from"), transition.get("to")
        if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int):
            findings.append(finding("TRANSITION_VERSION_INVALID", path, "from and to must be integers"))
        else:
            pair = (start, end)
            observed.append(pair)
            if pair in seen:
                findings.append(finding("DUPLICATE_TRANSITION", path, f"duplicate transition {start}->{end}"))
            seen.add(pair)
            if strategy == "sequential" and end != start + 1:
                findings.append(finding("NON_SEQUENTIAL_TRANSITION", path, f"transition {start}->{end} skips a version"))
        for field, code in BOOL_CHECKS.items():
            value = transition.get(field)
            if value is not True:
                detail = "must be boolean true" if isinstance(value, bool) or value is None else "must be a boolean and true"
                findings.append(finding(code, f"{path}.{field}", detail))
        plan = transition.get("plan_check")
        if plan == "unsupported":
            findings.append(finding("PLAN_CHECK_UNSUPPORTED", f"{path}.plan_check", "record a documented limitation; release gate remains closed"))
        elif plan != "no_change":
            findings.append(finding("PLAN_NOT_NO_CHANGE", f"{path}.plan_check", "must equal no_change"))

    if current is not None and strategy in ("sequential", "direct_to_current"):
        expected = ([(version, version + 1) for version in range(current)] if strategy == "sequential"
                    else [(version, current) for version in range(current)])
        if observed != expected:
            findings.append(finding("TRANSITION_COVERAGE_GAP", "$.transitions", f"expected ordered edges {expected}; observed {observed}"))

    released = packet.get("released_provider")
    if not isinstance(released, dict):
        findings.append(finding("RELEASED_PROVIDER_INVALID", "$.released_provider", "must be an object"))
    else:
        for field in ("source_version", "target_version"):
            if not isinstance(released.get(field), str) or not released[field].strip():
                findings.append(finding("RELEASED_VERSION_INVALID", f"$.released_provider.{field}", "must be a non-empty string"))
        for field, code in (("setup_passed", "RELEASED_SETUP_FAILED"), ("migration_passed", "RELEASED_MIGRATION_FAILED")):
            if released.get(field) is not True:
                findings.append(finding(code, f"$.released_provider.{field}", "must be boolean true"))
        if released.get("plan_check") != "no_change":
            findings.append(finding("RELEASED_PLAN_NOT_NO_CHANGE", "$.released_provider.plan_check", "must equal no_change"))

    if packet.get("backup_restore_rehearsed") is not True:
        findings.append(finding("RESTORE_NOT_REHEARSED", "$.backup_restore_rehearsed", "must be boolean true"))

    findings.sort(key=lambda item: (item["code"], item["path"], item["detail"]))
    return {
        "status": "pass" if not findings else "fail",
        "resource": resource,
        "current_schema_version": current,
        "finding_count": len(findings),
        "findings": findings,
    }, 0 if not findings else 1


def emit(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    target = Path(output)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", help="JSON evidence packet")
    parser.add_argument("--output", help="atomically write JSON result instead of stdout")
    args = parser.parse_args()
    try:
        path = Path(args.packet)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError(f"input exceeds {MAX_BYTES} bytes")
        packet = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
        result, status = validate(packet)
        emit(result, args.output)
        return status
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, TypeError) as exc:
        error = {"status": "invalid", "findings": [finding("INPUT_OR_OUTPUT_ERROR", "$", str(exc))]}
        try:
            sys.stderr.write(json.dumps(error, sort_keys=True, allow_nan=False) + "\n")
        except Exception:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
