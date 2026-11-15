---
name: dbt-unit-testing
description: Use when adding fixture-driven unit tests for dbt SQL model logic, fixing a transformation bug, or developing a model test-first. Covers complete dependency mocks, incremental and ephemeral cases, safe development execution, and CI handoff. For column uniqueness or null checks alone, use ordinary dbt data tests.
version: "1.0.0"
license: Apache-2.0
source: "https://github.com/dbt-labs/dbt-agent-skills"
attribution: "Adapted from dbt-labs/dbt-agent-skills, adding-dbt-unit-test, commit b8facde20b7a92c40ce3e6b86b71c4b92aa44040; see LICENSE."
---

# dbt model unit testing

Turn a model's business rules into small input/output fixtures, run them before
materializing production data, and keep the fixtures with the model changes.
Unit tests check transformation logic. Data tests check properties of real
relations after materialization; model contracts check schema shape.

## When to Use

- Refactor joins, filters, refund handling, date logic, or window functions.
- Reproduce a reported transformation bug before fixing it.
- Verify full-refresh and incremental branches with explicit expected rows.
- Test models that depend on ephemeral SQL without querying customer data.

Do not activate just to add `not_null`, `unique`, or `relationships` data tests,
check a warehouse's built-in arithmetic, or test Python models or snapshots.

## Prerequisites

Use a dbt version with unit-test support (dbt Core 1.8+ or the applicable dbt
platform engine) and a supported adapter. Check the project's engine and adapter
versions before copying version-specific options. Unit-test YAML belongs under
`model-paths`, usually `models/`; CSV/SQL fixture files belong under
`test-paths/fixtures`, usually `tests/fixtures/`.

Use an explicit development target. Warehouse unit tests still compile/execute
SQL and may require existing parent relations and their schemas. Do not assume
that mocked data means no warehouse access. The runnable bundled example uses
only a disposable local DuckDB database and synthetic data.

## Procedure

1. **Read the model and dependency graph.** Identify every `ref()` and `source()`,
   materialization, adapter-specific type, macro, variable, and use of `this` or
   `is_incremental()`. Name the business rule being protected, not just its SQL
   expression. Inspect the current local tests before adding duplicates.
2. **Freeze scenarios and expected results.** Include the normal business case,
   a costly edge or past regression, and a nearby request that should use data
   tests instead. Calculate expected rows independently. Useful cases include
   pending versus settled payments, refunds, missing joins, empty inputs, and
   timestamps at an incremental boundary. Do not silently choose business policy
   for the user; clarify ambiguous expected behavior.
3. **Mock every dependency.** Define one `given` entry per relevant `ref()` or
   `source()`. Prefer inline `dict` rows for ordinary types. Use explicit empty
   rows when a dependency is structurally required but irrelevant. Use SQL mocks
   for ephemeral dependencies and include every column in those SQL mocks. Match
   aliases/types to the actual adapter; don't infer production data from a demo.
4. **Describe the expected model output.** Put `unit_tests` alongside model YAML
   and assert business columns. For incremental tests, override `is_incremental`
   for each branch and mock `this` where the model reads it. Assert the rows the
   model emits for insertion/merge, not the hypothetical final merged table.
5. **Prepare a safe execution target.** Verify required parent relations exist.
   If schema-only builds are needed, use `--empty` only against a disposable
   development database/schema whose contents may be replaced. `--empty` can
   overwrite existing relations with zero-row versions; never run it against
   valuable data or a production target. Preserve existing profiles and secrets.
6. **Run, explain, and repair.** Run `dbt test --select "test_type:unit"` with the
   explicit project/profiles/target options. Distinguish compile/type/schema
   errors from actual-versus-expected row failures. Inspect each failure before
   changing expectations; don't weaken a test merely to get green. Run the
   project's normal build/data-test suite after fixing the model.
7. **Hand off reproducibly.** Commit model changes and fixture YAML/CSV/SQL
   together, with the exact command, engine/adapter versions and observed result.
   Run unit tests in development/CI. Follow the project's supported exclusion
   flags for production runs; do not copy obsolete environment-variable names.

See [advanced cases](references/advanced-cases.md) before handling incremental,
versioned, adapter-specific, or introspective-macro models.

## Run the included example

The example tests a development-only order-revenue model, including refunds,
pending payments, an ephemeral parent, incremental recomputation and timestamp
ties. Its upstream relation contains the full synthetic payment history. Its
inclusive watermark is an example policy, not a universal late-arrival policy.

Install a compatible dbt DuckDB adapter in your development environment. This
example was verified with `dbt-duckdb==1.11.1`; record the resolved dbt version.
Copy it out of the installed skill before running it so generated files stay out
of the package:

```bash
skill_dir="<installed-path-to-dbt-unit-testing>"
demo=$(mktemp -d)
cp -R "$skill_dir/examples/." "$demo/"
export DBT_DEMO_PATH="$demo/demo.duckdb"
dbt run --project-dir "$demo" --profiles-dir "$demo" --target demo --empty
dbt test --project-dir "$demo" --profiles-dir "$demo" --target demo --select "test_type:unit"
```

`DBT_DEMO_PATH` must point to a new disposable local file. The example profile
has no network database credentials. Expected: all three unit tests pass. Keep
reports in the copied project's `target/` and `logs/`, not in this skill folder.

## Verification and evaluation scenarios

- **Normal:** add tests for a revenue model with settled/pending payments and a
  refund. Verify all input mocks are declared and the expected amount reflects
  business semantics rather than raw row count.
- **Difficult:** an incremental model reads `this` and an ephemeral parent, and
  two updates share the watermark timestamp. Verify SQL mocks, both execution
  modes, emitted merge rows and the boundary. The bundled example exercises it.
- **Should not activate:** add a `not_null` constraint/test for one column.
  Route to ordinary data tests; don't introduce unit-test fixtures unnecessarily.

The bundled dbt tests verify example execution, not agent-response quality or
warehouse portability. Revalidate on the intended production adapter. A demo
passing on DuckDB does not prove Snowflake, BigQuery, or another adapter equivalent.

## Sources and license

Adapted from [dbt Labs' unit-test skill](https://github.com/dbt-labs/dbt-agent-skills/blob/b8facde20b7a92c40ce3e6b86b71c4b92aa44040/skills/dbt/skills/adding-dbt-unit-test/SKILL.md)
and its incremental/ephemeral references, under [Apache-2.0](LICENSE). The
synthetic runnable example and development-target workflow are local additions.
Check [current dbt unit-test documentation](https://docs.getdbt.com/docs/build/unit-tests)
for supported engines, materializations, adapters and selectors.
