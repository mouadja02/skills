---
name: long-horizon-operational-policy-evaluation
description: >-
  Use when comparing agents or policies in a persistent simulator where actions create future commitments, delayed outcomes, or shared-resource constraints. Freezes matched worlds, verifies resumable runs, separates censored seasons from completed scores, and produces an economic and trajectory decision report.
version: "1.0.0"
license: MIT
source: "https://arxiv.org/abs/2611.17933; https://arxiv.org/abs/2603.16453; https://arxiv.org/abs/2607.28956; https://arxiv.org/abs/2603.23638"
attribution: "Original workflow informed by OutfitterBench, RetailBench, MerchantBench, and EnterpriseArena"
---

# Long-Horizon Operational Policy Evaluation

Compare policies in persistent worlds without rewarding leakage, incomplete seasons, or mismatched environments. The output is a replayable campaign and a decision report—not a leaderboard assembled from incomparable runs.

## When to Use

- An agent manages inventory, capital, capacity, reservations, schedules, or other resources across many steps.
- Earlier actions create obligations or constrain later choices.
- Outcomes arrive after delays or a separate settlement period.
- A policy, prompt, model, or harness change needs comparison against a deterministic baseline on matched worlds.
- Interrupted runs must resume without changing the experiment.

Do **not** activate for independent stateless questions, one-shot tasks with immediate gold labels, or ordinary output-quality evaluation. Use a paired task suite with correctness, latency, and cost instead. Do not invent checkpoints, settlement, opportunity cost, or persistent-world metrics where none exist.

## Required Outputs

Create one private campaign directory containing:

1. `campaign.yaml` — frozen identities, eligibility claim, information boundary, seeds, horizon, budgets, stop rules, and scoring rules;
2. `runs.jsonl` — one planned run and exactly one terminal status per policy × seed;
3. `events/` and `checkpoints/` — append-only receipts plus resumable state evidence;
4. `metrics/` — per-run feasibility, service, resource, economic, and execution metrics;
5. `replay/` — deterministic replay or bounded-counterfactual evidence, when enabled;
6. `decision.md` — matched comparisons, exclusions, censored runs, limitations, and `PROMOTE`, `HOLD`, or `REJECT`.

Start with [the campaign manifest](templates/campaign-manifest.yaml) and [decision report](templates/decision-report.md).

## Workflow

### 1. Prove the campaign is eligible

Write one sentence naming all three:

- **persistent state** changed by policy actions;
- **future coupling** through commitments, delayed effects, or shared resources;
- **terminal interpretation** such as settlement, runoff, or a declared censoring boundary.

If any element is absent, stop and use a simpler task-suite evaluation. A long prompt or many turns alone does not qualify.

### 2. Freeze the world and decision

Before any measured run, record immutable identities for:

- simulator source and configuration;
- dataset, scenario, event stream, and transformation code;
- policy code/prompt, model/provider, tools, and harness;
- seed set, decision horizon, settlement horizon, and clock;
- observation/action schemas, retry policy, limits, and cost rates;
- every input checksum and the decision this campaign supports.

A display name or semantic version is insufficient when bytes can differ. Use a commit, digest, or content hash. Never pool runs whose comparison identity differs; quarantine them into separate groups.

### 3. Define identical information and action boundaries

List what each policy may observe at each decision point and every allowed action. Enforce the same public information, tool surface, timing, rate limits, and resource budgets across arms unless that difference is the treatment.

Add negative controls for future information. A policy that reads tomorrow's hidden demand, post-decision outcomes, another arm's trace, or a later checkpoint is contaminated. Preserve it for leakage diagnosis, but exclude it from deployable policy scoring.

### 4. Establish deterministic controls

Include at least:

- a no-agent or scripted environment smoke policy;
- a deterministic rule baseline;
- the candidate agent or policy.

Prove on a short synthetic world that fixed inputs and a fixed policy reproduce the same event receipts, checkpoint digest, final state, and metrics. A baseline need not be optimal; it anchors feasibility, economics, and operational cost.

### 5. Plan matched worlds

Run every eligible policy on the same prespecified seeds or scenario IDs. Keep repetitions distinct from seeds. Randomize execution order when infrastructure drift is plausible, but never change world identity.

Predeclare:

- minimum completed matched pairs;
- hard feasibility and safety gates;
- utility/economic metrics and uncertainty method;
- run, model-call, wall-clock, token, and monetary budgets;
- failure, pause, retry, and censoring rules.

Do not replace a failed run with an easier seed or report only surviving runs.

### 6. Make interruption and resume testable

A checkpoint must bind:

- simulator, data, policy, and schema identities;
- current logical time and original terminal horizons;
- state digest and last committed event sequence;
- RNG state or deterministic event cursor;
- cumulative commitments, resources, costs, and model/tool usage.

Pause at a declared absolute point, copy the checkpoint to a clean process, and resume. Verify:

1. the pre-resume ledger prefix is unchanged;
2. no event is skipped or duplicated;
3. replaying from the start reaches the same boundary digest;
4. resumed and uninterrupted controls end with equivalent receipts, state, and metrics.

A pause changes neither the decision horizon nor settlement. If equivalence fails, mark the run `integrity_failed`; do not score it.

### 7. Run and account for every attempt

Use independent run directories. Append immutable event/tool receipts before advancing the checkpoint. Record planned, running, paused, resumed, completed, censored, contaminated, integrity-failed, and infrastructure-failed states explicitly.

For each attempt capture model/tool calls, retries, latency, tokens, monetary cost, and stop reason. A provider success code or plausible final prose is not run verification. Read the persisted state, ledger, and terminal marker back.

### 8. Score completed seasons conservatively

Report dimensions separately:

- **feasibility:** hard constraint and commitment violations;
- **service:** fulfillment, lateness, cancellation, abandonment, or SLA outcomes;
- **resources:** utilization, idle reserve, bottlenecks, and capital tied up;
- **economics:** cash flow, obligations, asset/resource value, penalties, and terminal value;
- **execution:** calls, retries, latency, tokens, cost, failures, and interventions.

Only a run that reaches the frozen terminal boundary—including required settlement—receives a final economic score. An interrupted or unfinished run is **censored**, not zero and not safe. Partial telemetry may support failure analysis but may not rank policies against completed seasons.

Aggregate only matched, identity-compatible completed runs. Show per-seed values, contributing pair count, dispersion or confidence interval, and missing/censored counts. Do not let an average utility score compensate for a hard feasibility breach.

### 9. Keep diagnostics distinct from outcomes

Trajectory diagnostics explain behavior; they do not silently redefine reward. Label each result as:

- observed violation;
- supported association;
- counterfactual witness;
- bounded search with no witness;
- unsupported or undetermined.

A bounded replay that reaches its search cap without an improvement proves only “no witness found within the tested set.” It is not zero opportunity and not optimality. Keep expensive counterfactual replay opt-in, CPU-bounded, source-matched, and network-free where possible.

### 10. Decide from the matched evidence

Use the decision template:

- **PROMOTE** only when identity, information, integrity, completion, hard gates, and prespecified utility/cost rules pass;
- **HOLD** for insufficient matched completions, censored evidence, unavailable diagnostics, or uncertain trade-offs;
- **REJECT** for leakage, integrity failure, hard constraint regression, or unacceptable completed-run performance.

Preserve replay inputs, receipts, hashes, exclusions, and limitations. Do not publish raw traces containing prompts, credentials, private data, or proprietary simulator inputs.

## Verification Scenarios

### Normal

Run a deterministic baseline and one candidate on the same two seeds in a 30-day world plus 5 settlement days. Pause the baseline at Day 10 and resume from its checkpoint. Pass only when identities and boundaries match, resume equals uninterrupted replay, all terminal runs settle, and the report includes feasibility, service, resource, economic, calls, retries, latency, tokens, and cost.

### Difficult

Inject one environment-version mismatch, one policy with future-weather access, one run interrupted before settlement, and one bounded replay that reaches its cap without a witness. Pass only when the report quarantines the version mismatch, invalidates the leaked run for policy scoring, censors the incomplete run, labels the replay result undetermined, and proposes matched clean reruns.

### Should Not Activate

Compare two models on independent classification questions with immediate gold labels. Recommend paired correctness, latency, and cost analysis. Do not create commitment ledgers, checkpoints, settlement, or opportunity-cost claims.

## Completion Gate

Complete only when:

- eligibility and the decision are explicit;
- all comparison identities and information boundaries are frozen;
- deterministic and resume-equivalence controls pass;
- every planned attempt has one terminal status;
- final scores include only completed, settled, matched worlds;
- leakage, mismatches, censored runs, and undetermined diagnostics are visible;
- execution cost and uncertainty accompany policy outcomes;
- the decision links every claim to persisted evidence.

## Guardrails

- Use synthetic or licensed data and disposable worlds by default.
- Never run downloaded simulator code before review or use live operational systems without authorization.
- Keep credentials out of manifests, traces, checkpoints, and reports.
- Separate code licenses from dataset and service terms.
- Do not claim production safety, optimality, causality, or generalization beyond the frozen campaign.

## Related Skills

- `harness-benchmarking` for general harness throughput and quality comparisons.
- `agent-trajectory-diagnostics` for trajectory-level failure analysis without a persistent-world campaign.
- `ordinary-hazard-agent-intervention-evaluation` for causal intervention tests around a reproduced incident.
- `business-simulation` for operating a simulated venture rather than evaluating policies.

## Sources

- [OutfitterBench](https://arxiv.org/abs/2611.17933) and [reference implementation](https://github.com/adminblackjack/OutfitterBench)
- [RetailBench](https://arxiv.org/abs/2603.16453)
- [MerchantBench](https://arxiv.org/abs/2607.28956)
- [EnterpriseArena](https://arxiv.org/abs/2603.23638)
