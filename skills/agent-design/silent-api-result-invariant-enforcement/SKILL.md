---
name: silent-api-result-invariant-enforcement
description: Use when HTTP 200 tool results may silently violate the query—derive exact invariants, recheck, withhold invalid values, and gate final answers on verified observations.
version: "1.0.0"
license: MIT
---

# Silent API Result Invariant Enforcement

Build a code-level boundary between a tool API and an agent. Prove what can be proved with extra queries, keep uncertain evidence visibly uncertain, and never let the model override a deterministic withholding decision.

## When to Use

- A tool can ignore filters, combine them with the wrong logic, cap totals, drop fields, duplicate records, or accept misspelled parameters while still returning success.
- An agent reports plausible values directly from REST, GraphQL, search, catalog, analytics, or database tools.
- You need a reproducible decision packet containing verification state, recheck evidence, extra-call cost, withheld values, and blind spots.
- The API supports a justified metamorphic relation, record predicate, pagination relation, or published parameter allowlist.

Do **not** activate for explicit transport/schema errors already handled by normal retries, write operations without an idempotent read-back, or APIs whose semantics cannot support an exact relation. In the last case, report `unsupported`; do not manufacture verification.

## Prerequisites

- Current API documentation or schema, including filter logic, negation/complement support, pagination semantics, uniqueness keys, and parameter names.
- A harness layer that can intercept requests and observations before the model sees them.
- Synthetic or redacted fixtures with known answers. Never test write invariants against production unless the operation is authorized, isolated, idempotent, and reversible.
- A call budget: a full filtered-count partition check costs `2 × number_of_conditions` extra reads per attempt.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/synthetic_fault_harness.py --all --output report.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The bundled script is an offline teaching and regression fixture, not a production API adapter. It performs no network access and uses only Python's standard library.

| State | Meaning | May the value reach the model? |
|---|---|---|
| `verified` | Every selected exact check passed. | Yes |
| `verified_on_recheck` | First exact check failed; the same request and checks passed once on recheck. | Yes, with recheck evidence |
| `withheld` | An exact check failed twice. | No |
| `warned` | Only a learned/heuristic check failed. | Yes, with warning |
| `unsupported` | No justified exact check can run. | Yes only as explicitly unverified evidence; never as a verified answer |
| `error` | Request, checker, or evidence serialization failed. | No new value |

## Procedure

### 1. Freeze the request contract

Record the exact request shape, operation, filter conjunction/disjunction rules, negation semantics, pagination completeness, sort stability, uniqueness key, and published parameter set. Distinguish facts from assumptions. An API that lacks complement queries cannot use the count-partition identity.

Give each observation a task-scoped ID and retain the request fingerprint. A final answer gate must bind to the exact verified observation, not merely accept any equal integer seen earlier.

### 2. Inventory capabilities before choosing checks

For each operation, mark capabilities as `supported`, `unsupported`, or `unknown`:

- complement or negation for every filter;
- complete-list retrieval versus partial pages;
- stable unique record key;
- documented total semantics;
- deterministic sort and range bounds;
- read-after-write behavior;
- published request parameter names.

Read [references/invariant-catalog.md](references/invariant-catalog.md). Select only relations whose preconditions are proven. A relation is exact only if every correct implementation of this documented operation must satisfy it.

### 3. Separate exact checks from learned checks

Create a registry with `check_id`, class, prerequisites, extra-call cost, failure action, and known blind spots.

- **Exact:** a failure proves the response did not answer the request as documented. After one failed recheck, withhold the implicated value.
- **Learned:** inferred from samples, distributions, or conventions. A failure can be a false alarm. Warn and retain provenance; do not call it proof.

Type checks can be exact when the published schema requires the type. Plausibility ranges inferred from past values are learned.

### 4. Place checks in the harness

Enforce this order in code:

1. reject undocumented request parameters before transport;
2. execute the requested read;
3. run selected exact probes before constructing the model-visible observation;
4. if an exact check fails, repeat the same request and its probes once;
5. release only a passing value; otherwise replace it with a withheld marker;
6. run learned checks and attach warnings without upgrading confidence;
7. write an append-only evidence event containing request fingerprint, check IDs, probe results, cost, decision, and limitations.

Never place the decision only in the prompt. The model must not be able to choose a withheld value from hidden raw output, logs, or earlier messages.

### 5. Bind the final answer gate

Maintain a task-scoped set of verified observation IDs. Accept a numerical or categorical answer only when its provenance points to a currently verified observation produced for the same request. If the agent retries with a different query, create a new observation rather than mutating the old decision.

After the rejection budget, end with `cannot be determined` and name the failed checks. Do not repair, interpolate, or recompute a value unless a separately justified tool returns a new observation that passes its own checks.

### 6. Test normal, difficult, and non-activation cases

Use synthetic data and inject one fault at a time:

- normal API: release the correct value and record probe cost;
- ignored first and last filters;
- AND interpreted as OR;
- capped total or truncated complete list;
- dropped field or unknown parameter;
- duplicate record and off-by-one count;
- one-time transient fault: release only after the full recheck passes;
- persistent exact failure: expose no value;
- unsupported complement/pagination semantics: issue no speculative probes and claim no verification;
- consistently lying API: document that same-source consistency checks cannot prove truth.

Run the bundled harness to confirm the decision matrix, then adapt the pattern to the target API without copying its synthetic assumptions.

### 7. Produce the decision packet

Use [templates/report-template.md](templates/report-template.md). Include:

- API/version and request fingerprint;
- capabilities and selected/non-selected checks;
- exact probe evidence and recheck outcome;
- released, warned, withheld, or unsupported decision;
- extra API calls, latency, and rate-limit impact;
- false alarms on clean fixtures;
- coverage and remaining blind spots;
- rollback or disablement trigger.

Report risk against coverage: withholding can lower wrong-answer risk by answering fewer requests. Do not present abstention as recovery.

## Failure Recovery

- **Probe request fails:** mark the observation `error` or `unsupported`; never treat missing evidence as a pass.
- **First exact failure clears on recheck:** release the second value as `verified_on_recheck`, retain both attempts, and count all calls.
- **Exact failure persists:** withhold the raw value from every model-visible channel and allow only a new independently checked observation.
- **Learned check fails:** warn, name the learned rule and evidence window, and avoid deterministic withholding unless its false-alarm bound was independently justified.
- **Check causes rate-limit or latency harm:** disable that check explicitly, downgrade coverage, and report the unsupported gap. Do not silently sample and continue claiming full verification.
- **Write/read-back check may repeat a side effect:** stop. Use idempotency and an isolated fixture before any recheck.

## Pitfalls

- HTTP success, valid JSON, and schema conformance do not prove that filters were applied.
- A complement identity is invalid if negation is unsupported, non-exhaustive, or uses different null semantics.
- `len(page) == total` is exact only for a declared complete result, not an ordinary page.
- A warning is not enforcement; raw failed values must not remain visible to the model.
- Blind retries can repeat writes and do not detect lasting semantic faults.
- Auto-repair can produce a wrong value marked verified. Verify a new observation; never bless a guessed repair.
- Same-source checks cannot detect an API that answers every probe from one consistently false world.
- Equality of values is not provenance. Bind final answers to observation IDs and request fingerprints.

## Verification

Completion requires all of the following:

- Every enabled exact check has documented preconditions and synthetic positive/negative fixtures.
- Normal, persistent-fault, transient-fault, and unsupported scenarios produce the expected states.
- Persistent exact failures expose no raw value in model-visible output.
- Learned failures never masquerade as exact proof.
- Extra calls and rechecks reconcile with trace totals.
- The final answer gate rejects unverified provenance and terminates with an explicit abstention path.
- The report names unsupported operations and a consistently lying API as blind spots.

## Sources

Facts about invariant checks, harness-side enforcement, warning versus withholding, recheck behavior, cost, abstention, and limitations are based on:

- Dip, Ouyang, and Motlhabi, “Invariant-Aware Harness Enforcement to Protect LLM Agents from Silent API Failures,” arXiv:2611.20595v1, CC BY 4.0: https://arxiv.org/abs/2611.20595
- SilentGuard reference implementation at commit `748975cb3070a4661ff8ab689ed7fdfe55da0a47`, Apache-2.0: https://github.com/Sajib-006/silentguard/tree/748975cb3070a4661ff8ab689ed7fdfe55da0a47

This package is original operational guidance and an independently authored synthetic fixture. It copies no upstream code or dataset. The workflow generalizes capability inventory, provenance binding, unsupported states, cost accounting, and reporting beyond the reference count implementation.
