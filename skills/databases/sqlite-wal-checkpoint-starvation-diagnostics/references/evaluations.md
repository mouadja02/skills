# Evaluation Prompts

These prompts test activation and observable decision quality. A response passes only when every listed assertion is present; stylistic similarity is irrelevant.

## Normal incident

**Prompt:** A SQLite WAL is 8 GB and `PRAGMA wal_checkpoint(TRUNCATE)` returns `1, 412000, 900`. Diagnose safely.

Assertions:

1. Interprets all three values as busy/log/checkpointed and computes a nonzero remainder.
2. Starts with evidence collection or PASSIVE sampling rather than repeated TRUNCATE.
3. Prohibits deleting or renaming live `-wal`/`-shm` files.
4. Seeks a long-lived reader/transaction owner.

## Difficult edge

**Prompt:** Readers overlap continuously, disk is nearly full, and a FULL checkpoint times out. Give a recovery sequence.

Assertions:

1. Distinguishes partial checkpoint progress from WAL reset.
2. Establishes a measured disk-reserve/growth deadline.
3. Pauses or throttles nonessential writers before reserve exhaustion.
4. Ends an identified stale reader through normal application control.
5. Uses bounded checkpoint attempts and stops on busy/deadline.
6. Verifies tuple progress and WAL behavior after traffic resumes.

## Should not activate

**Prompt:** How do I optimize a normal SQLite query with no WAL growth, busy checkpoint, or disk-pressure symptom?

Assertion: routes to ordinary query-plan/index analysis and does not prescribe checkpoint escalation.

## Deterministic helper check

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_analyze_checkpoint.py
```

The helper passes only if it classifies normal and busy results and rejects malformed JSON, non-object input, booleans masquerading as integers, negative/floating counts, unknown fields, impossible frame counts, non-standard `NaN`, unreadable inputs, and impossible PASSIVE busy values.
