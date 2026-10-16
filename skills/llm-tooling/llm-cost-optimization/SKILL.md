---
name: llm-cost-optimization
description: >-
  Use when an application that calls an LLM API costs too much, needs a cost forecast, or is about to
  ship at scale — "the bill is too high", "make this cheaper", "should we route to a smaller model".
  Profiles spend per completed task from usage logs, then applies levers in order: prompt caching,
  input-token hygiene, agent-loop hygiene, output control, and batch APIs before effort, budget, and
  model-routing tradeoffs validated on an eval. Provider-agnostic, with Anthropic specifics.
version: "1.0.0"
license: MIT
source: "https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence; https://arxiv.org/abs/2305.05176; https://arxiv.org/abs/2406.18665; https://arxiv.org/abs/2310.05736"
attribution: "Written for this collection from Anthropic's cost-optimization and prompt-caching guides and the FrugalGPT, RouteLLM, and LLMLingua papers"
---

# LLM Cost Optimization

Optimize **cost per completed task**, not cost per request. A cheaper request that needs more turns,
retries, or a human fix is not cheaper. Work the free levers first — they cut cost without touching
quality — and treat every lever that trades capability for cost as an experiment that must pass an eval.

## When to Use

- An LLM feature's API spend is too high, growing faster than traffic, or unknown.
- Before a launch or a traffic increase, to forecast and cap spend.
- Someone proposes "just use a smaller model" or a router, and you need to know if it pays.
- Agent loops whose cost grows with every turn.

Not for a coding agent's own usage limits (Claude Code, Cursor) — use `coding-agent-token-efficiency`.

## Workflow

```
Cost pass:
- [ ] 0. Quality bar and baseline agreed
- [ ] 1. Token profile built
- [ ] 2. Free wins applied and verified
- [ ] 3. Tradeoffs tested on the eval (only with approval)
- [ ] 4. Report written
```

### 0. Agree the quality bar and baseline

Ask the user, do not assume:

- What counts as a completed task, and how is it checked (tests, a validator, a rubric, human review)?
- Which routes or features are in scope, and which are latency-sensitive?
- Is there an eval set? If not, offer to build a small one: 20–30 real requests, frozen, each with a
  pass/fail check. Without one, only the free levers can be applied.

Every run that calls the model spends money. Get approval for a measurement budget before running
baselines or sweeps.

### 1. Build the token profile

Log `usage` from every response (it is free to add and is the measurement channel for everything else),
tagged with a task id and the outcome. Then:

```bash
python3 scripts/cost_per_task.py usage.jsonl --input-price <USD/MTok> --output-price <USD/MTok> \
    --cache-read-mult <x> --cache-write-mult <x> --batch-discount <fraction>
```

The script (standard library only, path relative to this skill) accepts Anthropic or OpenAI usage
fields and reports cost per request, per task, and per successful task; cache hit rate; spend by token
type; and two ceilings: all traffic batched, and every prompt token served from cache. Take prices from
the provider's pricing page today — never from memory.

Read the profile: which token type dominates, how deep the loops run, how much of the prompt repeats,
and which routes have no user waiting.

### 2. Apply the free wins, in this order

**2.1 Prompt caching — first, and it stays on.** Every turn re-sends the whole prefix; caching reprices
the repeated part. Caching is a prefix match, so any changed byte invalidates everything after it.

- Order the prompt by stability: tools → system prompt → static context → conversation → the volatile
  tail (timestamps, request ids, the question). Never put a timestamp or a random id in the system prompt.
- Keep tool order and JSON key order deterministic; do not toggle tools, model, or reasoning settings
  mid-conversation — each one restarts the cache.
- Verify from usage, not code review: `cache_read_input_tokens` (Anthropic) or `cached_tokens` (OpenAI)
  should dominate on a warm loop. Zero hits on repeated identical prefixes means a silent invalidator.

Anthropic specifics (confirm on the prompt-caching page before computing): explicit `cache_control`
breakpoints (at most 4 per request) or top-level automatic caching; a 5-minute TTL by default or 1 hour
on request; cache writes cost 1.25× the input price for 5 minutes and 2× for 1 hour, reads about 0.1×
(lower on some current models); prefixes below a model-dependent minimum (512 to 4,096 tokens) silently
do not cache. With the 5-minute TTL two requests already break even; the 1-hour TTL needs three, so use
it only when gaps between requests regularly exceed five minutes. Other providers cache automatically
or explicitly with different minimums and discounts — read their caching page.

**2.2 Input-token hygiene.**

- Move large reference documents behind a tool or retrieval step if most requests use only a section;
  keep them inline (and cached) if most requests need most of it.
- Delete prose that restates tool schemas. Load rarely used tool definitions on demand (tool search /
  deferred loading) once schemas pass roughly 10K tokens.
- Downscale images to what the task needs: vision cost scales with pixel area, not information.
- Give list tools `limit`, `fields`, and date filters; prefer narrow accessors to data dumps.
- Count tokens on unbounded user input before sending it, and route oversize payloads elsewhere.
- Prompt compression (LLMLingua and successors) helps on long, redundant retrieved context. Test it on
  the eval: compression that drops a constraint costs more than it saves.

**2.3 Agent-loop hygiene** (only when loops are long and tool results pile up).

- Push self-contained, bulky steps into a sub-call that returns one summary line.
- Use server-side compaction or context clearing only to make room in the window. Each pass rewrites the
  cached conversation, so trigger it rarely and in large batches.

**2.4 Output control.**

- Specify the exact output shape with an example; ask for diffs, not whole files.
- `max_tokens` is a backstop, not a tuning knob: the model never sees it, and a truncated answer is a
  failed attempt you pay for twice. Set it generously and treat `stop_reason: max_tokens` as a failure.
- Add a stop sentinel for "cannot proceed" cases so the model stops instead of explaining.

**2.5 Batch everything no one is waiting for.** Evaluations, backfills, nightly jobs. Anthropic's
Message Batches API is 50% off every token, including cache reads and writes; results arrive within 24
hours. Batch requests are single-shot, so tool loops do not batch without restructuring.

### 3. Test the tradeoffs (one at a time, on the eval)

From here every lever can lower quality. Present each with its measured effect and apply it only when
the user accepts the trade.

1. **Effort / reasoning level first.** Sweep it on the current model before changing models. Research
   and Q&A curves are often flat (a lower level holds accuracy for much less); long-horizon coding loses
   a few points per step down. Change it between conversations, not mid-conversation.
2. **Re-run failures at higher effort.** When a cheap checker exists, run everything at a low setting and
   retry only the failures higher.
3. **Task budgets / token ceilings** where the provider supports a model-visible budget; set from the
   90th-percentile task, then tighten while watching pass rate.
4. **Model choice, last.** First check whether a newer model in the same tier at lower effort beats the
   old one. Then try one tier down, re-sweeping effort. Compare on the hardest tenth of tasks — the tail
   decides the bill.
5. **Routing and cascades** (FrugalGPT, RouteLLM): send easy requests to a cheap model and escalate on
   low confidence or a failed check. The papers report large savings — FrugalGPT matched its best single
   model's accuracy at up to 98% lower cost on its benchmarks; RouteLLM cut cost more than 2× without
   quality loss in some settings — but caches are per model, so a cascade forfeits cache reuse across
   tiers, and a bad router silently degrades quality. Build one only after the simpler levers, and only
   with an eval and a fallback.

### 4. Report

```markdown
# LLM cost review — <app / route>

Baseline: <cost per completed task>, <pass rate>, <requests/day>, measured <date> from <source>
Prices used: <model, $/MTok in/out, cache multipliers, source URL, date>

| Lever | Type | Expected saving | Measured | Quality | Decision |
| --- | --- | ---: | ---: | --- | --- |
| Prompt caching (static prefix) | free | | | unchanged | applied |
| Batch nightly summarization | free | | | unchanged | applied |
| Effort high → medium on /search | tradeoff | | | -1 task of 30 | proposed |

Skipped levers and why: <list>
Next: <approval or eval needed>
```

"No changes recommended" is a valid outcome when the profile shows no lever with headroom.

## Gotchas

- **Validate caching with a warm cache.** The first request writes at a premium; measure from the
  second request on, or caching looks like a regression.
- **Caches are scoped** (per model, and per workspace or organization depending on provider). Traffic
  split across keys or workspaces caches separately.
- **Concurrency defeats caching:** parallel requests sent before the first finishes all miss.
- **Prices change.** Never ship a cost model with remembered prices; cite the pricing page and the date.
- **Do not cap output to save money** without checking pass rate; truncated answers inflate cost per
  completed task.

## Related skills

`coding-agent-token-efficiency`, `context-compression`, `agentic-eval`, `eval-driven-dev`,
`amazon-bedrock` (Bedrock pricing, caching, and batch specifics).

## Sources

- Anthropic, [Optimizing for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence),
  [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
  [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing),
  [Pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- Chen, Zaharia & Zou, *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving
  Performance*, [arXiv:2305.05176](https://arxiv.org/abs/2305.05176).
- Ong et al., *RouteLLM: Learning to Route LLMs with Preference Data*, [arXiv:2406.18665](https://arxiv.org/abs/2406.18665).
- Jiang et al., *LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models*,
  [arXiv:2310.05736](https://arxiv.org/abs/2310.05736).
