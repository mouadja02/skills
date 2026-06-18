# LLM Serving Checklist

## Inputs To Collect

- Model name and parameter count.
- Weight precision or quantization.
- GPU type, count, and memory.
- Expected requests per second.
- Concurrency target.
- Median and p95 input tokens.
- Median and p95 output tokens.
- Streaming requirement.
- Latency SLO: time to first token, p95 completion, or both.
- Shared prompt prefix percentage.

## Benchmark Metrics

- Time to first token.
- Inter-token latency.
- End-to-end latency p50, p95, p99.
- Tokens/sec per GPU.
- Queue time.
- GPU memory.
- GPU utilization.
- Error and timeout rate.
- Cost per 1,000 successful requests.

## Rollout Guardrails

- Canary one model and one traffic segment first.
- Keep a hosted fallback for critical workloads.
- Alert on queue time and timeout rate, not only process health.
- Pin model revisions and serving image versions.
- Record benchmark prompts with no secrets.
