---
name: postgres-logical-slot-failover-triage
description: "Use when PostgreSQL logical replication slots retain WAL, become orphaned or invalid after switchover, or must be proven synchronized and usable before failover."
version: "1.0.0"
license: MIT
---

# PostgreSQL Logical Slot Failover Triage

Diagnose logical-slot ownership, WAL retention, and failover readiness without turning an uncertain slot into data loss. Start read-only. A slot that looks inactive may still belong to a stopped consumer; a synchronized standby slot may exist but still be temporary or invalidated.

## When to Use

- Logical replication stops or resumes incorrectly after promotion, switchover, or demotion.
- An inactive slot retains growing WAL or threatens disk headroom.
- PostgreSQL 17+ failover slots must be proven ready before planned failover.
- `wal_status`, `safe_wal_size`, `synced`, or `invalidation_reason` indicate risk.

## When Not to Use

- Physical streaming-replication lag with no logical slots.
- Initial logical-replication design with no incident or failover-readiness question.
- Damaged cluster recovery, WAL file surgery, or bypassing a replication consumer's recovery process.
- PostgreSQL versions whose `pg_replication_slots` columns do not match this runbook; use version-specific documentation first.

## Prerequisites

- Exact PostgreSQL major version and server role: primary, standby, or demoted primary.
- Read-only SQL access to every relevant node and subscriber metadata.
- Consumer ownership map, maintenance authority, and a verified backup/recovery point before mutation.
- Disk free-space and WAL-growth telemetry.
- PostgreSQL 17 or later for built-in failover-slot synchronization fields and workflow.

## Quick Reference

Run on each relevant PostgreSQL 17+ node and preserve timestamps:

```sql
SELECT slot_name, slot_type, database, active, active_pid,
       restart_lsn, confirmed_flush_lsn, wal_status, safe_wal_size,
       failover, synced, temporary, inactive_since,
       conflicting, invalidation_reason
FROM pg_replication_slots
ORDER BY slot_name;
```

Measure retained WAL on a writable primary or demoted primary:

```sql
SELECT slot_name,
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)::numeric AS retained_wal_bytes
FROM pg_replication_slots
WHERE slot_type = 'logical' AND restart_lsn IS NOT NULL;
```

Do not infer deletion safety from `active = false`. Correlate slot name, database, plugin, publication/subscription, consumer deployment, and the consumer's durable offset.

For a redacted offline classification:

```bash
python3 scripts/analyze_slots.py --input observations/slot-snapshot.json
```

The helper never connects to PostgreSQL and always reports `mutation_permitted: false`.

## Procedure

### 1. Freeze topology and evidence

Record UTC timestamp, node identity, server role, PostgreSQL version, timeline, cluster manager, recent promotion/demotion, disk free bytes, WAL generation rate, and every logical consumer. Capture the query above on all relevant nodes before changing traffic or slots.

**Completion:** each node and slot has a unique identity, role, timestamp, and expected consumer owner.

### 2. Quantify retention and deadline

Measure `retained_wal_bytes`, filesystem free bytes, and WAL growth at least three times. `safe_wal_size` estimates bytes that can be written before a slot risks becoming `lost` when retention is bounded; `NULL` is not automatically safe because it can also occur for an already-lost slot. Interpret it with `wal_status` and `invalidation_reason`.

Classify:

- `reserved` or `extended`: WAL is still retained, but `extended` is already beyond `max_wal_size`.
- `unreserved`: required WAL is no longer guaranteed and may be removed at the next checkpoint.
- `lost` or non-NULL `invalidation_reason`: the slot is unusable for normal continuation.

**Completion:** record a measured disk-exhaustion deadline and a separate slot-loss boundary; do not substitute one for the other.

### 3. Reconcile ownership before mutation

For every inactive slot, identify the subscriber, connector, job, or application that created it. Compare configured slot names and durable consumer offsets. Check whether the consumer is intentionally stopped, restarting, migrated, or pointed at the new primary.

An inactive, unowned, WAL-retaining slot is only an **orphan candidate**. It is not deletion authorization.

**Completion:** ownership is confirmed, explicitly denied by all plausible owners, or marked unresolved with escalation contacts.

### 4. Prove standby readiness before failover

On the subscriber, inventory the primary slot and table-synchronization slots required by that subscriber. On the standby, require every required slot to exist and satisfy:

```text
synced = true AND temporary = false AND invalidation_reason IS NULL
```

Also verify the standby is ahead of the subscriber as required by the official failover procedure. Slot synchronization is asynchronous; existence alone is insufficient. A synchronized standby slot cannot be used for logical decoding or manually dropped while it remains a synced standby slot.

**Completion:** the complete required-slot set passes the readiness predicate and position check on the intended promotion target.

### 5. Classify the incident

| Evidence | Classification | Safe next step |
| --- | --- | --- |
| Demoted primary, inactive, owner unknown, retained WAL grows | Orphan candidate | Identify owner; protect disk; require approval before mutation |
| Standby slot missing, unsynced, temporary, or invalidated | Failover not ready | Stop planned promotion for that consumer; repair synchronization |
| `wal_status=lost` or invalidation reason set | Unusable slot | Use the consumer's approved re-snapshot/recovery path |
| Owner confirmed but consumer stopped | Inactive owned | Restore/reconcile consumer before considering slot action |
| Healthy primary slot lacks failover enablement | Not failover enabled | Plan and test failover-slot configuration before switchover |

**Completion:** every logical slot has one classification, supporting fields, and a named decision owner.

### 6. Stage recovery without destructive defaults

1. Protect disk headroom by throttling nonessential writers or expanding storage through the platform's supported procedure.
2. Restore a known consumer when its durable offset and required WAL remain valid.
3. If a slot is unusable, follow that consumer's explicit re-snapshot/rebootstrap procedure.
4. For a suspected orphan, obtain written owner confirmation, backup/recovery evidence, impact analysis, and human approval before any drop.
5. Rehearse promotion and consumer continuation in a disposable environment before production failover.

Never automatically drop or advance a slot, alter a subscription, promote a standby, or copy slot state by filesystem manipulation.

**Completion:** recovery has a bounded window, rollback, owner, and evidence that consumer data continuity is preserved.

### 7. Verify after recovery or failover

Re-capture all slot rows and positions. Confirm the consumer resumes from the intended point, retained WAL decreases or stabilizes, no slot becomes invalidated, disk headroom recovers, and old-primary slots are reconciled by the cluster manager's supported lifecycle.

**Completion:** representative changes arrive exactly once at the downstream system, WAL remains within the documented reserve under normal traffic, and a repeated failover drill passes.

## Offline Snapshot Schema

```json
{
  "schema_version": 1,
  "server_role": "demoted_primary",
  "warning_threshold_bytes": 1073741824,
  "slots": [{
    "slot_name": "orders_cdc",
    "slot_type": "logical",
    "active": false,
    "failover": true,
    "synced": false,
    "temporary": false,
    "invalidation_reason": null,
    "wal_status": "extended",
    "safe_wal_size": 2147483648,
    "retained_wal_bytes": 42949672960,
    "consumer_owner_confirmed": false
  }]
}
```

Use only redacted metadata. Do not include connection strings, credentials, captured row data, or consumer secrets.

## Unsafe Operations and Failure Recovery

- **Never drop or advance a slot merely because it is inactive.** This can destroy the consumer's continuation point.
- Never delete files under `pg_wal`, copy replication-slot directories, or edit PostgreSQL system catalogs.
- Never promote solely because slot names match; prove the readiness predicate and position ordering.
- Do not loop slot recreation or consumer retries without a bounded recovery plan.
- If disk exhaustion is imminent and ownership remains unresolved, pause or throttle writers through approved operations, preserve evidence, expand storage if supported, and escalate. Uncertainty is not permission to destroy the slot.
- If a mutation has already happened, stop further changes, preserve logs and LSNs, and invoke the consumer's restore/re-snapshot process from a verified recovery point.

## Objective Verification

Pass only when all are true:

- Node roles, versions, timelines, and slot snapshots are timestamped.
- Retained WAL, growth rate, free-space reserve, and slot-loss risk are measured.
- Every inactive slot has a confirmed owner or an explicit unresolved status.
- Every required standby slot satisfies `synced AND NOT temporary AND invalidation_reason IS NULL` and the position check.
- No mutation occurs without backup/recovery evidence, impact analysis, rollback, and human approval.
- After recovery, consumer progress and representative downstream delivery are verified while WAL stabilizes.
- A disposable failover drill proves both the not-ready boundary and successful continuation after readiness is restored.

## Pitfalls

- `active=false` means no process currently streams the slot; it does not mean the slot is abandoned.
- `synced=true` alone does not prove failover readiness.
- `safe_wal_size=NULL` is context-dependent; inspect `wal_status` and invalidation.
- Retained bytes are not consumer lag semantics; correlate with the consumer's durable offset.
- A platform operator may manage slot lifecycle differently from stock PostgreSQL; verify its supported switchover behavior.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with deterministic assertions.

## Sources and Provenance

Sourced facts about failover-slot synchronization, readiness, and `pg_replication_slots` fields come from PostgreSQL 18 documentation, accessed 2026-07-29. Factual demand evidence comes from CloudNativePG and Debezium issue reports. The classification table, evidence sequence, thresholds, snapshot schema, and helper are original operational recommendations, not PostgreSQL guarantees.

- [PostgreSQL 18: Logical Replication Failover](https://www.postgresql.org/docs/current/logical-replication-failover.html)
- [PostgreSQL 18: pg_replication_slots](https://www.postgresql.org/docs/current/view-pg-replication-slots.html)
- [CloudNativePG #9969: orphaned slots retain WAL after switchover](https://github.com/cloudnative-pg/cloudnative-pg/issues/9969)
- [Debezium DBZ-8544 / dbz issue #2095: PostgreSQL 17 failover slots](https://github.com/debezium/dbz/issues/2095)
