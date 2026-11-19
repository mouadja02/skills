#!/usr/bin/env python3
"""Approximate vLLM memory pressure estimator."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-gb", type=float, required=True, help="model weights in GiB")
    parser.add_argument("--gpu-gb", type=float, required=True, help="total GPU memory in GiB")
    parser.add_argument("--input-tokens", type=int, required=True)
    parser.add_argument("--output-tokens", type=int, required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--kv-kb-per-token", type=float, default=64.0, help="rough KV cache KiB per token per request")
    parser.add_argument("--overhead", type=float, default=1.15, help="runtime overhead multiplier")
    args = parser.parse_args()

    tokens_per_request = args.input_tokens + args.output_tokens
    kv_gb = tokens_per_request * args.concurrency * args.kv_kb_per_token / (1024 * 1024)
    estimated = (args.model_gb + kv_gb) * args.overhead
    headroom = args.gpu_gb - estimated

    print(f"tokens/request: {tokens_per_request:,}")
    print(f"estimated kv cache: {kv_gb:.2f} GiB")
    print(f"estimated total: {estimated:.2f} GiB")
    print(f"gpu memory: {args.gpu_gb:.2f} GiB")
    print(f"headroom: {headroom:.2f} GiB")
    print("verdict:", "risk" if headroom < args.gpu_gb * 0.1 else "plausible")
    return 0 if headroom >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
