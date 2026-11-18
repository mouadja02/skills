#!/usr/bin/env python3
"""Create a binary A/B-test design from a validated JSON specification."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from statistics import NormalDist
from typing import Any


def require_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    return float(value)


def design_experiment(spec: dict[str, Any]) -> dict[str, Any]:
    baseline = require_number(spec, "baseline_rate")
    relative_mde = require_number(spec, "relative_mde")
    alpha = require_number(spec, "alpha")
    power = require_number(spec, "power")
    if not 0 < baseline < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if relative_mde <= 0:
        raise ValueError("relative_mde must be greater than 0")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")

    treatment = baseline * (1 + relative_mde)
    if treatment >= 1:
        raise ValueError("baseline_rate * (1 + relative_mde) must be less than 1")

    difference = treatment - baseline
    midpoint = (baseline + treatment) / 2
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    numerator = (
        z_alpha * math.sqrt(2 * midpoint * (1 - midpoint))
        + z_power * math.sqrt(baseline * (1 - baseline) + treatment * (1 - treatment))
    ) ** 2
    per_variant = math.ceil(numerator / difference**2)

    return {
        "status": "designed",
        "test": "two-sided two-proportion z-test",
        "baseline_rate": baseline,
        "target_rate": treatment,
        "absolute_mde": difference,
        "relative_mde": relative_mde,
        "alpha": alpha,
        "power": power,
        "sample_size_per_variant": per_variant,
        "total_sample_size": per_variant * 2,
        "assumptions": [
            "equal allocation",
            "independent user-level assignment",
            "one pre-registered primary binary metric",
            "fixed-horizon analysis without repeated peeking",
        ],
    }


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


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
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args()
    try:
        report = design_experiment(read_object(args.input))
        write_json(args.output, report, args.force)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
