# Evaluation Prompts

Run each prompt against a redacted snapshot with `python3 scripts/analyze_slots.py --input <fixture>`.

## Normal

**Prompt:** “After a switchover, the demoted PostgreSQL primary has an inactive logical failover slot retaining 40 GiB of WAL. No team confirms ownership. Diagnose it safely.”

**Assertions:** output is `review`; the slot is `orphan_candidate`; mutation remains prohibited; actions require owner identification, measured growth, and approval.

## Difficult edge

**Prompt:** “A standby reports a synchronized logical slot, but `invalidation_reason=wal_removed` and `wal_status=lost`. Is failover ready?”

**Assertions:** output is `critical`; the slot is `unusable`, not ready; recovery must start from an approved recovery point rather than promotion or slot advancement.

## Should not activate

**Prompt:** “Assess a healthy physical streaming-replication slot; there are no logical slots.”

**Assertions:** output is `not_applicable` and routes to a physical-replication runbook.
