# dbt State rollout and decision record

## Record identity

- Date:
- Owner:
- Project / Git SHA:
- Decision: `assess | canary | promote | hold | rollback`
- Evidence directory or run links:

## Current contract

| Field | Recorded value |
|---|---|
| dbt distribution and version | |
| Adapter and version | |
| Warehouse | |
| Execution surface / orchestrator | |
| Target and environment | |
| Current command / selector | |
| Current state or deferral mechanism | |
| Critical freshness SLA | |
| Materializations in scope | |

## Eligibility and boundaries

- Supported version and installation mode:
- Supported warehouse:
- dbt account/project or org:
- Interactive authentication mode:
- Non-interactive authentication mode and secret owner:
- Metadata/SQL handling reviewed against current docs: `yes | no | unknown`
- Clone sources allowed:
- Clone targets prohibited:
- Python/custom materialization limits:
- Current usage terms and allowance source:

## Baseline

| Metric | Window | Result | Evidence |
|---|---|---:|---|
| Successful runs | | | |
| Failure/retry rate | | | |
| Nodes selected / executed | | | |
| Warehouse compute | | | |
| Elapsed / queue time | | | |
| Freshness | | | |
| Critical reconciliation | | | |
| Full-refresh frequency | | | |

Normalization notes:

## Canary manifest

- Fixed Git SHA:
- Pinned dbt / adapter / plugin versions:
- Isolated target:
- Controlled source snapshot or interval:
- Models/tests in scope:
- Production exclusions:
- Rollback path exercised:

| Case | Controlled change | Expected action | Actual action | Explanation evidence | Warehouse evidence | Correctness/freshness | Disposition |
|---|---|---|---|---|---|---|---|
| Unchanged target object | none | skip | | | | | |
| Matching object elsewhere | empty target | clone or documented no-clone | | | | | |
| Semantic SQL change | one expression | build | | | | | |
| Fresh data beyond tolerance | one freshness advance | build | | | | | |
| Cosmetic SQL change | comment/whitespace | reuse | | | | | |
| Clone prohibited | `allow_clones: false` | no clone | | | | | |
| Unsupported/limited node type | representative node | documented behavior | | | | | |
| Reused failing test | unchanged input | failure remains visible | | | | | |

## Configuration decisions

| Control | Value | Reason / SLA | Evidence |
|---|---|---|---|
| `lag_tolerance` | | | |
| `require_fresh_data_from` | | | |
| `compare_unrendered_code` | | | |
| `evaluate_volatile_sql` | | | |
| `pre_clone` | | | |
| `execute_hooks_on_any_reuse` | | | |
| `allow_clones` by target | | | |
| `defer_to_target` if used | | | |
| `loaded_at_field/query` | | | |

## Unexpected-decision investigation

- Node:
- Known-good run:
- Unexpected run:
- State explanation difference:
- Raw and compiled SQL difference:
- Macro/Jinja determinism finding:
- Freshness and lag finding:
- Hook/config finding:
- View/schema finding:
- Clone/permission finding:
- One-variable controlled rerun:
- Negative control that still forces a build:
- Status: `proven | plausible | unresolved`

## Cost and usage

| Metric | Baseline | Canary | Normalized delta | Evidence |
|---|---:|---:|---:|---|
| Nodes built | | | | |
| Nodes skipped | | | | |
| Nodes cloned | | | | |
| Test results reused | | | | |
| Warehouse compute | | | | |
| Runtime | | | | |
| DATTs | | | | |
| Other storage/retention | | | | |
| Estimated net cost | | | | |

Current pricing/allowance source and access date:

## Promotion gate

- [ ] Every sampled action has State and warehouse evidence.
- [ ] Critical outputs and tests meet documented tolerances.
- [ ] Freshness remains within SLA, including late-arriving data.
- [ ] Normalized net saving clears the agreed threshold.
- [ ] DATT exposure is understood and budgeted.
- [ ] Identity, clone, metadata, and retention controls are approved.
- [ ] Rollback completed successfully in the canary.

Decision and rationale:

## Rollback

- Disable control for this exact version/surface:
- Previous command/config to restore:
- Recovery build procedure:
- Evidence and suspect objects to preserve:
- Trigger thresholds:
- Owner and response time:
