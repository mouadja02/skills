---
name: vllm-serving-planner
description: Use when planning, reviewing, or tuning vLLM or OpenAI-compatible LLM serving for throughput, latency, KV-cache pressure, batching, quantization, prefix caching, or multimodal serving.
source: "https://github.com/vllm-project/vllm"
---

# vLLM Serving Planner

Plan LLM serving around workload shape: concurrency, context length, output length, model size, hardware, latency target, and cost. vLLM is usually strongest for high-throughput serving, but it still needs workload-specific tuning.

## Use When

- Deploying an OpenAI-compatible self-hosted model endpoint.
- Comparing vLLM with TGI, SGLang, llama.cpp, or hosted APIs.
- Throughput collapses under long context, high concurrency, or large output.
- You need batching, chunked prefill, prefix caching, quantization, tensor parallelism, or multimodal serving.

## Planning Steps

1. Capture workload: requests per second, concurrent users, input tokens, output tokens, streaming needs, latency SLO, and model list.
2. Estimate KV-cache pressure before choosing hardware.
3. Choose precision and quantization based on quality tolerance and GPU memory.
4. Enable prefix caching only when prompts share stable prefixes.
5. Tune max model length, max batched tokens, max sequences, and prefill behavior together.
6. Benchmark with real prompts, not only synthetic token counts.
7. Track p50, p95, p99 latency, time to first token, tokens/sec, GPU memory, queue time, and error rates.
8. Use disaggregated or staged serving for multimodal or any-to-any pipelines when one engine cannot efficiently host all stages.

## Capacity Helper

```bash
python skills/llm-tooling/vllm-serving-planner/scripts/vllm_capacity_planner.py \
  --model-gb 70 --gpu-gb 80 --input-tokens 4000 --output-tokens 1000 --concurrency 32
```

The helper is intentionally approximate. Use it to flag obvious capacity risk before running a real benchmark.

## Tuning Table

| Symptom | Likely lever |
| --- | --- |
| GPU memory full before target concurrency | Lower max model length, quantize, add GPUs, reduce concurrency |
| High queue time | Increase batching capacity or add replicas |
| Slow first token | Tune prefill, use prefix caching, reduce prompt length |
| Slow decode | Check model size, parallelism, quantization, GPU utilization |
| Multimodal pipeline stalls | Split stages and batch each stage independently |

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Sizing only model weights | Include KV cache and activation overhead |
| Benchmarking one request at a time | Test expected concurrency and prompt lengths |
| Turning on every optimization | Add one lever at a time and record deltas |
| Ignoring workload variance | Test short, median, long, and worst-case prompts |
| Comparing systems without SLOs | Decide throughput, latency, cost, and model-quality priorities first |

## References

- GitHub: vllm-project/vllm - https://github.com/vllm-project/vllm
- arXiv: Efficient Memory Management for LLM Serving with PagedAttention - https://arxiv.org/abs/2309.06180
- arXiv: vLLM-Omni - https://arxiv.org/abs/2602.02204
- GitHub: vllm-project/vllm-omni - https://github.com/vllm-project/vllm-omni
- GitHub: sgl-project/sglang - https://github.com/sgl-project/sglang
