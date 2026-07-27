#!/usr/bin/env python3
"""Validate offline evidence for a free-threaded CPython extension release gate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOP_KEYS = {"schema_version", "project", "claim", "native_extensions", "builds", "dependencies"}
EXT_KEYS = {"name", "gil_declaration", "stress", "tsan"}
STRESS_KEYS = {"runs", "threads", "completed", "failures"}
BUILD_KEYS = {"mode", "passed", "py_gil_disabled"}
DEP_KEYS = {"name", "version", "free_threaded_support"}


class EvidenceError(ValueError):
    pass


def strict_object(value: Any, label: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    unknown = sorted(set(value) - keys)
    if unknown:
        raise EvidenceError(f"{label} has unknown keys: {', '.join(unknown)}")
    missing = sorted(keys - set(value))
    if missing:
        raise EvidenceError(f"{label} is missing keys: {', '.join(missing)}")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{label} must be a non-empty string")
    return value.strip()


def integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceError(f"{label} must be an integer")
    return value


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceError(f"{label} must be a boolean")
    return value


def choice(value: Any, label: str, options: set[str]) -> str:
    result = text(value, label)
    if result not in options:
        raise EvidenceError(f"{label} must be one of: {', '.join(sorted(options))}")
    return result


def array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceError(f"{label} must be an array")
    return value


def load(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle, parse_constant=lambda token: (_ for _ in ()).throw(EvidenceError(f"non-finite JSON constant: {token}")))
    except EvidenceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read valid UTF-8 JSON: {exc}") from exc
    return strict_object(value, "evidence", TOP_KEYS)


def evaluate(data: dict[str, Any], require_tsan: bool) -> dict[str, Any]:
    if integer(data["schema_version"], "schema_version") != 1:
        raise EvidenceError("schema_version must be 1")
    project = text(data["project"], "project")
    claim = choice(data["claim"], "claim", {"ready", "experimental", "gil-required", "not-applicable"})
    extensions = array(data["native_extensions"], "native_extensions")
    builds = array(data["builds"], "builds")
    dependencies = array(data["dependencies"], "dependencies")

    if not extensions:
        if claim != "not-applicable":
            raise EvidenceError("an empty native_extensions array requires claim not-applicable")
        if builds or dependencies:
            raise EvidenceError("not-applicable evidence must have empty builds and dependencies arrays")
        return {"schema_version": 1, "project": project, "status": "not_applicable", "blocking": [], "warnings": []}

    blocking: list[str] = []
    warnings: list[str] = []
    seen_modes: set[str] = set()
    for index, raw in enumerate(builds):
        item = strict_object(raw, f"builds[{index}]", BUILD_KEYS)
        mode = choice(item["mode"], f"builds[{index}].mode", {"gil", "free-threaded"})
        if mode in seen_modes:
            raise EvidenceError(f"duplicate build mode: {mode}")
        seen_modes.add(mode)
        passed = boolean(item["passed"], f"builds[{index}].passed")
        disabled = boolean(item["py_gil_disabled"], f"builds[{index}].py_gil_disabled")
        if disabled != (mode == "free-threaded"):
            blocking.append(f"{mode} interpreter identity does not match py_gil_disabled={str(disabled).lower()}")
        if not passed:
            blocking.append(f"{mode} build or test leg did not pass")
    for missing in sorted({"gil", "free-threaded"} - seen_modes):
        blocking.append(f"missing {missing} build leg")

    seen_extensions: set[str] = set()
    for index, raw in enumerate(extensions):
        item = strict_object(raw, f"native_extensions[{index}]", EXT_KEYS)
        name = text(item["name"], f"native_extensions[{index}].name")
        if name in seen_extensions:
            raise EvidenceError(f"duplicate native extension: {name}")
        seen_extensions.add(name)
        declaration = choice(item["gil_declaration"], f"{name}.gil_declaration", {"not-used", "used", "unknown"})
        if declaration != "not-used":
            blocking.append(f"{name} does not have a verified no-GIL declaration")
        stress = strict_object(item["stress"], f"{name}.stress", STRESS_KEYS)
        runs = integer(stress["runs"], f"{name}.stress.runs")
        threads = integer(stress["threads"], f"{name}.stress.threads")
        completed = boolean(stress["completed"], f"{name}.stress.completed")
        failures = integer(stress["failures"], f"{name}.stress.failures")
        if runs < 10 or threads < 2 or not completed or failures != 0:
            blocking.append(f"{name} lacks a passing overlap stress boundary (runs>=10, threads>=2, completed, zero failures)")
        tsan = choice(item["tsan"], f"{name}.tsan", {"clean", "findings", "not-run"})
        if tsan == "findings":
            blocking.append(f"{name} has unresolved ThreadSanitizer findings")
        elif tsan == "not-run":
            (blocking if require_tsan else warnings).append(f"{name} has no ThreadSanitizer evidence")

    seen_dependencies: set[str] = set()
    for index, raw in enumerate(dependencies):
        item = strict_object(raw, f"dependencies[{index}]", DEP_KEYS)
        name = text(item["name"], f"dependencies[{index}].name")
        text(item["version"], f"dependencies[{index}].version")
        if name in seen_dependencies:
            raise EvidenceError(f"duplicate dependency: {name}")
        seen_dependencies.add(name)
        support = choice(item["free_threaded_support"], f"{name}.free_threaded_support", {"yes", "no", "unknown"})
        if support != "yes":
            blocking.append(f"dependency {name} free-threaded support is {support}")

    if claim != "ready":
        blocking.append(f"declared release claim is {claim}, not ready")
    return {"schema_version": 1, "project": project, "status": "blocked" if blocking else "ready", "blocking": blocking, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--require-tsan", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = evaluate(load(args.evidence), args.require_tsan)
    except EvidenceError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
