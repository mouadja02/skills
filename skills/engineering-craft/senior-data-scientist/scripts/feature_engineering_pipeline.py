#!/usr/bin/env python3
"""Fit leakage-safe tabular transforms on a training prefix and transform a holdout."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def string_list(spec: dict[str, Any], key: str) -> list[str]:
    value = spec.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{key} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{key} contains duplicates")
    return value


def finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must contain finite numbers or null")
    return float(value)


def parse_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must contain ISO-8601 strings")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} contains an invalid ISO-8601 timestamp") from exc


def fit_and_transform(spec: dict[str, Any]) -> dict[str, Any]:
    records = spec.get("records")
    if not isinstance(records, list) or len(records) < 2 or any(not isinstance(row, dict) for row in records):
        raise ValueError("records must contain at least two JSON objects")
    split = spec.get("split_index")
    if isinstance(split, bool) or not isinstance(split, int) or not 0 < split < len(records):
        raise ValueError("split_index must leave non-empty training and holdout partitions")
    numeric = string_list(spec, "numeric")
    categorical = string_list(spec, "categorical")
    datetimes = string_list(spec, "datetime")
    all_fields = numeric + categorical + datetimes
    if len(all_fields) != len(set(all_fields)):
        raise ValueError("a field may appear in only one feature group")
    if not all_fields:
        raise ValueError("at least one feature field is required")

    train = records[:split]
    parameters: dict[str, Any] = {"numeric": {}, "categorical": {}, "datetime": datetimes}
    for field in numeric:
        values = [finite_number(row[field], field) for row in train if row.get(field) is not None]
        if not values:
            raise ValueError(f"training partition has no numeric values for {field}")
        fill = median(values)
        completed = [fill if row.get(field) is None else finite_number(row[field], field) for row in train]
        mean = sum(completed) / len(completed)
        variance = sum((value - mean) ** 2 for value in completed) / len(completed)
        parameters["numeric"][field] = {"median": fill, "mean": mean, "std": math.sqrt(variance)}
    for field in categorical:
        values = [row.get(field) for row in train]
        if any(value is not None and not isinstance(value, str) for value in values):
            raise ValueError(f"{field} must contain strings or null")
        observed = [value for value in values if value is not None]
        if not observed:
            raise ValueError(f"training partition has no categorical values for {field}")
        counts = Counter(observed)
        mode = sorted(counts, key=lambda value: (-counts[value], value))[0]
        vocabulary = sorted(set(observed))
        parameters["categorical"][field] = {"mode": mode, "vocabulary": vocabulary}
    for field in datetimes:
        for row in records:
            parse_datetime(row.get(field), field)

    def transform(row: dict[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for field, fitted in parameters["numeric"].items():
            raw = fitted["median"] if row.get(field) is None else finite_number(row[field], field)
            output[f"{field}__scaled"] = 0.0 if fitted["std"] == 0 else (raw - fitted["mean"]) / fitted["std"]
        for field, fitted in parameters["categorical"].items():
            raw = fitted["mode"] if row.get(field) is None else row[field]
            if not isinstance(raw, str):
                raise ValueError(f"{field} must contain strings or null")
            for category in fitted["vocabulary"]:
                output[f"{field}__{category}"] = 1 if raw == category else 0
            output[f"{field}__unknown"] = 0 if raw in fitted["vocabulary"] else 1
        for field in datetimes:
            stamp = parse_datetime(row.get(field), field)
            weekday = stamp.weekday()
            month = stamp.month - 1
            output[f"{field}__dow_sin"] = math.sin(2 * math.pi * weekday / 7)
            output[f"{field}__dow_cos"] = math.cos(2 * math.pi * weekday / 7)
            output[f"{field}__month_sin"] = math.sin(2 * math.pi * month / 12)
            output[f"{field}__month_cos"] = math.cos(2 * math.pi * month / 12)
        return output

    return {
        "status": "transformed",
        "split_index": split,
        "fit_scope": "training partition only",
        "parameters": parameters,
        "train": [transform(row) for row in train],
        "holdout": [transform(row) for row in records[split:]],
    }


def write_json(path: Path, value: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"output already exists: {path}; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--output", "-o", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        report = fit_and_transform(read_object(args.input))
        write_json(args.output, report, args.force)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "train_rows": len(report["train"]), "holdout_rows": len(report["holdout"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
