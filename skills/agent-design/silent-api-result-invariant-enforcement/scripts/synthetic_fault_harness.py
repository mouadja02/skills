#!/usr/bin/env python3
"""Offline decision-matrix fixture for silent API result enforcement."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


MODES = (
    "correct",
    "drop-last",
    "cap-total",
    "or-semantics",
    "drop-field",
    "off-by-one",
    "transient",
    "unsupported",
)
QUERY = (("status", "active", False), ("tier", "gold", False))
RECORDS = (
    {"id": "1", "status": "active", "tier": "gold"},
    {"id": "2", "status": "active", "tier": "gold"},
    {"id": "3", "status": "active", "tier": "gold"},
    {"id": "4", "status": "active", "tier": "silver"},
    {"id": "5", "status": "active", "tier": "silver"},
    {"id": "6", "status": "inactive", "tier": "gold"},
    {"id": "7", "status": "inactive", "tier": "gold"},
    {"id": "8", "status": "inactive", "tier": "silver"},
)


@dataclass
class CheckResult:
    passed: bool
    failed_checks: list[str]
    evidence: list[dict[str, object]]
    extra_calls: int


def _matches(record: dict[str, str], condition: tuple[str, str, bool]) -> bool:
    field, value, negate = condition
    equal = record.get(field) == value
    return not equal if negate else equal


def _make_count(mode: str) -> Callable[[Iterable[tuple[str, str, bool]]], int]:
    calls = 0

    def count(conditions: Iterable[tuple[str, str, bool]]) -> int:
        nonlocal calls
        calls += 1
        selected = list(conditions)
        effective_mode = "off-by-one" if mode == "transient" and calls == 1 else mode
        if effective_mode == "drop-last" and selected:
            selected = selected[:-1]
        if effective_mode == "drop-field":
            selected = [item for item in selected if item[0] != "tier"]
        if effective_mode == "or-semantics" and selected:
            value = sum(any(_matches(record, item) for item in selected) for record in RECORDS)
        else:
            value = sum(all(_matches(record, item) for item in selected) for record in RECORDS)
        if effective_mode == "cap-total":
            value = min(value, 2)
        if effective_mode == "off-by-one":
            value += 1
        return value

    return count


def _check_count(
    count: Callable[[Iterable[tuple[str, str, bool]]], int],
    conditions: list[tuple[str, str, bool]],
    reported: int,
) -> CheckResult:
    failed: list[str] = []
    evidence: list[dict[str, object]] = []
    for index, condition in enumerate(conditions):
        rest = conditions[:index] + conditions[index + 1 :]
        field, value, negate = condition
        negated = rest + [(field, value, not negate)]
        complement_count = count(negated)
        without_count = count(rest)
        check_id = f"count-partition:{field}"
        passed = reported + complement_count == without_count
        evidence.append(
            {
                "check_id": check_id,
                "reported": reported,
                "complement_count": complement_count,
                "without_count": without_count,
                "passed": passed,
            }
        )
        if not passed:
            failed.append(check_id)
    return CheckResult(not failed, failed, evidence, 2 * len(conditions))


def run_scenario(mode: str) -> dict[str, object]:
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    if mode == "unsupported":
        return {
            "mode": mode,
            "decision": "unsupported",
            "verified": False,
            "check_class": "exact",
            "released_value": None,
            "failed_checks": [],
            "attempts": [],
            "extra_calls": 0,
            "rechecks": 0,
            "limitations": ["API does not document exhaustive complement or negation semantics"],
        }

    count = _make_count(mode)
    reported = count(QUERY)
    first = _check_count(count, list(QUERY), reported)
    attempts = [{"reported": reported, "checks": first.evidence}]
    extra_calls = first.extra_calls
    if first.passed:
        return {
            "mode": mode,
            "decision": "verified",
            "verified": True,
            "check_class": "exact",
            "released_value": reported,
            "failed_checks": [],
            "attempts": attempts,
            "extra_calls": extra_calls,
            "rechecks": 0,
            "limitations": ["same-source consistency does not prove external truth"],
        }

    second_reported = count(QUERY)
    second = _check_count(count, list(QUERY), second_reported)
    attempts.append({"reported": second_reported, "checks": second.evidence})
    extra_calls += 1 + second.extra_calls
    if second.passed:
        return {
            "mode": mode,
            "decision": "verified_on_recheck",
            "verified": True,
            "check_class": "exact",
            "released_value": second_reported,
            "failed_checks": first.failed_checks,
            "attempts": attempts,
            "extra_calls": extra_calls,
            "rechecks": 1,
            "limitations": ["same-source consistency does not prove external truth"],
        }
    return {
        "mode": mode,
        "decision": "withheld",
        "verified": False,
        "check_class": "exact",
        "released_value": None,
        "failed_checks": sorted(set(first.failed_checks + second.failed_checks)),
        "attempts": attempts,
        "extra_calls": extra_calls,
        "rechecks": 1,
        "limitations": ["same-source consistency does not prove external truth"],
    }


def build_report(modes: Iterable[str]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "fixture": "synthetic filtered-count API",
        "scenarios": [run_scenario(mode) for mode in modes],
        "global_limitations": (
            "A consistently lying API can preserve every same-source invariant; "
            "an independent source of truth is required."
        ),
    }


def _atomic_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mode", choices=MODES)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modes = MODES if args.all else (args.mode,)
    try:
        _atomic_write(args.output, build_report(modes))
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
