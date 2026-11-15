# Advanced dbt unit-test cases

## Incremental models

Test full-refresh and incremental branches separately with an `is_incremental`
macro override. When SQL reads `this`, provide a `given: input: this` fixture.
Expected rows are the model's emitted insert/merge rows, not the final relation.
A test that checks only new records can miss an incorrect recomputation of an
existing key: include old and new inputs for one changed key and an unchanged key.

Define timestamp policy explicitly: inclusive versus exclusive watermarks,
late arrivals, timezone conversion and retries are business/ingestion choices.
Do not copy the demo's watermark into production without checking those choices.
For a retry-safe merge, verify repeating a batch does not duplicate keys.

## Ephemeral dependencies and SQL fixtures

Use `format: sql` for an ephemeral parent. Include all its columns, with explicit
casts where the adapter cannot infer a type from null or mixed values. Declare
other `ref`/`source` inputs rather than relying on data in the developer's schema.
The included example deliberately has an ephemeral `int_payments` dependency.

## Adapter and engine boundaries

Check current dbt documentation and your project's locked versions. BigQuery
STRUCT mocks need complete fields; Redshift has relation/database constraints.
A successful DuckDB example is not adapter parity evidence. Python models,
snapshots, recursive SQL, materialized views and introspective-query behavior
have different or unsupported boundaries; don't claim generic unit-test support.
Versioned models may run tests against multiple versions; restrict versions only
when that is the intended compatibility policy. For introspective macros,
explicitly override supported macro values when possible; otherwise explain the
limitation rather than forcing warehouse discovery into a synthetic test.

## Safe prerequisites

Do not issue `dbt run --empty` merely to make a failing test compile. First verify
target, warehouse/database/schema, direct parent relations, engine and adapter.
It can replace existing relations with zero-row versions. Use a new disposable
schema/database, or let the user choose a safe project-specific setup. Never
modify a production profile or run a production job as a test prerequisite.

## Debugging and production handoff

A parser/type/relation error is not a failed business assertion. Preserve its
actual error and fix the fixture/environment separately. For a row mismatch,
compare expected outputs with the business rule before editing the test.
Run the project's usual data tests and build after unit tests pass. Keep static
unit tests in development/CI; use version-supported production exclusion flags
and verify the selected resource set rather than assuming an old environment
variable has the same name across dbt engines.

Adapted from dbt Labs' adding-dbt-unit-test references at commit
`b8facde20b7a92c40ce3e6b86b71c4b92aa44040`, Apache-2.0. See the package LICENSE.
