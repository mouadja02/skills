#!/usr/bin/env python3
"""Classify redacted PostgreSQL replication-slot snapshots without database access."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_INPUT_BYTES = 1_048_576
TOP_KEYS = {"schema_version", "server_role", "warning_threshold_bytes", "slots"}
SLOT_KEYS = {
    "slot_name", "slot_type", "active", "failover", "synced", "temporary",
    "invalidation_reason", "wal_status", "safe_wal_size", "retained_wal_bytes",
    "consumer_owner_confirmed",
}
ROLES = {"primary", "standby", "demoted_primary"}
WAL_STATUSES = {"reserved", "extended", "unreserved", "lost", None}

class InputError(ValueError):
    pass

def reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON number is not allowed: {value}")

def require_bool(obj: dict, key: str) -> bool:
    value = obj.get(key)
    if type(value) is not bool:
        raise InputError(f"{key} must be a boolean")
    return value

def optional_nonnegative_int(obj: dict, key: str) -> int | None:
    value = obj.get(key)
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise InputError(f"{key} must be a non-negative integer or null")
    return value

def load_snapshot(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid UTF-8 JSON: {exc}") from exc
    if type(data) is not dict:
        raise InputError("top level must be an object")
    unknown = set(data) - TOP_KEYS
    if unknown:
        raise InputError(f"unknown top-level keys: {', '.join(sorted(unknown))}")
    missing = {"schema_version", "server_role", "slots"} - set(data)
    if missing:
        raise InputError(f"missing top-level keys: {', '.join(sorted(missing))}")
    if data.get("schema_version") != 1:
        raise InputError("schema_version must equal 1")
    if data.get("server_role") not in ROLES:
        raise InputError("server_role must be primary, standby, or demoted_primary")
    threshold = data.get("warning_threshold_bytes", 1_073_741_824)
    if type(threshold) is not int or threshold < 0:
        raise InputError("warning_threshold_bytes must be a non-negative integer")
    slots = data.get("slots")
    if type(slots) is not list:
        raise InputError("slots must be an array")
    names: set[str] = set()
    for index, slot in enumerate(slots):
        if type(slot) is not dict:
            raise InputError(f"slots[{index}] must be an object")
        unknown = set(slot) - SLOT_KEYS
        if unknown:
            raise InputError(f"slots[{index}] has unknown keys: {', '.join(sorted(unknown))}")
        missing = SLOT_KEYS - set(slot)
        if missing:
            raise InputError(f"slots[{index}] has missing keys: {', '.join(sorted(missing))}")
        name = slot.get("slot_name")
        if type(name) is not str or not name or len(name) > 63 or "\x00" in name:
            raise InputError(f"slots[{index}].slot_name must be a non-empty PostgreSQL identifier-length string")
        if name in names:
            raise InputError(f"duplicate slot_name: {name}")
        names.add(name)
        if slot.get("slot_type") not in {"logical", "physical"}:
            raise InputError(f"slots[{index}].slot_type must be logical or physical")
        for key in ("active", "failover", "synced", "temporary", "consumer_owner_confirmed"):
            require_bool(slot, key)
        reason = slot.get("invalidation_reason")
        if reason is not None and (type(reason) is not str or not reason or len(reason) > 128):
            raise InputError(f"slots[{index}].invalidation_reason must be a short string or null")
        if slot.get("wal_status") not in WAL_STATUSES:
            raise InputError(f"slots[{index}].wal_status is not recognized")
        optional_nonnegative_int(slot, "safe_wal_size")
        optional_nonnegative_int(slot, "retained_wal_bytes")
    data["warning_threshold_bytes"] = threshold
    return data

def classify_slot(slot: dict, role: str, threshold: int) -> dict:
    result = {"slot_name": slot["slot_name"], "classification": "healthy", "reasons": [], "actions": []}
    if slot["slot_type"] == "physical":
        result.update(classification="not_applicable", reasons=["physical_slot"], actions=["route_to_physical_replication_runbook"])
        return result
    invalid = slot["invalidation_reason"] is not None or slot["wal_status"] == "lost"
    if invalid:
        result.update(classification="unusable", reasons=["slot_invalidated_or_wal_lost"], actions=["stop_failover_assumption", "rebuild_consumer_from_approved_recovery_point"])
        return result
    if role == "standby":
        ready = slot["synced"] and not slot["temporary"] and slot["invalidation_reason"] is None
        if ready:
            result.update(classification="failover_ready", reasons=["synced_non_temporary_not_invalidated"], actions=["verify_standby_ahead_of_subscriber"])
        else:
            result.update(classification="failover_not_ready", reasons=["standby_slot_readiness_predicate_failed"], actions=["do_not_promote_for_this_consumer", "repair_slot_synchronization"])
        return result
    retained = slot["retained_wal_bytes"] or 0
    safe = slot["safe_wal_size"]
    if slot["wal_status"] == "unreserved" or safe == 0:
        result.update(classification="wal_loss_imminent", reasons=["slot_near_or_beyond_retention_boundary"], actions=["protect_disk_headroom", "confirm_consumer_and_recovery_point"])
    elif not slot["active"] and not slot["consumer_owner_confirmed"] and retained > 0:
        result.update(classification="orphan_candidate", reasons=["inactive_unowned_slot_retains_wal"], actions=["identify_consumer_owner", "measure_wal_growth", "require_approval_before_slot_mutation"])
    elif safe is not None and safe <= threshold:
        result.update(classification="retention_pressure", reasons=["safe_wal_size_below_warning_threshold"], actions=["protect_disk_headroom", "restore_consumer_progress"])
    elif not slot["failover"]:
        result.update(classification="not_failover_enabled", reasons=["logical_slot_not_enabled_for_failover"], actions=["plan_failover_slot_configuration_before_switchover"])
    elif not slot["active"]:
        result.update(classification="inactive_owned", reasons=["confirmed_consumer_is_inactive"], actions=["reconcile_consumer_before_mutation"])
    return result

def analyze(data: dict) -> dict:
    logical = [s for s in data["slots"] if s["slot_type"] == "logical"]
    results = [classify_slot(s, data["server_role"], data["warning_threshold_bytes"]) for s in data["slots"]]
    classes = {r["classification"] for r in results}
    if not logical:
        overall = "not_applicable"
    elif classes & {"unusable", "wal_loss_imminent"}:
        overall = "critical"
    elif "failover_not_ready" in classes:
        overall = "blocked"
    elif classes & {"orphan_candidate", "retention_pressure", "not_failover_enabled", "inactive_owned"}:
        overall = "review"
    else:
        overall = "ready"
    return {
        "schema_version": 1,
        "overall": overall,
        "server_role": data["server_role"],
        "mutation_permitted": False,
        "human_approval_required_for_mutation": True,
        "slots": results,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = analyze(load_snapshot(args.input))
        json.dump(output, sys.stdout, indent=2, sort_keys=True, allow_nan=False)
        sys.stdout.write("\n")
        return 0
    except (InputError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
