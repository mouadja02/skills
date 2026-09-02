#!/usr/bin/env python3
"""Offline, fail-closed comparison of named-zone observations across runtimes."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Any

EXIT_INPUT = 2
EXIT_BLOCKED = 1
EXIT_OUTPUT = 74
KINDS = {"gap", "fold", "recent-rule", "control"}

class InputError(ValueError):
    pass

def obj(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    return value

def exact_keys(value: dict[str, Any], required: set[str], optional: set[str], where: str) -> None:
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - required - optional)
    if missing or extra:
        raise InputError(f"{where} keys invalid: missing={missing}, extra={extra}")

def text(value: Any, where: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value or "\x00" in value:
        raise InputError(f"{where} must be a non-empty NUL-free string")
    return value

def integer(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputError(f"{where} must be an integer")
    return value

def iso(value: Any, where: str) -> str:
    value = text(value, where)
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputError(f"{where} must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise InputError(f"{where} must include an offset")
    return value

def strict_load(path: str) -> Any:
    def reject(value: str) -> None:
        raise InputError(f"non-finite number is forbidden: {value}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh, parse_constant=reject)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot parse input: {exc}") from exc

def analyze(raw: Any) -> tuple[dict[str, Any], int]:
    root = obj(raw, "root")
    exact_keys(root, {"schema_version", "mode"}, {"policy", "observations"}, "root")
    if integer(root["schema_version"], "schema_version") != 1:
        raise InputError("schema_version must be 1")
    mode = text(root["mode"], "mode")
    if mode == "fixed-offset":
        if root.get("observations") not in (None, []):
            raise InputError("fixed-offset mode must not include named-zone observations")
        return {"schema_version": 1, "status": "not_applicable", "reason": "fixed-offset/epoch-only data has no named-zone rule dependency", "observations": [], "findings": []}, 0
    if mode != "named-zone":
        raise InputError("mode must be named-zone or fixed-offset")
    policy = obj(root.get("policy"), "policy")
    exact_keys(policy, {"require_declared_version"}, set(), "policy")
    require_version = policy["require_declared_version"]
    if not isinstance(require_version, bool):
        raise InputError("policy.require_declared_version must be boolean")
    observations = root.get("observations")
    if not isinstance(observations, list) or len(observations) < 2:
        raise InputError("named-zone mode requires at least two observations")
    normalized: list[dict[str, Any]] = []
    runtime_ids: set[str] = set()
    zone: str | None = None
    for oi, item in enumerate(observations):
        rec = obj(item, f"observations[{oi}]")
        exact_keys(rec, {"runtime_id", "provider", "version", "zone", "probes"}, set(), f"observations[{oi}]")
        rid = text(rec["runtime_id"], f"observations[{oi}].runtime_id")
        if rid in runtime_ids:
            raise InputError(f"duplicate runtime_id: {rid}")
        runtime_ids.add(rid)
        provider = text(rec["provider"], f"observations[{oi}].provider")
        version = text(rec["version"], f"observations[{oi}].version", nullable=True)
        current_zone = text(rec["zone"], f"observations[{oi}].zone")
        if zone is None:
            zone = current_zone
        elif zone != current_zone:
            raise InputError("all observations must use the same named zone")
        probes = rec["probes"]
        if not isinstance(probes, list) or not probes:
            raise InputError(f"observations[{oi}].probes must be a non-empty array")
        seen: set[str] = set(); norm_probes = []
        for pi, probe in enumerate(probes):
            p = obj(probe, f"observations[{oi}].probes[{pi}]")
            exact_keys(p, {"id", "kind", "wall", "fold", "valid", "offset_seconds", "utc"}, set(), f"observations[{oi}].probes[{pi}]")
            pid = text(p["id"], "probe.id")
            if pid in seen: raise InputError(f"duplicate probe id {pid} in {rid}")
            seen.add(pid)
            kind = text(p["kind"], "probe.kind")
            if kind not in KINDS: raise InputError(f"unknown probe kind: {kind}")
            wall = text(p["wall"], "probe.wall")
            try: parsed_wall = dt.datetime.fromisoformat(wall)
            except ValueError as exc: raise InputError("probe.wall must be ISO local datetime") from exc
            if parsed_wall.tzinfo is not None:
                raise InputError("probe.wall must be offset-free local datetime")
            fold = p["fold"]
            if fold is not None and integer(fold, "probe.fold") not in (0, 1): raise InputError("probe.fold must be 0, 1, or null")
            valid = p["valid"]
            if not isinstance(valid, bool): raise InputError("probe.valid must be boolean")
            offset = p["offset_seconds"]
            utc = p["utc"]
            if valid:
                offset = integer(offset, "probe.offset_seconds")
                if abs(offset) > 86400: raise InputError("probe.offset_seconds outside bounded range")
                utc = iso(utc, "probe.utc")
            elif offset is not None or utc is not None:
                raise InputError("invalid wall-time probe must use null offset_seconds and utc")
            norm_probes.append({"id":pid,"kind":kind,"wall":wall,"fold":fold,"valid":valid,"offset_seconds":offset,"utc":utc})
        normalized.append({"runtime_id":rid,"provider":provider,"version":version,"zone":current_zone,"probes":norm_probes})
    findings: list[dict[str, Any]] = []
    for rec in normalized:
        if rec["version"] is None:
            findings.append({"code":"UNKNOWN_PROVENANCE","severity":"violation" if require_version else "observation","runtime_id":rec["runtime_id"],"message":"runtime did not expose a declared time-zone database version"})
    required_kinds = {"gap", "fold", "recent-rule"}
    for rec in normalized:
        missing = sorted(required_kinds - {p["kind"] for p in rec["probes"]})
        if missing:
            findings.append({"code":"MISSING_TRANSITION_COVERAGE","severity":"violation","runtime_id":rec["runtime_id"],"missing":missing})
    probe_maps = [{p["id"]:p for p in rec["probes"]} for rec in normalized]
    all_ids = sorted(set().union(*(set(m) for m in probe_maps)))
    for pid in all_ids:
        missing = [normalized[i]["runtime_id"] for i,m in enumerate(probe_maps) if pid not in m]
        if missing:
            findings.append({"code":"MISSING_PROBE","severity":"violation","probe_id":pid,"runtimes":missing})
            continue
        values = {(m[pid]["valid"],m[pid]["offset_seconds"],m[pid]["utc"],m[pid]["wall"],m[pid]["fold"]) for m in probe_maps}
        if len(values) != 1:
            findings.append({"code":"PROBE_DIVERGENCE","severity":"violation","probe_id":pid,"results":[{"runtime_id":normalized[i]["runtime_id"],"valid":m[pid]["valid"],"offset_seconds":m[pid]["offset_seconds"],"utc":m[pid]["utc"]} for i,m in enumerate(probe_maps)]})
    findings.sort(key=lambda f:(f["code"],f.get("runtime_id",""),f.get("probe_id","")))
    blocked = any(f["severity"] == "violation" for f in findings)
    result = {"schema_version":1,"status":"blocked" if blocked else "allow","zone":zone,"observations":[{"runtime_id":r["runtime_id"],"provider":r["provider"],"version":r["version"],"probe_count":len(r["probes"])} for r in normalized],"findings":findings,"recovery":"preserve wall time, named zone, and fold; update or align the selected runtime data source in a controlled deployment, rerun the same probes, then persist only after allow" if blocked else None}
    return result, EXIT_BLOCKED if blocked else 0

def emit(payload: dict[str, Any]) -> None:
    try:
        sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    except (BrokenPipeError, OSError) as exc:
        try: sys.stderr.write(f"output error: {exc}\n")
        except OSError: pass
        try:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        except OSError:
            pass
        raise SystemExit(EXIT_OUTPUT)

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("input")
    args=parser.parse_args()
    try: payload, code = analyze(strict_load(args.input))
    except InputError as exc:
        emit({"schema_version":1,"status":"input_error","error":str(exc)})
        return EXIT_INPUT
    emit(payload); return code

if __name__ == "__main__":
    raise SystemExit(main())
