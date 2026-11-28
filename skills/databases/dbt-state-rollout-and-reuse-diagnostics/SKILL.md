---
name: dbt-state-rollout-and-reuse-diagnostics
description: >-
  Use when assessing, enabling, canarying, or debugging managed dbt State; when
  skip, clone, build, freshness, lag_tolerance, hooks, volatile SQL, or DATT
  usage is unclear; or when dbt State is confused with --state and deferral.
version: "1.0.0"
license: Apache-2.0
source: "https://github.com/dbt-labs/dbt-agent-skills/tree/b8facde20b7a92c40ce3e6b86b71c4b92aa44040/skills/dbt/skills/using-dbt-state"
attribution: "dbt-labs/dbt-agent-skills by dbt Labs"
---

> **Attribution:** Adapted from [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills/tree/b8facde20b7a92c40ce3e6b86b71c4b92aa44040/skills/dbt/skills/using-dbt-state) by [dbt Labs](https://www.getdbt.com/), licensed Apache-2.0. Modified for this collection with current version gates, rollout controls, evidence requirements, and a reusable decision record.

# dbt State Rollout and Reuse Diagnostics

## When to Use

- Assess whether dbt State is suitable for a dbt v1, dbt v2/Fusion, or dbt platform project.
- Plan a bounded rollout that measures warehouse savings, freshness, and usage cost before broad enablement.
- Explain why a selected node was skipped, cloned, or built, or why it rebuilds unexpectedly.
- Configure `lag_tolerance`, freshness, clone boundaries, volatile SQL, hooks, or deferral.
- Separate managed dbt State from local `state:*` selectors, `--state`, `--defer`, and `dbt clone`.

Do **not** activate this skill for ordinary manifest-based Slim CI when the user explicitly excludes managed services, accounts, or outbound state. Use local `--state` and `--defer` guidance instead.

## Deliverable

Produce a completed [rollout record](templates/rollout-record.md), not only setup commands. The record must identify:

1. current engine, version, warehouse, orchestrator, and authentication mode;
2. the exact reuse objective and a measured pre-State baseline;
3. eligibility, data-flow, security, clone, and cost constraints;
4. a bounded canary with expected skip, clone, and build cases;
5. decision evidence for every sampled node;
6. freshness, correctness, and cost acceptance gates; and
7. rollback conditions and an owner.

Mark unavailable facts as `unknown`. Never invent account IDs, project IDs, usage allowances, prices, or observed decisions.

## Keep the Two Meanings of State Separate

| Mechanism | Comparison source | What it does | Managed service |
|---|---|---|---|
| dbt State | Server-backed execution history across eligible environments | May skip a selected node, clone a matching node, or build it | Yes; dbt account authentication and usage terms apply |
| `state:*` selector | Usually a supplied `manifest.json` | Selects nodes whose project state differs | No |
| `--defer --state <dir>` | A supplied manifest and its relation locations | Resolves unselected upstream references elsewhere | No |
| `dbt clone --state <dir>` | A supplied manifest | Creates target objects from a prior state | No |

A command such as `dbt build --select state:modified+ --defer --state ./state` does not enable dbt State. It selects changed nodes and descendants, then defers eligible unselected references. Every selected node still executes unless another mechanism changes that behavior.

## Workflow

### 1. Freeze the Existing Contract

Record before changing anything:

```text
project / commit:
dbt distribution and exact version:
adapter and exact version:
warehouse:
execution surface: local | external orchestrator | dbt platform
current selector and command:
current state/deferral behavior:
critical freshness SLA:
materializations in scope:
regulated or environment-isolated schemas:
```

Capture a representative baseline across normal and peak workloads:

- successful run count and failure/retry rate;
- nodes selected and actually executed;
- warehouse credits or equivalent compute, elapsed time, and queue time;
- source/model freshness and critical reconciliation checks;
- full-refresh frequency and incremental row volumes;
- current artifact, query-tag, and log retention; and
- per-run identity: Git SHA, invocation ID, target, dbt/adapter versions.

Normalize comparisons for warehouse size, data volume, refresh mode, and concurrency. A faster run on a larger warehouse is not automatically a saving.

### 2. Verify Eligibility and Current Version Gates

Current first-party setup documentation defines these boundaries:

- Supported warehouses: Snowflake, Databricks, BigQuery, and Redshift.
- dbt v1.7–1.12: install the `dbt-state` plugin in the same isolated environment as dbt.
- dbt v1.13: dbt State is native; use `dbt login` and the native enablement controls.
- dbt v2/Fusion and dbt platform: dbt State is native.
- A dbt account is required for authentication even for local or externally orchestrated runs. Do not collect credentials. For unattended runs, use the documented service-token flow and an approved secret store.
- Python models always build. Custom materializations may be skipped when unchanged but are not cloned.
- dbt State is a separate usage-based product. Read current account terms and allowances; do not quote stale pricing from memory.

For dbt v1.7–1.12, create an isolated environment and pin compatible versions before a canary:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install "dbt-core==<approved-version>" \
  "<adapter-package>==<approved-version>" \
  "dbt-state==<approved-version>"
```

Review dependency resolution before production use. Do not install packages into a shared system Python or execute unreviewed install hooks in a privileged environment.

For dbt v1.13, enablement can be controlled per run with `--manage-state` / `--no-manage-state`, or with `DBT_ENGINE_MANAGE_STATE`. For v1.7–1.12, use `DBT_ENGINE_MANAGE_STATE` because those CLI flags are not available. In `dbt_project.yml`, native versions may set:

```yaml
flags:
  manage_state: true
```

Reopen the official setup page before applying a version-specific command. Version support and trial/usage terms can change independently of this skill.

### 3. Map Data, Identity, and Environment Boundaries

Document what crosses the boundary and who owns each credential. dbt State evaluates project logic and relation metadata; it does not need raw table rows to make ordinary reuse decisions. Verify the current provider statement and organizational policy rather than promising that no metadata leaves the environment.

Require:

- a named dbt account/project or org boundary;
- approved interactive identity for development and service identity for CI/orchestration;
- least-privilege warehouse roles per target;
- explicit production clone policy;
- secrets held in the orchestrator or platform secret store, never in profiles committed to Git;
- retention and access rules for compiled SQL, manifests, run results, and State explanations; and
- a decision on cross-developer or cross-environment clone sources.

Set `allow_clones: false` on a target when objects must never be cloned into it, especially production or regulated targets:

```yaml
my_project:
  outputs:
    prod:
      type: snowflake
      allow_clones: false
```

Do not assume zero-copy clone semantics on every warehouse or object type. Validate grants, ownership, policies, table type, retention, and downstream-tool behavior in a disposable target.

### 4. Define the Decision Model Before the Canary

For each selected node, dbt State chooses the cheapest valid action it can prove:

1. **Skip/reuse in place** when the object already exists in the target, relevant logic is unchanged, and freshness permits reuse.
2. **Clone/reuse from elsewhere** when a matching sufficiently fresh object exists in another eligible location and clone policy permits it.
3. **Build** when neither reuse path is valid; unselected upstream nodes may still be deferred.

Views can usually be reused when logic is unchanged because fresh upstream data is visible when queried. A view using `select *` may rebuild when column equivalence cannot be proven. Data-test results may also be reused; a previously failing result must remain visible rather than being converted into a pass.

Create at least these canary cases:

| Case | Controlled change | Expected evidence |
|---|---|---|
| Same target, unchanged logic/data | Repeat an identical run | Skip/reuse in place |
| Empty target, matching eligible object elsewhere | Use an isolated target | Clone/reuse or documented no-clone reason |
| Semantic SQL change | Change one expression | Build with logic-change reason |
| Fresh upstream data beyond tolerance | Advance controlled source freshness | Build with freshness reason |
| Cosmetic SQL change | Change whitespace/comment/alias only | Reuse if normalization is supported |
| Clone prohibited | Set target `allow_clones: false` | No clone; safe build or reuse |
| Python/custom materialization | Include one representative node | Behavior matches documented limits |
| Failing reused test | Re-run unchanged inputs | Prior failing result remains surfaced |

Change one variable at a time. Use synthetic or non-production data where possible. Never mutate production merely to manufacture a clone case.

### 5. Configure Freshness Intentionally

`lag_tolerance` delays rebuilding after upstream data changes; it does not suppress semantic SQL changes. The default is currently `45m`. Start from the business SLA, not from an arbitrary maximum:

```yaml
models:
  +state:
    lag_tolerance: "{{ '4h' if target.name == 'prod' else '7d' }}"
```

Other current model-state controls include:

```yaml
models:
  +state:
    require_fresh_data_from: any
    compare_unrendered_code: false
    evaluate_volatile_sql: false
    pre_clone: if_missing
    execute_hooks_on_any_reuse: false
```

Interpret them carefully:

- `require_fresh_data_from: any|all` controls whether any or all direct parents must be fresh before a rebuild is eligible.
- `compare_unrendered_code` can stabilize comparison when environment-dependent or nondeterministic rendering changes compiled SQL, but must not hide a real semantic difference.
- `evaluate_volatile_sql: false` compares a volatile function such as `current_timestamp()` by function identity rather than by each runtime value. Turn it on only when runtime value changes should invalidate reuse.
- `pre_clone` controls pre-population of incremental models and snapshots.
- `execute_hooks_on_any_reuse: true` is required when hooks must run even if the node is reused. First confirm the hook is idempotent and safe to repeat.

For sources and upstream relations, decide whether warehouse metadata is sufficient. Use `loaded_at_field` or `loaded_at_query` when metadata cannot express actual freshness. Align the query with incremental lookback windows so late-arriving rows do not remain invisible. Do not disable freshness globally to improve reuse numbers.

### 6. Run a Bounded Canary

Use one domain, isolated target, fixed Git SHA, pinned versions, and a controlled source snapshot. Keep the current production path available.

For each run, preserve:

- command and environment/target identity without secrets;
- Git SHA, invocation ID, dbt and adapter versions;
- structured logs and `run_results.json`;
- State explanation for every sampled node;
- warehouse query IDs/tags and resulting object metadata;
- reconciliation and freshness results; and
- built, skipped, cloned, and reused-test counts.

Verify activation after the run. Current docs show an enablement log similar to `dbt State adapter: dbt-state ... is enabled`; match the actual installed version rather than hardcoding the example.

Use the version-appropriate explanation command:

```bash
# dbt v1.x
 dbt-state explain

# dbt v2/Fusion
 dbt state explain
```

In dbt platform, use the run's **Explain** tab. The exact command options and output schema are versioned; capture `--help` and the installed version before automating parsing.

### 7. Prove Each Decision

Do not infer a State decision merely because a node is absent from `run_results.json`.

**Skip/reuse in place** requires:

- State explanation or structured logs naming the node and reason;
- no model DDL/DML for that node under the invocation query tag;
- expected target relation still present; and
- freshness/reconciliation checks passing.

**Clone/reuse elsewhere** requires:

- explanation naming the source and destination or an equivalent stable identifier;
- warehouse history showing the documented clone/copy operation;
- destination object type and policy/grant checks; and
- output reconciliation.

**Build** requires:

- explanation naming the invalidating condition;
- execution evidence in run results and warehouse history; and
- tests, freshness, and business reconciliation passing.

If logs and warehouse evidence disagree, classify the decision as `unresolved`; do not count it as a saving.

### 8. Diagnose Unexpected Rebuilds

Start from the node's explanation and compare a known reused run with the unexpected build. Preserve both artifacts before changing configuration.

Investigate in this order:

1. **Activation and provenance** — same project/org, target, Git SHA, dbt/adapter/plugin versions, and State enabled?
2. **Decision reason** — logic, config, schema, freshness, clone policy, object absence, or unsupported node type?
3. **Rendered logic** — compare raw and compiled SQL plus dependent macros. Relation-enumerating Jinja may emit unstable membership or order.
4. **Volatile behavior** — inspect `evaluate_volatile_sql` and whether Jinja rendered a changing value before parsing.
5. **Hooks/config** — check build-relevant configs and whether a reused node still needs an idempotent hook.
6. **Freshness** — compare parent timestamps, `loaded_at_*` output, `lag_tolerance`, and `require_fresh_data_from`.
7. **Views and schema** — inspect `select *`, inferred columns, contracts, and upstream schema drift.
8. **Clone boundaries** — inspect `allow_clones`, source eligibility, warehouse capabilities, and permissions.

Run a controlled comparison:

- fixed code, packages, versions, target, vars, and environment;
- separate clean artifact directories;
- one changed input at a time;
- same selected node and freshness snapshot; and
- before/after explanation plus compiled-node diff.

Possible remediation must match the evidence:

- sort and filter dynamic relation enumeration deterministically;
- keep runtime SQL volatility out of compile-time Jinja when it is not semantic;
- use `compare_unrendered_code` only after proving rendered instability is irrelevant;
- make hooks idempotent and opt them into reuse only when required;
- replace `select *` with explicit columns when schema is a controlled interface; or
- correct freshness and lag settings without weakening the SLA.

Require at least one negative control: a real semantic change or relevant freshness event must still force a build after the remediation.

### 9. Measure Cost and DATT Usage

Track warehouse savings and dbt State usage separately. A cheap warehouse run can still create product usage, and a reused view may have different billing behavior from a table or test.

For the canary record:

- built, skipped, cloned, and reused-test counts;
- warehouse compute and runtime normalized to baseline;
- current DATT count and account-reported billable/free split;
- distinct target objects and tests contributing to usage;
- storage, retention, and downstream-query effects; and
- estimated net saving under the account's current terms.

DATT means daily active target table. Treat current definitions, free allowances, and pricing as volatile commercial facts: read them from the account usage page and current first-party billing documentation. Do not extrapolate a monthly bill from one canary day without accounting for daily deduplication and workload seasonality.

### 10. Promote or Roll Back

Promote only when:

- every sampled decision is explained and matches warehouse evidence;
- critical outputs and tests meet documented tolerances;
- freshness remains within SLA, including late-arriving-data controls;
- normalized net savings clear the agreed threshold;
- usage exposure is understood and budgeted;
- clone, identity, and data-handling controls are approved; and
- rollback was exercised successfully.

Rollback triggers include incorrect output, unexplained reuse/build, stale data, clone-policy violation, service/authentication failure affecting the SLA, or net cost above the agreed threshold.

Use the version-appropriate disable control (`--no-manage-state`, `DBT_ENGINE_MANAGE_STATE=0`, or platform environment/job setting), restore the previous command path, and run the project's approved recovery build. Preserve suspect objects and evidence for investigation; do not delete them automatically. Never promote state from a failed or suspect invocation.

## Local Slim CI Non-Activation Pattern

When the requirement is local manifest-based Slim CI and excludes dbt State, stay local:

```bash
test -f ./state/manifest.json

dbt build \
  --target ci \
  --state ./state \
  --defer \
  --select 'state:modified+' \
  --indirect-selection cautious
```

Keep generated CI artifacts outside `./state`, use an isolated CI schema, and verify the production manifest's project, version, commit, and checksum. Deferral can mix newly built CI relations with production relations; relationship tests may cross environments. `state:modified+` selects descendants, while `--defer` changes reference resolution for eligible unselected parents. Neither requires nor enables managed dbt State.

## Primary References

Reopen these before a production rollout because versions and commercial terms change:

- [About dbt State](https://docs.getdbt.com/docs/deploy/dbt-state-about)
- [Set up dbt State](https://docs.getdbt.com/docs/deploy/dbt-state-setup)
- [dbt State configurations](https://docs.getdbt.com/reference/resource-configs/dbt-state-configs)
- [Configure dbt State deferral](https://docs.getdbt.com/docs/deploy/dbt-state-deferral)
- [Monitor dbt State activity](https://docs.getdbt.com/docs/deploy/dbt-state-interface)
- [dbt State usage](https://docs.getdbt.com/docs/platform/billing/dbt-state-usage)
- [Local state selection](https://docs.getdbt.com/reference/node-selection/state-selection)
- [Manifest-based deferral](https://docs.getdbt.com/reference/node-selection/defer)
