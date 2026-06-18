---
name: provenance-grounded-memory
description: >
  Use when designing or auditing long-term memory for persistent AI agents. Stores immutable source
  evidence before canonical facts, links beliefs to provenance, applies novelty-aware ADD/UPDATE/NOOP
  write gating, keeps uncertain merges explicit, separates retrieval from answer generation, supports
  deletion, and evaluates memory failures layer by layer.
source: "https://arxiv.org/abs/2605.30771; https://arxiv.org/abs/2605.30711"
attribution: "Derived from Eywa: Provenance-Grounded Long-Term Memory for AI Agents and SAGE: A Novelty Gate for Efficient Memory Evolution in Agentic LLMs"
---

# Provenance-Grounded Agent Memory

Build memory around evidence before belief. Persistent agents need memory that can be retrieved, audited,
updated, corrected, and erased without collapsing raw evidence, derived beliefs, retrieval logic, and answer
policy into one opaque prompt path.

## When to Activate

Activate when:
- Adding cross-session memory to an agent
- Auditing stale, contradictory, duplicated, or unsupported memories
- Reducing write-side LLM calls in a growing memory store
- Separating memory retrieval quality from answer-model behavior
- Implementing user-visible correction, deletion, or provenance inspection

## Architecture

```text
Raw evidence (immutable)
    -> typed signals and hard anchors
    -> candidate canonical facts
    -> provenance validation
    -> novelty-aware write gate
       -> ADD
       -> NOOP
       -> UPDATE / MERGE with LLM only when uncertain
    -> canonical fact store linked to evidence
    -> deterministic multi-route retrieval
    -> bounded retrieved context
    -> separate answer policy and answer model
```

## Paper-Backed Principles

1. **Evidence before belief.** Preserve immutable source evidence before promoting derived facts.
2. **Provenance is not truth.** It shows where a claim came from and whether extraction is supported, not
   whether the source statement is world-level truth.
3. **Retrieval and answer synthesis should be separable.** Evaluate the memory substrate independently from
   the answer model.
4. **Write-side control matters.** Memory quality degrades when systems append duplicates, merge unrelated
   facts, or route every candidate through expensive LLM deliberation.
5. **Novelty gating is a useful write abstraction.** Resolve clearly novel facts as `ADD`, clearly redundant
   facts as `NOOP`, and send ambiguous cases to an `UPDATE` or merge path.

## Data Model

```yaml
evidence:
  id: evidence-001
  uri: source-or-session
  content_hash: sha256
  captured_at: ISO-8601
  immutable: true
  deletion_scope: user|project|organization

fact:
  id: fact-001
  statement: text
  evidence_ids: [evidence-001]
  entity_scope: []
  temporal_scope: {}
  typed_signals: []
  status: active|superseded|deleted|needs-review
  confidence: 0.0
  last_verified_at: ISO-8601
```

## Workflow

### Step 1: Capture Immutable Evidence

Store the original source before extraction. Preserve source ID, capture time, content hash, access scope,
and deletion semantics.

### Step 2: Extract Typed Signals

Detect signals such as:
- Entities
- Dates and temporal qualifiers
- Decisions
- Corrections
- Preferences
- Hard anchors such as exact paths, identifiers, or commitments

Validate derived facts against source support before promotion.

### Step 3: Apply the Write Gate

Compute a novelty score against the current memory scope. Use an adaptive threshold that changes as store
density changes.

```text
if store is empty:
    ADD
elif novelty >= threshold + uncertainty_margin:
    ADD
elif novelty < threshold:
    NOOP
else:
    UPDATE_OR_MERGE_WITH_LLM
```

The exact scoring function is implementation-specific. SAGE uses a von Mises-Fisher density estimate over
normalized memory embeddings. Do not invent universal thresholds; calibrate on a deployment-specific split.

### Step 4: Link Canonical Facts to Evidence

Every promoted fact must retain:
- Supporting evidence IDs
- Extraction version
- Superseded fact IDs when updated
- Confidence and verification timestamps
- Deletion relationship to its sources

### Step 5: Retrieve Through Multiple Deterministic Routes

Combine bounded routes such as:
- Entity scope
- Temporal metadata
- Keyword search
- Vector similarity
- Canonical facts
- Raw observations when needed

Return retrieved evidence separately from answer instructions.

### Step 6: Evaluate by Failure Layer

For each wrong answer, classify:

| Layer | Failure |
| --- | --- |
| Evidence capture | Original evidence missing |
| Extraction | Unsupported or omitted fact |
| Write gate | Wrong ADD, NOOP, or UPDATE decision |
| Canonical store | Stale, contradictory, or duplicated state |
| Retrieval | Relevant fact not selected within budget |
| Answer policy | Evidence received but misused, overgeneralized, or refused incorrectly |

### Step 7: Support Correction and Erasure

Deletion is first-class:
- Erase raw evidence when required
- Remove or invalidate derived facts that depend on deleted evidence
- Rebuild affected retrieval indexes
- Log the deletion result

## Metrics

- Provenance coverage
- Unsupported extraction rate
- Duplicate-memory rate
- Write-gate ADD/NOOP/UPDATE accuracy
- Merge-call rate
- Write-side token cost and latency
- Retrieval sufficiency
- Multi-hop recall
- Temporal update handling
- Abstention quality
- Deletion completeness

## Guidelines

1. Preserve evidence before creating beliefs.
2. Keep retrieval deterministic when possible.
3. Reserve expensive LLM merge calls for uncertain cases.
4. Calibrate novelty thresholds outside the target test set.
5. Keep answer instructions separate from retrieved memory.
6. Implement correction and erasure paths before production use.
7. Audit each failure at its actual layer.

## Gotchas

1. **Opaque prompt path** - Mixing evidence, facts, retrieval, and answer policy makes failures hard to repair.
2. **Provenance equals truth** - A supported extraction can still reflect a false source statement.
3. **Append-only memory** - Growing stores need write-side routing.
4. **Fixed novelty thresholds** - Store density changes over time.
5. **Hidden deletion gaps** - Removing a source without invalidating derived facts leaves ghost memory.
6. **Retrieval-score tunnel vision** - Evaluate downstream sufficiency and answer-policy behavior separately.

## References

- [Eywa: Provenance-Grounded Long-Term Memory for AI Agents](https://arxiv.org/abs/2605.30771)
- [SAGE: A Novelty Gate for Efficient Memory Evolution in Agentic LLMs](https://arxiv.org/abs/2605.30711)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.0.0
