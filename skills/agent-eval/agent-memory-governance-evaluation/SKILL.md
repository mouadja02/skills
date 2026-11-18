---
name: agent-memory-governance-evaluation
description: >-
  Use when comparing persistent agent memory backends or changing recall, retention, correction, deletion, or isolation policy. Designs a synthetic, license-aware governance campaign; holds the agent/model constant; verifies traces and lifecycle effects; and returns per-dimension release evidence instead of one score.
version: "1.0.0"
license: MIT
source: "https://arxiv.org/abs/2611.20144; https://github.com/milatechtransfer/heams"
attribution: "Original workflow informed by HEAMS by Goel et al. and recurring Mem0/LangGraph lifecycle failures"
---

# Agent Memory Governance Evaluation

Evaluate persistent memory as a custodian of user information, not only as a retrieval component. Produce a reproducible campaign, machine-readable evidence, separate dimension reports, and an explicit release decision.

## When to Use

Use this skill when:

- adopting or replacing a persistent agent memory backend;
- changing an embedding model, memory prompt, recall policy, retention rule, correction path, or deletion implementation;
- investigating cross-user disclosure, poisoning, stale recall, failed correction, or incomplete erasure;
- adding a governance regression gate around a memory plugin.

Do **not** use it for session-only scratchpads, ordinary RAG retrieval evaluation, selecting a memory architecture before persistence is needed, or implementing the store itself. Route those jobs to `memory-systems`, `rag-evaluation-matrix`, or `provenance-grounded-memory`. Never install a framework, use real user memory, download gated/non-commercial data, spend model budget, or alter a live store merely because this skill activated.

## Required Outputs

Create one campaign directory containing:

1. `campaign.yaml` — frozen systems, models, policies, datasets, licenses, controls, budgets, and stop rules;
2. `runs.jsonl` plus execution traces — one terminal record per planned scenario;
3. per-dimension reports for performance, efficiency, privacy, security, correction, deletion, transparency, and retention;
4. a redacted evidence index joining every finding to a run and trace;
5. `decision.md` — `RELEASE`, `HOLD`, or `REJECT`, with failed rule IDs and trade-offs.

Start from [the campaign manifest](templates/campaign-manifest.yaml), [benchmark selection matrix](references/benchmark-selection.md), and [decision record](templates/decision-record.md).

## Workflow

### 1. Freeze the decision and threat model

Name the release decision, candidate backend, current baseline, owner, date, and maximum acceptable cost. Inventory every place memory can persist or leak: canonical rows, vectors, derived summaries, caches, queues, replicas, exports, traces, logs, snapshots, and backups.

Define non-compensatory hard gates before running. Privacy, authorization, deletion, and retention failures cannot be offset by better recall or latency.

### 2. Inventory dependencies and data terms

For every benchmark or fixture, record the exact version/commit, code license, dataset license, access condition, intended use, and redistribution rule. Exclude any dataset whose terms do not fit the campaign. A framework license does not override benchmark dataset terms.

Default to synthetic fixtures. Use random per-run canaries, fictional users, disposable namespaces, and no real credentials or personal data. Keep plaintext canaries in the assertion process only; reports contain opaque IDs and keyed digests.

### 3. Define controlled arms

Include at minimum:

- **A0 no-memory control** — sizes what the model can answer without persistence;
- **A1 current baseline** — the deployed or simplest accepted memory system;
- **A2 candidate** — the backend or policy under review.

Hold constant the agent instructions, model/version, evaluator, prompts, event stream, query order, retrieval budget, clock, concurrency, retries, and resource limits. Record unavoidable backend-specific settings instead of pretending they are equal.

### 4. Select separate dimension scenarios

Use [the matrix](references/benchmark-selection.md). Every dimension needs at least one normal scenario and one lifecycle or adversarial scenario. Do not collapse results into a weighted total.

Required synthetic regression cases:

- correct recall, temporal update, and abstention;
- cross-user and cross-tenant canaries;
- poisoned memory treated as untrusted data rather than authority;
- correction that removes stale answers without corrupting history;
- explicit deletion followed by readback from primary and derived stores;
- TTL expiry, retention holds, restart, reindex, and replay resurrection checks;
- provenance and lifecycle-state visibility;
- latency, token/model calls, storage, and run cost.

### 5. Validate the adapter before the campaign

Use disposable storage. Verify retain, recall, update, delete, tenant scoping, stable identifiers, and cleanup independently of the agent. Confirm plugin discovery and effective configuration. A successful API response is not verification: read state back through every relevant interface.

If using HEAMS, pin the repository/release and memory plugin, then run its memory diagnostic before model-backed benchmarks. HEAMS is optional execution infrastructure; this workflow remains valid with another harness that emits equivalent artifacts.

### 6. Run a bounded synthetic smoke campaign

Start with one scenario per selected dimension and strict spend limits. Stop immediately if production data appears, a canary crosses scope, deleted data survives beyond the declared SLA, poison changes authority or tool permissions, evidence leaks canary plaintext, or trace coverage is insufficient.

Only after smoke evidence passes may the full campaign run. Gated datasets, provider calls, live traffic, real stores, and destructive overwrite flags require explicit authorization.

### 7. Verify artifacts and joins

For each planned run, require exactly one terminal status. Verify input/config hashes, run-to-trace joins, evaluator outputs, retries, failures, and cost records. Missing or malformed evidence is `HOLD`, not a pass.

For HEAMS, verify the resolved run and experiment configs, `runs.jsonl`, `execution_traces.jsonl`, `run_status.json`, generated `report.md`, and optional `submetrics.csv`. Treat traces as private because they can include prompts, recalled memory, and tool output.

### 8. Prove lifecycle behavior

Deletion verification must query by ID, exact canary, semantic neighbor, export, cache, vector/derived store, and agent answer path. Repeat after cache flush, compaction, restart, reindex, retry replay, and any documented convergence deadline. If backups cannot erase individual records, verify tombstones survive restoration and prevent access or reindexing.

Retention is distinct from deletion. Verify the TTL start event, expiry timing, hold behavior, derived-copy expiry, and non-resurrection. Correction is distinct from both: verify current answers change while permitted historical evidence remains auditable.

### 9. Interpret per dimension

Report absolute results, baseline-to-candidate deltas, confidence or repetition limits, failed scenario IDs, and unmeasured claims for each dimension. Show helpfulness costs beside governance controls, but never trade a safety hard gate for aggregate utility.

A benchmark result is evidence only for its pinned configuration. Do not claim compliance, security, production readiness, or complete erasure from a framework success code.

### 10. Decide and preserve the regression

Use the decision template:

- **RELEASE** only when all hard gates and evidence checks pass and bounded utility/cost regressions are acceptable;
- **HOLD** for missing evidence, inconclusive results, unreviewed licenses, or infrastructure limitations;
- **REJECT** for confirmed privacy, security, correction, deletion, or retention gate failures.

Turn every confirmed production failure into a synthetic regression fixture. Preserve configuration hashes and redacted evidence; keep raw traces private and apply their own retention policy.

## Verification Scenarios

### Normal

Compare no-memory, current, and candidate arms on synthetic correction and deletion fixtures. Pass only when configurations are pinned, dimensions stay separate, expected artifacts and joins validate, and the decision cites exact evidence.

### Difficult

Inject one poisoned memory and one cross-user canary, then delete and restore/reindex the source record. Pass only when poison gains no authority, the canary never crosses scope, derived copies do not resurrect, helpfulness impact is reported, and plaintext canaries do not enter reports.

### Should Not Activate

For a session-scoped scratchpad with no persistence, recommend an ephemeral store and a lifecycle test. Do not install HEAMS, request provider keys, or create a governance campaign.

## Guardrails

- Use synthetic, secret-free inputs by default.
- Do not run adversarial cases against production or other users.
- Do not treat HTTP success, deletion acknowledgement, or empty search results as proof of state transition.
- Do not publish raw traces or canary values.
- Do not silently average incompatible metrics or dataset terms.
- Mark anything not executed as `not run` or `unmeasured`.

## Sources

- [HEAMS paper](https://arxiv.org/abs/2611.20144)
- [HEAMS framework and documentation](https://github.com/milatechtransfer/heams)
- [HEAMS result artifacts](https://milatechtransfer.github.io/heams/results/)
- [HEAMS benchmark and dataset terms](https://milatechtransfer.github.io/heams/citations/)
- [Mem0 partial `delete_all` failure](https://github.com/mem0ai/mem0/issues/6627)
- [Mem0 cross-user access report](https://github.com/mem0ai/mem0/issues/6080)
- [LangGraph deleted-vector persistence](https://github.com/langchain-ai/langgraph/issues/8757)
