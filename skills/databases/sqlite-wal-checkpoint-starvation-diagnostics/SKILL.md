---
name: sqlite-wal-checkpoint-starvation-diagnostics
description: "Use when a SQLite database in WAL mode has a growing -wal file, repeated incomplete checkpoints, SQLITE_BUSY, disk-pressure risk, or reader slowdowns that may indicate checkpoint starvation."
version: "1.0.0"
license: MIT
---

# SQLite WAL Checkpoint Starvation Diagnostics

Diagnose a WAL that cannot reset without deleting journal files or turning a production incident into a write outage. Separate **copying frames into the database** from **resetting/truncating the WAL**: a checkpoint can make progress while an older reader still prevents reset.

## When to Use

- A `database-wal` file grows continuously or threatens disk capacity.
- `PRAGMA wal_checkpoint(...)` repeatedly leaves frames uncheckpointed or reports busy.
- Read latency worsens while WAL size and long-lived read transactions increase.
- Space returns only after all application processes or readers exit.
- An operator needs a bounded, evidence-first checkpoint recovery sequence.

## When Not to Use

- Ordinary query/index tuning with no WAL growth or checkpoint symptom.
- Rollback-journal databases (`journal_mode` is not `wal`).
- Corruption recovery, file carving, or restoring a damaged database.
- Network filesystems: SQLite WAL requires cooperating processes on one host; redesign placement rather than applying this runbook.

## Prerequisites

- A verified backup or application recovery point before any production mutation.
- Filesystem access for size and free-space measurements.
- A SQLite client compatible with the target database.
- Application observability that can identify connection owners and transaction age. SQLite itself does not provide a universal cross-process reader list.
- Authority to pause traffic only if read-only diagnosis proves escalation necessary.

## Quick Reference

```sql
PRAGMA journal_mode;                 -- inspect; do not change during diagnosis
PRAGMA wal_autocheckpoint;           -- configured frame threshold
PRAGMA busy_timeout;                 -- current connection only
PRAGMA wal_checkpoint(PASSIVE);      -- non-blocking diagnostic snapshot
```

`wal_checkpoint` returns three integers: **busy, log frames, checkpointed frames**. Interpret the tuple together with its mode:

| Observation | Meaning | Next action |
| --- | --- | --- |
| `checkpointed == log` | All reported frames were copied | Verify whether WAL bytes stabilize/reset after new writes |
| PASSIVE and `checkpointed < log` | A reader boundary or concurrent activity limited progress; PASSIVE's busy column is always `0` | Correlate repeated samples with reader age |
| FULL/RESTART/TRUNCATE, `busy == 1` | The requested blocking checkpoint could not complete | Stop escalation and identify the holder |
| Repeated unchanged remainder | Likely persistent boundary, not a one-off spike | Find long transactions, leaked cursors, or overlapping readers |

Analyze a captured tuple offline:

```bash
python3 scripts/analyze_checkpoint.py \
  --input observations/checkpoint.json
```

Input example:

```json
{"mode":"PASSIVE","busy":0,"log_frames":412000,"checkpointed_frames":900,"wal_bytes":3375104000,"free_bytes":4294967296,"oldest_reader_seconds":1800}
```

## Procedure

### 1. Freeze the evidence, not the workload

Record UTC time, database path, database/WAL/SHM byte sizes, filesystem free bytes, process owners, deployment version, and recent write rate. Sample at least three times across the expected automatic-checkpoint interval.

**Completion:** observations show whether WAL bytes and the uncheckpointed remainder are growing, stable, or recovering.

Do not copy a live database by copying only the main file. Use the application's supported backup path or SQLite backup API.

### 2. Confirm WAL mode and scope

Run `PRAGMA journal_mode;` on the exact database. Map every process, worker, pool, desktop window, and maintenance job that can hold a connection. Check whether transaction scopes span streaming responses, iteration, sleeps, network calls, or user interaction.

**Completion:** every known connection class has an owner and expected maximum read/write transaction duration.

### 3. Take a PASSIVE checkpoint snapshot

Use `PRAGMA wal_checkpoint(PASSIVE);` first. It checkpoints what it can without waiting for readers or writers. Capture the exact three-column tuple; do not reduce it to “success” merely because SQL execution returned normally.

Repeat with timestamps. Compare `log - checkpointed`, WAL bytes, write rate, and the oldest observed reader age.

**Completion:** classify the incident as transient growth, partial progress behind a persistent boundary, or no progress.

### 4. Locate the oldest reader boundary

Instrument transaction begin/end and cursor lifetime in the application. Inspect pool checkout duration, open result iterators, background exports/scans, abandoned request contexts, and independent desktop/process connections. Correlate reader start times with when the checkpoint remainder stops advancing.

A busy timeout does not terminate a reader and automatic checkpoint thresholds do not guarantee reset. Fix transaction lifetime rather than repeatedly issuing stronger checkpoints.

**Completion:** identify a concrete owner or narrow the suspect set with an age/time correlation. If ownership remains unknown, preserve evidence and escalate to application instrumentation; do not guess by deleting files.

### 5. Gate escalation on disk headroom

Estimate near-term growth from measured bytes over time, not from a single snapshot. Set an incident deadline before free space reaches the application's minimum operating reserve. Reduce or pause nonessential writers if the deadline is shorter than the reader investigation.

Recommended policy (local, not a SQLite guarantee): alert when free bytes are less than twice the current WAL size or when measured growth reaches the reserve within the response window. Tune this to the workload.

**Completion:** an explicit free-space reserve, growth estimate, and writer-throttling trigger are recorded.

### 6. Recover in bounded stages

1. End or recycle the identified stale reader through the application's normal cancellation/shutdown path.
2. Re-run PASSIVE and verify that the remainder decreases.
3. During an approved maintenance window, try FULL with a finite connection-level `busy_timeout`.
4. Use RESTART only when future writers must begin a new WAL cycle and reader impact is understood.
5. Use TRUNCATE only after FULL/RESTART semantics and traffic impact are acceptable; treat it as an operational checkpoint, not a repair tool.
6. If any blocking mode returns busy or reaches its deadline, stop. Do not loop it indefinitely.

**Completion:** the tuple reaches full progress, WAL bytes reset or stabilize under resumed traffic, and no forced reader/writer outage occurred outside the approved window.

### 7. Prevent recurrence

Bound transaction and cursor lifetimes; avoid network/user waits inside transactions; close iterators deterministically; size pools intentionally; add WAL/free-space/remainder telemetry; and test overlapping readers plus sustained writes. Keep checkpoint scheduling separate from correctness—failed checkpoints must be observable and must not silently retry forever.

**Completion:** a regression test holds an old read snapshot while writes continue, proves a checkpoint remains incomplete, releases the reader, and proves a later checkpoint completes within a deadline.

## Unsafe Operations and Recovery

- **Never delete, rename, zero, or replace `-wal` or `-shm` while any connection may be open.** The WAL can contain committed data not yet copied to the database.
- Do not switch `journal_mode` during an incident merely to shrink files.
- Do not run unbounded FULL/RESTART/TRUNCATE loops; they can amplify an outage.
- Do not kill unidentified processes first. Capture owner, transaction age, tuple, and file sizes, then use normal shutdown.
- If free space is critical and no reader can be ended safely, pause writers, preserve the database and sidecar files through the supported backup procedure, and invoke the application's recovery plan.

## Objective Verification

Pass only when all are true:

- WAL mode is confirmed on the intended database.
- Three or more timestamped tuple/size samples are retained.
- The checkpoint tuple is interpreted by mode; PASSIVE `busy=0` is not mistaken for completion.
- The oldest-reader hypothesis has owner/time evidence or is explicitly unresolved.
- Recovery completes within a bounded deadline without manual sidecar deletion.
- Under resumed representative traffic, WAL bytes and uncheckpointed frames remain inside the documented reserve.
- The overlapping-reader regression test fails before release and passes after release.

## Pitfalls

- WAL file size alone does not identify the blocker; correlate it with tuple progress and transaction age.
- `checkpointed_frames > 0` does not mean reset succeeded.
- A PASSIVE first column of `0` does not prove all frames were checkpointed.
- `wal_autocheckpoint` is a trigger threshold, not a guarantee that readers permit completion.
- Filesystem byte growth and WAL frame counts use different units; do not compare them directly.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with deterministic assertions.

## Sources and Provenance

Sourced facts: WAL reader/checkpoint interaction, checkpoint modes, and result-column semantics come from SQLite's official WAL and PRAGMA documentation, accessed 2026-07-23. Demand evidence comes from factual issue reports in Syncthing, OpenCode, and Codex. Recommendations such as alert ratios, sample counts, deadlines, and escalation order are original operational guidance, not SQLite guarantees.

- [SQLite Write-Ahead Logging](https://sqlite.org/wal.html)
- [SQLite PRAGMA wal_checkpoint](https://sqlite.org/pragma.html#pragma_wal_checkpoint)
- [Syncthing issue #10559: checkpoint starvation](https://github.com/syncthing/syncthing/issues/10559)
- [OpenCode issue #37495: unbounded WAL growth](https://github.com/anomalyco/opencode/issues/37495)
- [Codex issue #30517: startup stall with large or busy WAL](https://github.com/openai/codex/issues/30517)
