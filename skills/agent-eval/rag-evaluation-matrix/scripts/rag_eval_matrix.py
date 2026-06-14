#!/usr/bin/env python3
"""Summarize RAG evaluation JSON files into a compact decision matrix."""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def as_bool(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes"}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: rag_eval_matrix.py results/*.json", file=sys.stderr)
        return 2

    rows = []
    for arg in sys.argv[1:]:
        data = json.loads(Path(arg).read_text(encoding="utf-8"))
        rows.extend(data if isinstance(data, list) else [data])

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pipeline", "unknown"))].append(row)

    print("| Pipeline | N | Correct | Answerability | Median latency | Cost / correct |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for pipeline, items in sorted(grouped.items()):
        n = len(items)
        correct = sum(as_bool(item.get("correct")) for item in items)
        answerable = sum(as_bool(item.get("answerable_correct")) for item in items)
        latencies = [float(item.get("latency_ms", 0) or 0) for item in items]
        total_cost = sum(float(item.get("cost_usd", 0) or 0) for item in items)
        cost_per_correct = total_cost / correct if correct else 0
        print(
            f"| {pipeline} | {n} | {correct / n:.1%} | {answerable / n:.1%} | "
            f"{statistics.median(latencies):.0f} ms | ${cost_per_correct:.4f} |"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
