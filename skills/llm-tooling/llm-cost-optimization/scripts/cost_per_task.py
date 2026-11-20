#!/usr/bin/env python3
"""Cost per completed task from LLM usage logs, with what-if levers.

Reads JSON Lines, one API response's usage per line. Recognised fields:
  Anthropic: input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens
  OpenAI:    prompt_tokens, completion_tokens, prompt_tokens_details.cached_tokens
  Optional:  task_id (groups requests into one task), success (true/false), batch (true/false)
A line may hold the usage object directly or under a "usage" key.

Prices are per million tokens and must come from the provider's current pricing page; nothing is
hard-coded. Cache multipliers default to Anthropic's documented 5-minute-TTL write (1.25x) and a
0.1x read; pass the values for your model and provider.

Usage:
  python3 cost_per_task.py usage.jsonl --input-price 2 --output-price 10 \
      [--cache-read-mult 0.1] [--cache-write-mult 1.25] [--batch-discount 0.5] [--json]

Standard library only.
"""

import argparse
import json
import sys
from collections import defaultdict


def tokens(record):
    usage = record.get("usage", record)
    if "prompt_tokens" in usage or "completion_tokens" in usage:
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
        return {
            "input": max((usage.get("prompt_tokens") or 0) - cached, 0),
            "output": usage.get("completion_tokens") or 0,
            "cache_read": cached,
            "cache_write": 0,
        }
    return {
        "input": usage.get("input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "cache_write": usage.get("cache_creation_input_tokens") or 0,
    }


def cost(t, args, batch=False):
    per = 1_000_000
    value = (
        t["input"] * args.input_price
        + t["cache_write"] * args.input_price * args.cache_write_mult
        + t["cache_read"] * args.input_price * args.cache_read_mult
        + t["output"] * args.output_price
    ) / per
    return value * (1 - args.batch_discount) if batch else value


def load(path):
    records = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as err:
                sys.exit(f"{path}:{number}: not valid JSON ({err.msg})")
    if not records:
        sys.exit(f"{path}: no usage records")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("usage_file")
    parser.add_argument("--input-price", type=float, required=True, help="USD per million uncached input tokens")
    parser.add_argument("--output-price", type=float, required=True, help="USD per million output tokens")
    parser.add_argument("--cache-read-mult", type=float, default=0.1, help="cache read price as a multiple of input price")
    parser.add_argument("--cache-write-mult", type=float, default=1.25, help="cache write price as a multiple of input price")
    parser.add_argument("--batch-discount", type=float, default=0.5, help="discount for batch requests (0.5 = 50%% off)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = load(args.usage_file)
    totals = defaultdict(int)
    by_task = defaultdict(lambda: {"cost": 0.0, "success": None, "requests": 0})
    spend = {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    actual = all_sync = 0.0
    for index, record in enumerate(records):
        t = tokens(record)
        for key, value in t.items():
            totals[key] += value
        batch = bool(record.get("batch"))
        request_cost = cost(t, args, batch)
        actual += request_cost
        all_sync += cost(t, args, False)
        spend["input"] += t["input"] * args.input_price / 1e6
        spend["cache_write"] += t["cache_write"] * args.input_price * args.cache_write_mult / 1e6
        spend["cache_read"] += t["cache_read"] * args.input_price * args.cache_read_mult / 1e6
        spend["output"] += t["output"] * args.output_price / 1e6
        task = by_task[str(record.get("task_id", index))]
        task["cost"] += request_cost
        task["requests"] += 1
        if "success" in record:
            task["success"] = bool(record["success"]) if task["success"] is None else task["success"] and bool(record["success"])

    prompt_side = totals["input"] + totals["cache_read"] + totals["cache_write"]
    hit_rate = totals["cache_read"] / prompt_side if prompt_side else 0.0
    succeeded = [t for t in by_task.values() if t["success"]]
    known = [t for t in by_task.values() if t["success"] is not None]
    # What-if: everything sent as batch; every prompt-side token read from cache.
    batch_all = all_sync * (1 - args.batch_discount)
    ideal_cache = {**totals, "input": 0, "cache_write": 0, "cache_read": prompt_side}
    ideal_cache_cost = cost(ideal_cache, args)
    result = {
        "requests": len(records),
        "tasks": len(by_task),
        "tokens": dict(totals),
        "cache_hit_rate": round(hit_rate, 4),
        "cost_usd": round(actual, 6),
        "cost_share": {k: round(v / sum(spend.values()), 4) if sum(spend.values()) else 0 for k, v in spend.items()},
        "cost_per_request": round(actual / len(records), 6),
        "cost_per_task": round(actual / len(by_task), 6),
        "cost_per_successful_task": round(actual / len(succeeded), 6) if succeeded else None,
        "success_rate": round(len(succeeded) / len(known), 4) if known else None,
        "what_if": {
            "all_requests_batched_usd": round(batch_all, 6),
            "prompt_fully_cached_usd_ceiling": round(ideal_cache_cost, 6),
        },
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"{result['requests']} requests in {result['tasks']} tasks, cost ${result['cost_usd']:.4f}")
    print(f"  per request ${result['cost_per_request']:.5f} | per task ${result['cost_per_task']:.5f}", end="")
    if result["cost_per_successful_task"] is not None:
        print(f" | per successful task ${result['cost_per_successful_task']:.5f} (success {result['success_rate']:.0%})")
    else:
        print(" | add 'success' to records for cost per completed task")
    print(f"  cache hit rate {hit_rate:.1%} of prompt tokens")
    print("  spend by token type: " + ", ".join(f"{k} {v:.0%}" for k, v in result["cost_share"].items()))
    print(f"  what if every request were batched: ${batch_all:.4f}")
    print(f"  ceiling if every prompt token were a cache read: ${ideal_cache_cost:.4f} (unreachable; bounds the caching lever)")


if __name__ == "__main__":
    main()
