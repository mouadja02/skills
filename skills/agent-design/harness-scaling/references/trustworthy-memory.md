# Trustworthy Memory Design

From arXiv:2605.26112v1 — Shangding Gu, UC Berkeley, May 2026.

The central failure mode for agent memory is **stale-but-confident**: outdated stored facts remain highly ranked through semantic search, leading the agent to act confidently on invalidated assumptions — often with destructive results.

---

## The Core Problem: Stale-but-Confident

```
Timeline:
  Day 0: Agent writes memory "file_x.py contains function foo()"  [confidence: 0.95]
  Day 14: Developer deletes file_x.py
  Day 15: Agent retrieves memory, ranks it HIGH (semantic similarity still matches)
  Day 15: Agent calls "edit function foo() in file_x.py" → ERROR / wrong action

The agent is CONFIDENT. The agent is WRONG.
Semantic similarity does not degrade with staleness.
```

**Why this is worse than "agent doesn't know":**
- The agent acts, rather than asking for clarification
- The action may be destructive (deleting, overwriting, calling wrong API endpoint)
- The agent may retry with variations when the first attempt fails, compounding errors

---

## Principle: Make Trust a Runtime Decision

Memory entries should not have **stored trust** — they should have **stored metadata** from which trust is **derived at retrieval time**.

**Wrong model:**
```python
# BAD: Trust baked in at write time and never updated
entry = {"content": "file_x.py exists", "trust": "high"}
```

**Right model:**
```python
# GOOD: Trust derived at retrieval time from staleness + confidence + risk
entry = {
    "content": "file_x.py exists",
    "confidence": 0.95,           # How sure was the agent when it wrote this?
    "last_verified": "2026-05-01", # When was this last confirmed against live env?
    "source": "file_list_tool",   # What generated this fact?
}
# At retrieval time, compute: effective_trust = f(confidence, staleness, action_risk)
```

---

## Memory Entry Schema

Full schema for trustworthy memory entries (CheetahClaws approach):

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class MemoryScope(Enum):
    USER = "user"         # Persists across all sessions for this user
    PROJECT = "project"  # Persists for this project/codebase
    SESSION = "session"  # Volatile — cleared at session end

class VerificationStatus(Enum):
    UNVERIFIED = "unverified"   # Never checked against live env
    VERIFIED = "verified"       # Recently confirmed
    STALE = "stale"             # Due for re-verification
    CONTRADICTED = "contradicted" # Live env contradicts this entry

@dataclass
class MemoryEntry:
    # Identity
    id: str                              # UUID
    content: str                         # The stored fact (plain text or structured)

    # Trust axes (used for retrieval ranking)
    confidence: float                    # 0.0–1.0: how reliable was the source?
    last_verified: datetime              # Last time confirmed against live env
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    # Temporal metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None  # None = no hard expiry

    # Provenance
    source: str = ""                     # Tool/agent that generated this
    source_type: str = ""               # "tool_call" | "agent_inference" | "user_provided"
    scope: MemoryScope = MemoryScope.SESSION

    # Conflict tracking
    supersedes: Optional[str] = None    # ID of entry this one replaces
    contradicted_by: Optional[str] = None  # ID of newer entry that contradicts this

    # Tags for categorical retrieval
    tags: list[str] = field(default_factory=list)
```

---

## Retrieval with Confidence-Gated Risk

Different actions require different levels of memory trust. A destructive action (file delete) requires higher trust than a read action (file list).

```python
class TrustRequirement(Enum):
    LOW = 0.3       # Read-only, low-risk actions
    MEDIUM = 0.6    # Write actions, reversible changes
    HIGH = 0.85     # Destructive/irreversible actions
    CRITICAL = 0.95 # Actions with external side effects

def retrieve_for_action(
    query: str,
    action_risk: TrustRequirement,
    memory_store: MemoryStore,
) -> list[MemoryEntry]:
    """Retrieve memories with confidence threshold based on action risk."""
    now = datetime.utcnow()

    candidates = memory_store.semantic_search(query, top_k=20)
    trusted = []

    for entry in candidates:
        # Compute effective trust at retrieval time
        days_stale = (now - entry.last_verified).days
        staleness_penalty = min(days_stale / 30.0, 0.9)

        effective_confidence = entry.confidence * (1 - staleness_penalty)

        # Apply risk gate
        if effective_confidence >= action_risk.value:
            trusted.append((effective_confidence, entry))
        else:
            # Trust insufficient — flag for re-verification before acting
            entry.verification_status = VerificationStatus.STALE

    trusted.sort(reverse=True)
    return [e for _, e in trusted]
```

---

## Verification Loops

### Pattern 1: Lazy Verification (Default)

Re-verify only when the action risk warrants it or when staleness threshold is exceeded.

```python
async def act_with_lazy_verification(
    task: Task,
    memory: MemoryStore,
    env: LiveEnvironment,
    risk: TrustRequirement,
):
    entries = retrieve_for_action(task.query, risk, memory)

    needs_verification = [
        e for e in entries
        if e.verification_status == VerificationStatus.STALE
        or (datetime.utcnow() - e.last_verified).days > STALE_THRESHOLD_DAYS
    ]

    for entry in needs_verification:
        live_result = await env.verify_fact(entry.content)
        if live_result.contradicts(entry):
            # Live env says this is wrong
            memory.mark_contradicted(entry, by=live_result.as_entry())
            entries.remove(entry)
            entries.append(live_result.as_entry())  # Use fresh data
        else:
            memory.refresh_verification(entry)

    # Now act with verified entries
    return await execute_action(task, verified_context=entries)
```

### Pattern 2: Eager Verification (High-Risk Actions)

Re-verify all relevant memory before any destructive or irreversible action.

```python
async def act_with_eager_verification(task: Task, memory: MemoryStore, env: LiveEnvironment):
    """For HIGH/CRITICAL risk actions: verify EVERYTHING before acting."""
    entries = memory.retrieve_all_relevant(task.query)

    # Re-verify every entry, regardless of age
    verified_entries = []
    contradictions = []

    for entry in entries:
        live = await env.verify_fact(entry.content)
        if live.contradicts(entry):
            contradictions.append((entry, live))
            memory.mark_contradicted(entry, by=live.as_entry())
        else:
            memory.refresh_verification(entry)
            verified_entries.append(entry)

    if contradictions:
        # Surface contradictions before acting
        report = format_contradiction_report(contradictions)
        raise MemoryContradictionError(
            f"Found {len(contradictions)} stale memory entries that contradict "
            f"current live state. Review before proceeding:\n{report}"
        )

    return await execute_action(task, verified_context=verified_entries)
```

---

## Conflict Resolution

When a new observation contradicts an existing memory entry:

```python
def resolve_conflict(
    existing: MemoryEntry,
    incoming: MemoryEntry,
    strategy: str = "confidence_with_recency_tiebreak"
) -> MemoryEntry:
    """
    Resolve conflict between existing and new memory entries.
    Returns the winner.
    """
    if strategy == "recency_wins":
        # Simple: newer fact wins always
        winner = incoming if incoming.created_at > existing.created_at else existing

    elif strategy == "confidence_wins":
        # Higher confidence wins
        winner = incoming if incoming.confidence > existing.confidence else existing

    elif strategy == "confidence_with_recency_tiebreak":
        # Confidence wins; recency breaks ties
        if abs(incoming.confidence - existing.confidence) < 0.05:
            winner = incoming if incoming.created_at > existing.created_at else existing
        else:
            winner = incoming if incoming.confidence > existing.confidence else existing

    elif strategy == "tool_over_inference":
        # Facts from tool calls are more reliable than agent inference
        if incoming.source_type == "tool_call" and existing.source_type == "agent_inference":
            winner = incoming
        elif existing.source_type == "tool_call" and incoming.source_type == "agent_inference":
            winner = existing
        else:
            # Both same type: use confidence + recency
            winner = max([existing, incoming],
                        key=lambda e: (e.confidence, e.created_at))

    # Mark the loser as superseded (don't delete — preserve history)
    loser = existing if winner is incoming else incoming
    loser.verification_status = VerificationStatus.CONTRADICTED
    loser.contradicted_by = winner.id
    winner.supersedes = loser.id

    return winner
```

---

## Memory Hygiene: Preventing Drift and Pollution

### Staleness Decay Schedule

```python
STALENESS_POLICY = {
    # (source_type, scope) → re-verification interval in days
    ("tool_call", "session"):  1,   # Session-scope facts verified every turn
    ("tool_call", "project"):  7,   # Project facts re-verified weekly
    ("tool_call", "user"):     30,  # User facts re-verified monthly
    ("agent_inference", "*"):  3,   # Inferences are less reliable, verify sooner
    ("user_provided", "*"):    90,  # User-provided facts relatively stable
}
```

### Periodic Consolidation

Run consolidation to prevent unbounded memory growth and drift:

```python
async def consolidate_memory(memory: MemoryStore, env: LiveEnvironment):
    """
    Periodic maintenance task:
    1. Re-verify stale entries
    2. Merge contradicted entries
    3. Compress redundant entries
    4. Archive low-confidence entries
    """
    now = datetime.utcnow()
    all_entries = memory.get_all()

    stats = {"verified": 0, "contradicted": 0, "archived": 0, "merged": 0}

    for entry in all_entries:
        days_stale = (now - entry.last_verified).days
        threshold = STALENESS_POLICY.get(
            (entry.source_type, entry.scope.value),
            STALENESS_POLICY.get((entry.source_type, "*"), 14)
        )

        if days_stale > threshold:
            live = await env.verify_fact(entry.content)
            if live.contradicts(entry):
                memory.mark_contradicted(entry, by=live.as_entry())
                stats["contradicted"] += 1
            else:
                memory.refresh_verification(entry)
                stats["verified"] += 1

        # Archive very low confidence entries
        if entry.confidence < 0.3:
            memory.archive(entry)
            stats["archived"] += 1

    # Merge near-duplicate entries (same fact, slightly different wording)
    duplicates = find_near_duplicates(all_entries, threshold=0.95)
    for group in duplicates:
        canonical = max(group, key=lambda e: (e.confidence, e.last_verified))
        for dup in group:
            if dup.id != canonical.id:
                memory.mark_superseded(dup, by=canonical)
                stats["merged"] += 1

    return stats
```

---

## Memory Trust Anti-Patterns

| Anti-Pattern | Description | Fix |
|-------------|-------------|-----|
| **Semantic trust fallacy** | Assuming high cosine similarity = trustworthy content | Penalize by staleness independently of semantic score |
| **Unbounded confidence** | Writing entries with confidence=1.0 always | Cap confidence at 0.95; reserve 1.0 for human-verified facts only |
| **No provenance** | Entries without source tracking | Mandatory `source` and `source_type` fields |
| **Delete on contradiction** | Deleting old entries when contradicted | Mark as `CONTRADICTED`, preserve for audit/temporal queries |
| **Global trust** | Same trust level for all entries regardless of action risk | Apply confidence gates proportional to action risk level |
| **Forget-on-session-end** | Never persisting useful session-scope facts | Auto-extract high-confidence, low-scope facts to project scope at session end |

---

## Evaluation Metrics for Memory Trustworthiness

| Metric | Definition | Target |
|--------|-----------|--------|
| Memory hygiene score | % entries within staleness threshold | > 0.85 |
| Contradiction detection rate | % contradicted entries flagged before they cause errors | > 0.95 |
| Retrieval precision | % retrieved entries that are accurate at action time | > 0.90 |
| Confidence calibration | Correlation between stored confidence and actual accuracy | > 0.80 |
| Provenance coverage | % entries with source + timestamp | 1.0 |
| Stale action rate | % agent actions based on later-disproven memory | < 0.05 |
