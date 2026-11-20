#!/usr/bin/env python3
"""Evaluate binary probability predictions from a validated JSON fixture."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def roc_auc(labels: list[int], scores: list[float]) -> float:
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("y_true must contain both classes")
    order = sorted(range(len(scores)), key=lambda index: scores[index])
    rank_sum = 0.0
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and scores[order[end]] == scores[order[start]]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        rank_sum += average_rank * sum(labels[order[index]] for index in range(start, end))
        start = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def average_precision(labels: list[int], scores: list[float]) -> float:
    positives = sum(labels)
    if not positives:
        raise ValueError("y_true must contain positive labels")
    thresholds = sorted(set(scores), reverse=True)
    true_positives = 0
    predicted_positives = 0
    total = 0.0
    previous_recall = 0.0
    for threshold in thresholds:
        group = [index for index, score in enumerate(scores) if score == threshold]
        true_positives += sum(labels[index] for index in group)
        predicted_positives += len(group)
        recall = true_positives / positives
        precision = true_positives / predicted_positives
        total += (recall - previous_recall) * precision
        previous_recall = recall
    return total


def evaluate(spec: dict[str, Any]) -> dict[str, Any]:
    labels = spec.get("y_true")
    scores = spec.get("y_score")
    threshold = spec.get("threshold", 0.5)
    if not isinstance(labels, list) or not labels or any(value not in (0, 1) or isinstance(value, bool) for value in labels):
        raise ValueError("y_true must be a non-empty list containing only integer 0 and 1")
    if not isinstance(scores, list) or len(scores) != len(labels):
        raise ValueError("y_score must be a list with the same length as y_true")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1 for value in scores):
        raise ValueError("y_score must contain finite probabilities between 0 and 1")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("threshold must be a finite number between 0 and 1")
    numeric_scores = [float(value) for value in scores]
    predictions = [1 if score >= threshold else 0 for score in numeric_scores]
    tp = sum(label == 1 and prediction == 1 for label, prediction in zip(labels, predictions))
    tn = sum(label == 0 and prediction == 0 for label, prediction in zip(labels, predictions))
    fp = sum(label == 0 and prediction == 1 for label, prediction in zip(labels, predictions))
    fn = sum(label == 1 and prediction == 0 for label, prediction in zip(labels, predictions))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    brier = sum((score - label) ** 2 for label, score in zip(labels, numeric_scores)) / len(labels)
    return {
        "status": "evaluated",
        "n": len(labels),
        "threshold": float(threshold),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "metrics": {
            "accuracy": (tp + tn) / len(labels),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc(labels, numeric_scores),
            "average_precision": average_precision(labels, numeric_scores),
            "brier_score": brier,
        },
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
        report = evaluate(read_object(args.input))
        write_json(args.output, report, args.force)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "n": report["n"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
