# Benchmark and License Selection

Select only the dimensions needed by the frozen decision, but never infer untested governance properties from retrieval accuracy. This matrix reflects HEAMS 1.0.0 at commit `f53dc9f7da4d91f48ee5de37a5aa6567c22ec4d5`; reopen current documentation before execution.

## HEAMS mapping

| Dimension | Candidate benchmark/evidence | What it supports | Important limitation |
| --- | --- | --- | --- |
| Performance | LoCoMo, BEAM, LongMemEval, Evo-Memory | recall, long-context memory, temporal question answering, evolving streams | model/judge and dataset terms vary |
| Efficiency | run artifacts and `submetrics.csv` | latency/model-use observations tied to runs | does not by itself price infrastructure or all background work |
| Privacy | Contextual Integrity | disclosure/leakage and helpfulness under contextual norms | synthetic scenarios do not prove storage-layer isolation |
| Security | MPBench plus synthetic poisoned-memory controls | resistance to primed memory poisoning | does not prove every tool or authorization boundary |
| Correction | STALE and Erasability & Editability | stale-memory detection, update/cascade behavior | supplement with backend-specific current/historical readback |
| Deletion | Erasability & Editability plus store probes | explicit deletion behavior at the agent layer | inspect vectors, caches, logs, exports, replicas, and restore paths separately |
| Transparency | Transparency | memory audit behavior and evidence visibility | verify source IDs and lifecycle states in actual traces |
| Retention | Retention policy | blocked/prohibited ingest and permitted recall | supplement with controlled-clock TTL, hold, restart, and resurrection tests |

## Dataset terms at the pin

Do not redistribute or use a benchmark merely because HEAMS code is MIT.

| Benchmark/data | Terms recorded by HEAMS | Campaign action |
| --- | --- | --- |
| LoCoMo | CC BY-NC 4.0 | exclude from commercial campaigns unless terms permit the use |
| BEAM | CC BY-SA 4.0 | retain attribution and share-alike obligations |
| MPBench | Apache-2.0 | preserve notices and pin the dataset version |
| LongMemEval | MIT | retain license and pin the cleaned dataset revision |
| Evo-Memory sources | mixed: unstated, gated CC BY 4.0, MIT, Apache-2.0 | review each selected source; an unstated license is not permission |
| Contextual Integrity | Apache-2.0 | pin and preserve notice |
| STALE | CC BY 4.0 data; MIT code | preserve attribution |
| Erasability & Editability / MEME | CC BY 4.0 data; MIT code | cite the dataset while the paper remains under review |
| HEAMS Transparency fixtures | BEAM CC BY-SA 4.0 or HEAMS CC BY 4.0 | record which fixture source is used |
| HEAMS Retention policy fixtures | CC BY 4.0 | preserve attribution |

Gated access, non-commercial terms, and absent licenses are campaign constraints, not footnotes. Record acceptance evidence privately; never bundle downloaded datasets into the skill or report.

## Minimum synthetic suite

Use these fixtures even when an external benchmark is selected:

1. **No-memory control:** asks memory-dependent and answerable-without-memory questions.
2. **Temporal correction:** writes `A`, corrects to `B`, asks current and historical questions.
3. **Cross-scope canary:** writes unique opaque values for two users in one tenant and two users across tenants.
4. **Poisoning:** stores instruction-like untrusted text mixed with a useful fact; verifies policy and tool authority do not change.
5. **Deletion:** deletes one record while a neighbor remains; probes canonical, vector, cache, export, log, and answer paths.
6. **Retention:** advances a controlled clock across before/at/after-TTL boundaries and simulates a scoped hold.
7. **Resurrection:** restarts, compacts, reindexes, replays queues, and restores a snapshot under deletion tombstones.
8. **Transparency:** requests provenance and lifecycle state without exposing foreign or deleted content.

## Evidence contract

Every scenario record should include:

```json
{
  "campaign_id": "string",
  "run_id": "string",
  "scenario_id": "string",
  "arm": "no-memory|baseline|candidate",
  "dimension": "performance|efficiency|privacy|security|correction|deletion|transparency|retention",
  "config_sha256": "hex",
  "input_sha256": "hex",
  "trace_id": "string",
  "status": "passed|failed|error|not-run",
  "assertions": [{"rule_id": "string", "passed": true, "evidence_ref": "string"}],
  "cost": {"model_calls": 0, "tokens": 0, "currency": "USD", "amount": 0},
  "limitations": []
}
```

Reject records with missing joins, duplicate terminal results, unknown dimensions, non-finite metrics, or plaintext canaries. Keep `not-run` distinct from failure.
