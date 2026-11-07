---
name: dbt-model-contracts
description: >-
  Use when adding or repairing dbt model contracts — generating data_type declarations from
  manifest.json and catalog.json, preserving existing column tests and docs, and validating a
  contract before it is enforced in CI.
version: "1.0.0"
author: Mouad Jaouhari
license: MIT
---

# dbt Model Contracts

Turn "we should add contracts" into a reviewed, enforceable properties patch. Types come from the
compiled catalog, existing column semantics are preserved, and anything ambiguous is blocked with a
reason instead of guessed. This skill does not infer business keys or nullability from data samples,
and it does not enable enforcement as a side effect of scaffolding.

## When to Use

- A dbt project has models but no `config.contract.enforced: true`, and someone must declare column
  types without hand-copying them out of the warehouse.
- A contract already exists but drifted: renamed columns, changed precision, or columns present in
  the catalog and missing from `schema.yml`.
- A downstream consumer (BI tool, reverse ETL, another team's model) needs a stable column contract
  before a model is refactored.
- A CI gate must fail when a model's compiled columns stop matching its declared contract.

Skip this skill when the task is writing model SQL, designing the DAG, or authoring tests — and skip
it for `ephemeral`/`snapshot` resources, which cannot carry a contract.

## Prerequisites

- Python 3.10+ with PyYAML (`pip install pyyaml`). Any dbt install already has it.
- Fresh artifacts from the target project: `dbt build` (or `dbt run`) followed by
  `dbt docs generate`, which produces `target/manifest.json` and `target/catalog.json`.
- The properties YAML you intend to change (usually `models/**/schema.yml`).
- No warehouse connection is required by the helper. `dbt build` at the end does need one.

## How to Run

```bash
python3 scripts/scaffold_contracts.py \
  --manifest target/manifest.json \
  --catalog target/catalog.json \
  --properties models/marts/schema.yml \
  --out /tmp/proposed-schema.yml \
  --report /tmp/contract-report.json \
  --adapter snowflake
```

Review `/tmp/proposed-schema.yml` and `/tmp/contract-report.json`, then apply with a snapshot:

```bash
python3 scripts/scaffold_contracts.py ... --apply --snapshot-dir .contract-snapshots/
```

`--apply` refuses to run without `--snapshot-dir`; the snapshot is written mode `0700` and its
checksum is recorded in the report. Verify the helper itself with
`python3 scripts/test_scaffold_contracts.py` (23 offline tests, no network, no dbt).

## Quick Reference

| Model state | Status | What it means |
|---|---|---|
| `materialized` is `table`/`view`, all catalog types usable | `READY` | Contract proposed |
| `incremental`, `materialized_view`, `ephemeral`, `snapshot` | `SKIPPED_MATERIALIZATION` | Needs a human decision first |
| Model absent from `catalog.json` | `SKIPPED_NOT_IN_CATALOG` | Stale artifacts — rebuild and regenerate |
| A column has no catalog type, or a nested/opaque type | `BLOCKED_COLUMN_TYPE` | Never invent a type; hand-author or exclude |
| Same model name in two packages | `BLOCKED_DUPLICATE_NAME` | Ambiguous identity |
| Zero catalog columns | `BLOCKED_EMPTY_COLUMNS` | Artifact problem, not a contract problem |

Exit codes: `0` proposal written, `2` refused (bad artifact, ambiguous target, unsafe `--apply`),
`3` write failure. A `2` means no file was written — fix the input, do not hand-edit around it.

## Procedure

1. **Refresh artifacts.** Run the project's normal build, then `dbt docs generate`. A catalog older
   than the last model change produces confidently wrong types — check `catalog.json` mtime against
   your last `dbt run`.
2. **Run the helper in propose mode** (no `--apply`). Read the JSON summary first: `ready`,
   `skipped`, `blocked`, and per-model `reasons`/`warnings`.
3. **Resolve every `BLOCKED_COLUMN_TYPE` by hand.** A missing type usually means the model was not
   materialised; a nested type means the contract cannot express the column. Do not paper over it by
   dropping the column from the catalog — that silently weakens the contract.
4. **Decide on `SKIPPED_MATERIALIZATION` models case by case.** Incremental models accept contracts
   only when `on_schema_change` is `fail` or `append_new_columns`; a contract cannot retro-fit a type
   change on an existing incremental table, so set the strategy before enabling enforcement.
5. **Diff the proposal against the original.** The helper round-trips YAML, so comments and key
   ordering in the original file are lost. Re-apply comment blocks by hand in the diff, or keep
   comments in a separate file — reviewable YAML beats silent comment loss.
6. **Check the type choices**, not just their presence. Length parameters are dropped for adapters
   that do not enforce them (Snowflake, BigQuery, Databricks, Spark, Athena, Trino, DuckDB) and kept
   where they are enforced (Postgres) — the report says which case applied and why.
7. **Apply, then compile.** `dbt parse` catches malformed properties; `dbt build --select <models>`
   proves the declared types match the SQL output. A type mismatch fails at build time, which is the
   whole point of the contract.
8. **Enable in CI** only after the models build clean: run `dbt build --select state:modified+` on
   pull requests so a column change that breaks a contract fails review rather than production.
9. **Record the rollout** in the PR: which models are now enforced, which were skipped and why, and
   what consumers depend on them.

Completion criteria: `dbt parse` succeeds, `dbt build` passes for every newly contracted model,
the report has zero unexplained `BLOCKED_*` entries, and the diff shows no lost descriptions or
tests.

## Type Normalization Rules

| Catalog type | Emitted `data_type` | Rationale |
|---|---|---|
| `NUMBER(38,9)` / `NUMERIC(10,2)` | `number(38,9)` / `numeric(10,2)` | Precision and scale are part of the contract |
| `VARCHAR(16777216)` on Snowflake | `varchar` | Snowflake does not enforce the length; declaring it is false precision |
| `VARCHAR(255)` on Postgres | `varchar(255)` | Postgres rejects longer values, so the length is real |
| `NUMERIC` with no precision | `numeric` + warning | Confirm the adapter default before enforcing |
| `VARIANT`, `JSON`, `STRUCT<…>`, `ARRAY<…>` | blocked | dbt contracts cannot express nested or opaque shapes |

Quotes and stray whitespace are normalised (`"NUMBER(38, 9)"` → `number(38,9)`); nothing else is
rewritten. A type you disagree with should be corrected in the properties file consciously, not by
teaching the helper a special case.

## Pitfalls

- **Treating the catalog as the source of truth for intent.** It describes what the warehouse built,
  not what consumers were promised. Review each type against the SQL that produces it.
- **Enabling contracts on a model with an undeclared column.** dbt fails the build when the SQL emits
  a column the contract omits — that is correct behaviour, but it turns a green pipeline red. Stage
  contracts model by model.
- **Inferring keys or nullability from samples.** `not_null` and primary keys are business decisions.
  The helper only preserves constraints already declared in YAML.
- **YAML round-trip losing comments.** Always propose to a separate file, diff it, then apply.
- **Stale catalog after a rename.** A renamed column shows up as a removal plus an addition; the
  resulting contract legitimately breaks downstream consumers. Announce it, do not quietly edit the
  old column out.
- **Assuming `--apply` is reversible.** It is only reversible through the snapshot the helper writes;
  check the snapshot path and checksum in the report before you keep working.
- **Versioned models.** For versioned models, scaffold the version currently in production first and
  confirm the version pins in `schema.yml` before touching others.

## Verification

```bash
python3 scripts/test_scaffold_contracts.py          # helper's own offline suite
dbt parse --project-dir .                           # properties YAML is valid
dbt build --select <contracted models>              # declared types match the SQL output
git diff --stat -- models/                          # nothing outside the intended models changed
```

Fail-closed checks worth exercising before trusting the helper on a new project: a truncated
`manifest.json` (exit 2, nothing written), a properties file with duplicate model entries (exit 2),
an `--apply` without `--snapshot-dir` (exit 2, original untouched), and an unwritable `--out` path
(exit 3, original untouched).

## Test Prompts

1. *Normal:* "This dbt project has three `table` models and no contracts. Add contracts with the
   right column types and keep our existing descriptions and unique tests."
2. *Difficult edge:* "Same request, but one model is incremental with `on_schema_change: ignore`, one
   was never built, and one column has no type in `catalog.json`."
3. *Should not activate:* "Write a dbt model that computes monthly revenue by region." — that is dbt
   authoring, not contract scaffolding.

**Related skill:** `dbt-expert` for model SQL, materialization strategy, and YAML authoring.
