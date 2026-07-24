#!/usr/bin/env python3
"""Fail-closed, offline interpretation of SQLite wal_checkpoint observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MODES = {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
REQUIRED = {"mode", "busy", "log_frames", "checkpointed_frames", "wal_bytes", "free_bytes"}
OPTIONAL = {"oldest_reader_seconds"}


def nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def analyze(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    unknown = set(value) - REQUIRED - OPTIONAL
    missing = REQUIRED - set(value)
    if missing:
        raise ValueError("missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        raise ValueError("unknown fields: " + ", ".join(sorted(unknown)))

    mode = value["mode"]
    if not isinstance(mode, str) or mode.upper() not in MODES:
        raise ValueError("mode must be PASSIVE, FULL, RESTART, or TRUNCATE")
    mode = mode.upper()
    busy = nonnegative_int(value["busy"], "busy")
    if busy not in (0, 1):
        raise ValueError("busy must be 0 or 1")
    log = nonnegative_int(value["log_frames"], "log_frames")
    done = nonnegative_int(value["checkpointed_frames"], "checkpointed_frames")
    wal = nonnegative_int(value["wal_bytes"], "wal_bytes")
    free = nonnegative_int(value["free_bytes"], "free_bytes")
    if done > log:
        raise ValueError("checkpointed_frames cannot exceed log_frames")
    if mode == "PASSIVE" and busy != 0:
        raise ValueError("PASSIVE checkpoint busy must be 0 per SQLite result semantics")
    if "oldest_reader_seconds" in value:
        nonnegative_int(value["oldest_reader_seconds"], "oldest_reader_seconds")

    remaining = log - done
    if remaining == 0:
        classification = "all_reported_frames_checkpointed"
        action = "sample again under representative writes and verify WAL bytes stabilize or reset"
    elif mode == "PASSIVE":
        classification = "partial_passive_progress" if done else "no_passive_progress"
        action = "correlate repeated samples with the oldest reader or concurrent writer boundary"
    elif busy == 1:
        classification = "blocking_checkpoint_incomplete"
        action = "stop escalation, identify the holder, and retry only within a bounded maintenance window"
    else:
        classification = "inconsistent_blocking_result"
        action = "preserve the raw result and verify client column mapping before acting"

    return {
        "classification": classification,
        "remaining_frames": remaining,
        "disk_headroom": "critical_by_recommended_ratio" if wal and free < 2 * wal else "ratio_not_triggered",
        "recommended_next_action": action,
        "warnings": [
            "Never delete or rename live -wal or -shm files.",
            "A single observation cannot prove checkpoint starvation; compare timestamped samples.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8")
        value = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"non-standard JSON constant: {x}")))
        result = analyze(value)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
