# Control and rollout matrix

A benchmark decides nothing until its controls discriminate. Every published task carries five control classes and repeated evidence for each.

## The five controls

| Class | Construction | Required reward | What it proves |
|---|---|---|---|
| `oracle` | `solution/solve.sh` | 1 | The task is solvable in the frozen environment |
| `no-op` | Creates the output path with no work (empty file, empty array, unchanged input copy) | 0 | The verifier is not existence-only |
| `near-miss` | Performs the workflow but omits one required transition, field, ordering, or partition | 0 | The verifier checks the whole contract, not a headline value |
| `shortcut` | Satisfies the letter of the instruction without the work — echoes the fixture, copies a visible expected answer, hardcodes a sample, stubs the transform | 0 | The task measures capability, not copying |
| `alternative-valid` | Different method, same observable contract (different library, different row ordering normalizer, different intermediate format) | 1 | The verifier grades the contract, not the reference implementation |

A task without `shortcut` and `alternative-valid` is not yet a benchmark: it cannot distinguish memorization from capability, or over-fitting from conformance.

## Rollout manifest

Store one manifest per campaign, outside the published package when it contains private paths:

```json
{
  "task": "partner-revenue-reconciliation",
  "runner": {"name": "harbor", "version": "0.25.x"},
  "harness": {"sandbox": "docker", "cpus": 2, "memory_mb": 4096},
  "rollouts": [
    {"class": "oracle", "agent": "oracle", "model": "-", "seed": 0, "trials": [1, 1, 1], "trace_dir": "traces/oracle"},
    {"class": "no-op", "agent": "oracle", "model": "-", "seed": 0, "trials": [0, 0, 0], "trace_dir": "traces/noop"},
    {"class": "near-miss", "agent": "oracle", "model": "-", "seed": 0, "trials": [0, 0, 0], "trace_dir": "traces/nearmiss"},
    {"class": "shortcut", "agent": "oracle", "model": "-", "seed": 0, "trials": [0, 0, 0], "trace_dir": "traces/shortcut"},
    {"class": "alternative-valid", "agent": "oracle", "model": "-", "seed": 0, "trials": [1, 1, 1], "trace_dir": "traces/alternative"}
  ]
}
```

Requirements the validator enforces:

- all five classes present;
- at least three trials per class;
- oracle and alternative-valid trials all equal 1;
- no-op, near-miss, and shortcut trials all equal 0;
- identical outcomes within a class with identical inputs (a mixed class is flakiness, not difficulty).

## Interpreting results

- **Oracle below 1** → broken task: environment, artifact path, or verifier bug. Fix before measuring capability.
- **No-op above 0** → existence-only verifier. Add content and schema assertions.
- **Near-miss above 0** → the assertion set does not cover a required transition. Add the missing predicate and keep the near-miss as a regression control.
- **Shortcut above 0** → the environment leaks the answer or the verifier accepts the shape of the answer. Remove the leak; if unavoidable, change the task.
- **Alternative-valid below 1** → the verifier encodes the reference implementation. Assert the contract (values, structure, invariants), not the bytes of the reference output.
- **Mixed outcomes within a class** → nondeterminism: unsorted iteration, timestamps, locale, network, or a race. Pin all four before publishing.

## Model rollouts are optional, controls are not

Control rollouts use the oracle agent (deterministic scripts) and cost nothing. Model-backed rollouts measure capability and require a budget; record model identifier, provider, temperature, seed, token budget, and harness version for every one. Never mix model revisions inside a single reported score.
