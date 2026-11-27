# Operational Policy Evaluation Decision

## Decision

- Campaign:
- Decision: `PROMOTE | HOLD | REJECT`
- Baseline:
- Candidate:
- Evidence cutoff:

## Eligibility and frozen identities

- Persistent state:
- Future coupling:
- Terminal interpretation:
- Simulator/data/scenario/tool/harness digests:
- Policy/model digests:
- Seeds and terminal horizons:

## Information and action boundaries

- Shared observations:
- Shared actions:
- Forbidden future information:
- Boundary verification:

## Run accounting

| Policy | Seed | Terminal status | Completed settlement? | Identity-compatible? | Eligible for final score? | Evidence |
| --- | ---: | --- | --- | --- | --- | --- |

Statuses: `completed`, `censored`, `contaminated`, `integrity_failed`, or `infrastructure_failed`.

## Resume integrity

- Pause boundary:
- Ledger-prefix verification:
- Boundary state digest:
- Uninterrupted versus resumed equivalence:
- Duplicate/missing event check:

## Matched outcomes

| Dimension | Baseline | Candidate | Matched delta | Uncertainty | Hard gate |
| --- | ---: | ---: | ---: | --- | --- |
| Feasibility | | | | | |
| Service | | | | | |
| Resources | | | | | |
| Economics | | | | | |
| Calls/retries/latency/tokens/cost | | | | | |

List per-seed values and the exact number of contributing matched pairs. Do not include censored, contaminated, integrity-failed, or identity-mismatched runs in final-policy aggregates.

## Diagnostics

| Finding | Classification | Search/replay scope | Evidence | Interpretation limit |
| --- | --- | --- | --- | --- |

Classifications: observed violation, supported association, counterfactual witness, bounded search with no witness, unsupported, or undetermined.

## Exclusions and censoring

- Environment/version mismatches:
- Information leakage:
- Incomplete or unsettled runs:
- Infrastructure failures:
- Unsupported diagnostics:

## Decision rationale

- Hard gates:
- Utility/economic evidence:
- Operational cost:
- Generalization limits:

## Follow-up and rollback

- Required clean reruns:
- Promotion guardrails:
- Rollback trigger:
- Preserved evidence and retention:
