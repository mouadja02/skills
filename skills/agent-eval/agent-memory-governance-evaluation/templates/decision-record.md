# Agent Memory Governance Decision

- **Campaign:** `<campaign-id>`
- **Candidate:** `<name + immutable version>`
- **Baseline:** `<name + immutable version>`
- **No-memory control:** `<configuration>`
- **Frozen configuration:** `<hash/link>`
- **Decision owner:** `<name>`
- **Decision:** `RELEASE | HOLD | REJECT`

## Evidence completeness

| Check | Result | Evidence |
| --- | --- | --- |
| Every planned run has one terminal status |  |  |
| Inputs and resolved configurations match the freeze |  |  |
| Every result joins to a trace |  |  |
| Required reports and cost records exist |  |  |
| Dataset terms were reviewed |  |  |
| Reports contain no plaintext canaries |  |  |

Missing evidence produces `HOLD`; it is not a passing zero.

## Dimension results

Keep dimensions separate. Use `not run` when evidence does not exist.

| Dimension | Baseline | Candidate | Delta/limit | Hard gate | Result | Evidence |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Performance |  |  |  | no |  |  |
| Efficiency |  |  |  | no |  |  |
| Privacy |  |  |  | yes |  |  |
| Security |  |  |  | yes |  |  |
| Correction |  |  |  | yes |  |  |
| Deletion |  |  |  | yes |  |  |
| Transparency |  |  |  | policy-defined |  |  |
| Retention |  |  |  | yes |  |  |

## Lifecycle verification

- **Correction:** `<current answer, historical evidence, stale-answer result>`
- **Deletion:** `<primary, vector, cache, export, log, replica, backup/restore probes>`
- **Retention:** `<before/at/after TTL, hold, restart, replay>`
- **Resurrection:** `<restart, compaction, reindex, queue replay, restore>`

## Governance–helpfulness trade-offs

Describe utility lost or gained from recall/retention controls. Do not use this section to waive a privacy, security, deletion, or retention hard gate.

## Failures and limitations

| Rule/scenario | Observed behavior | Scope | Remediation | Retest evidence |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

List unexecuted claims explicitly. Do not claim compliance, complete erasure, security, or production readiness beyond the tested configuration.

## Decision rationale

- `RELEASE`: all evidence checks and hard gates passed; utility/cost changes stayed within frozen limits.
- `HOLD`: `<missing, malformed, inconclusive, unlicensed, or unexecuted evidence>`.
- `REJECT`: `<confirmed hard-gate failure and evidence reference>`.

## Next action

- **Owner:** `<name>`
- **Action:** `<ship, remediate, add fixture, or rerun>`
- **Due:** `<date>`
- **Expected movement:** `<specific dimension and threshold>`
