---
name: postgres-transaction-pool-prepared-statement-conformance
description: Use when PostgreSQL clients behind PgBouncer/Supavisor fail with missing or duplicate prepared statements, especially in transaction/statement pooling, COPY, migrations, bursts, or after disabling a client statement cache.
version: "1.0.0"
license: MIT
---

# PostgreSQL Transaction-Pool Prepared-Statement Conformance

## When to Use

- `prepared statement ... does not exist` or `already exists` appears behind PgBouncer, Supavisor, or another PostgreSQL pooler.
- A migration, COPY, ORM, or burst workload behaves differently on direct, session, and transaction endpoints.
- A client claims its statement cache is disabled but protocol captures or server errors still show named preparation.
- You need to decide whether `max_prepared_statements`, unnamed statements, session pooling, or a direct endpoint is the narrowest safe mode.

Do **not** activate for an ordinary slow query on a direct PostgreSQL connection, generic pool sizing, or SQL tuning without a prepared-statement lifecycle failure.

## Prerequisites

- Exact pooler product/version and endpoint; do not infer pool mode from a port number alone.
- Read access to pool configuration and sanitized client configuration.
- A disposable database or approved staging environment for reassignment tests.
- Python 3.9+ only if using the optional offline classifier.

Never capture credentials, bind test listeners publicly, or run migration/COPY probes against production by default.

## Quick Reference

| Preparation mechanism | Session pool | Transaction/statement pool |
| --- | --- | --- |
| SQL `PREPARE` / `EXECUTE` | Session-affine | Unsafe across backend reassignment |
| Extended-protocol unnamed statement | No reusable server-side name | Usually the lowest-risk pooled option; still test the exact client path |
| Extended-protocol named statement | Session-affine | Requires pooler support/configuration and a reassignment fixture |
| “Client cache disabled” | Configuration evidence only | Does not prove every COPY/migration/internal path is unnamed |

PgBouncer distinguishes SQL-level `PREPARE` from protocol-level prepared plans. Its current documentation states that protocol-level named plans can be tracked when `max_prepared_statements` is nonzero; SQL `PREPARE` is session state and is not transformed by that feature. Treat these as sourced facts. The mode-selection and test sequence below are conservative recommendations.

## Procedure

### 1. Identify every hop and role

Record, without secrets:

```text
client/driver + version
  -> application pool + mode
  -> PgBouncer/Supavisor + version, pool_mode, max_prepared_statements
  -> PostgreSQL + version
operation: query | migration | COPY
```

Confirm whether direct, session, and transaction endpoints terminate at the same database. A successful direct connection is a control, not proof that the pooled path is correct.

**Completion:** every endpoint has an observed product, mode, and configuration source; unknowns remain explicitly unknown.

### 2. Classify the preparation mechanism

Do not collapse these mechanisms into “prepared statements”:

1. SQL `PREPARE name AS ...` creates PostgreSQL session state.
2. Extended-protocol **named** Parse messages create reusable protocol-level plans.
3. Extended-protocol **unnamed** Parse messages replace the unnamed plan rather than relying on a reusable name.
4. A driver cache setting controls only the paths documented by that driver. COPY, migration, metadata, or ORM-internal paths can differ.

Prefer driver debug telemetry or a redacted protocol-aware capture in staging. Do not infer the mechanism from an error string alone.

**Completion:** classify the exact failing operation as `sql_prepare`, `protocol_named`, `protocol_unnamed`, or `unknown`. Stop rather than guessing when it is unknown.

### 3. Run the offline preflight

Create a data-only input:

```json
{
  "pool_mode": "transaction",
  "preparation_kind": "protocol_named",
  "max_prepared_statements": 0,
  "client_statement_cache": true,
  "operation": "query",
  "concurrent_clients": 100
}
```

Run:

```bash
python3 scripts/analyze.py topology.json
```

The classifier separates observations from violations. For example, “named preparation despite cache off” is evidence about the client path; it is not itself a safety violation. The actual violation is a named plan crossing a backend-reassignment boundary without tracking.

**Completion:** output is `not_applicable`, `compatible_by_declared_invariants`, `conditionally_compatible`, or `incompatible`, with explicit findings and no unknown fields.

### 4. Prove backend reassignment

Use a disposable database and at least one more client than available backend connections:

1. Record `pg_backend_pid()` at transaction boundaries.
2. Run a fresh-connection control.
3. Run repeated operations through one logical client while another client occupies/releases a backend.
4. Require evidence that a logical client used different backend PIDs; otherwise the test did not exercise the failure boundary.
5. Repeat the exact failing path: ordinary query, COPY, or migration—not a substitute `SELECT 1`.

Do not treat concurrency alone as reassignment evidence. Do not terminate production backends to force it.

**Completion:** the fixture proves both a backend PID transition and the operation result/error associated with that transition.

### 5. Select one bounded compatibility mode

Choose the narrowest option supported by measured behavior:

1. Prefer unnamed protocol execution when the client supports it for the exact operation.
2. For named protocol plans, enable a bounded nonzero pooler tracking limit only after sizing and reassignment tests. Monitor pooler memory and prepared-plan counts.
3. Route SQL `PREPARE`, migration session state, or an unfixable client path through session pooling or a direct endpoint.
4. Do not “fix” duplicate names by randomizing indefinitely; that can hide lifecycle errors and grow server/pooler state.
5. Do not use transaction pooling for a path merely because one sequential test passed.

If changing pool mode or tracking capacity, retain the old endpoint as the rollback path and canary a bounded workload first.

### 6. Verify correctness and pool reuse

A pass requires all of the following:

- fresh and reused connections return identical rows/bytes;
- no missing/duplicate prepared-statement errors occur under forced reassignment;
- COPY row count and payload digest match the direct/session control when COPY is in scope;
- migrations complete on the intended endpoint and leave the expected schema fingerprint when migrations are in scope;
- backend connection count remains bounded and backend PID reuse is observed;
- server/pooler prepared-plan counts stabilize after the workload;
- rollback to the prior endpoint/configuration is rehearsed.

A no-error run without proven reassignment is inconclusive.

## Failure Recovery

- **Mechanism unknown:** preserve traces and stop; use a protocol-aware staging capture rather than changing production configuration.
- **Tracking enabled but failures persist:** verify the pooler/version actually supports protocol tracking, confirm the failing path is protocol-level named preparation, and test a session endpoint.
- **Cache disabled but names remain:** inspect COPY/migration/internal driver paths; configuration intent is weaker than observed wire behavior.
- **Prepared-plan count grows:** stop the canary, restore the previous endpoint/configuration, and investigate naming/cardinality before raising limits.
- **Migration failure:** do not retry blindly through transaction pooling; inspect partial effects and use the migration tool's documented recovery on a session-affine endpoint.

## Objective Verification

Run the packaged offline tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

They cover all declared pool modes, SQL versus protocol preparation, COPY boundaries, observation-versus-violation separation, unknown/missing fields, boolean-as-integer confusion, oversized integers, and non-standard JSON numbers.

For a real substrate, archive only redacted topology, backend PID sequence, operation result digests/counts, error classes, pool reuse counts, and configuration version. Never archive connection strings or query parameters containing credentials.

## Evaluation Prompts

1. **Normal:** “Diagnose duplicate prepared statement failures for an asyncpg service behind PgBouncer transaction pooling during request bursts.”
2. **Difficult edge:** “`statement_cache_size` is zero but COPY still creates named statements through a statement pool; determine whether this is safe.”
3. **Should not activate:** “Tune a slow SELECT on a direct PostgreSQL session with no pooler.”

## Sources

- PgBouncer configuration: https://www.pgbouncer.org/config.html#max_prepared_statements
- PgBouncer feature matrix: https://www.pgbouncer.org/features.html
- PostgreSQL `PREPARE`: https://www.postgresql.org/docs/current/sql-prepare.html
- Prisma transaction-pool migration report: https://github.com/prisma/prisma/issues/22779
- asyncpg cache-disabled preparation reports: https://github.com/MagicStack/asyncpg/issues/1058 and https://github.com/MagicStack/asyncpg/issues/1219
- Supabase burst and duplicate-statement reports: https://github.com/supabase/supabase/issues/35684 and https://github.com/supabase/supabase/issues/39227

This skill contains original instructions and synthetic fixtures. Sources are cited for protocol facts and demonstrated problem evidence; no upstream code or prose is redistributed.
