# Context Governance Patterns

From arXiv:2605.26112v1 — Shangding Gu, UC Berkeley, May 2026.

Context governance is about treating the context window as the **output of a selection policy**, not a passive accumulation buffer. The central failure mode is "exposure without access": the model can technically attend to facts in the context, but signal dilution from low-relevance content prevents reliable access.

---

## The Core Problem: Exposure Without Access

**What goes wrong:**
1. Agent loads a large context (or has access to a long context window)
2. Relevant facts are present somewhere in that context
3. Model still fails to use them because attention is diluted by irrelevant content
4. Paradox: *more context = worse performance* when context is poorly governed

**Empirical evidence:**
- Models prefer evidence at start and end of context ("lost in the middle" effect)
- Privacy drift: sensitive tokens from earlier context leak into generation inappropriately
- Attention scarcity: too many competing items forces the model to guess which to prioritize

---

## The Three-Layer Context Strategy

Based on the Claude Code pattern described in the paper:

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Persistent Priors                                   │
│  ─ Loaded once at session start                              │
│  ─ Stable configuration: CLAUDE.md, project guidelines       │
│  ─ Examples: code style rules, domain vocabulary, constraints │
│  ─ High trust: human-curated, versioned                      │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: JIT Memory Retrieval                               │
│  ─ Retrieved per-turn based on current task                  │
│  ─ From memory store with staleness-penalized ranking        │
│  ─ Treated as hypothesis until re-verified                   │
│  ─ Medium trust: confidence-gated                            │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Live Environment Search                            │
│  ─ Always fresh — never cached across turns                  │
│  ─ Tool calls: glob, grep, ls, API queries                   │
│  ─ Prevents reliance on stale indices                        │
│  ─ Highest trust for current state                           │
└──────────────────────────────────────────────────────────────┘
```

**Why this hybrid design?**

- Static indexing alone fails when files are renamed, deleted, or modified
- Full live search on every turn is too expensive
- Memory retrieval alone uses stale data
- **The combination gives: stable context from priors + relevant history from memory + accurate current state from live search**

---

## Context Selection Policy

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class ContextItem:
    content: str
    source_id: str          # Provenance identifier
    timestamp: datetime     # When was this content generated/verified
    source_type: str        # "persistent_prior" | "memory" | "live_search"
    relevance_score: float  # Semantic similarity to current task
    token_count: int        # Pre-computed token count

class ContextSelectionPolicy:
    """
    Assembles context for a given task within a token budget.
    Implements relevance × recency × source-trust ranking.
    """

    # Source trust weights (persistent priors most stable)
    SOURCE_TRUST = {
        "persistent_prior": 1.0,
        "live_search": 0.95,   # Fresh but not curated
        "memory": 0.80,        # Historical, penalized by staleness
    }

    def select(self, task: str, candidates: list[ContextItem], budget: int) -> list[ContextItem]:
        scored = []
        now = datetime.utcnow()

        for item in candidates:
            # Recency weight: decays over 7 days for memory, not applied to live/priors
            if item.source_type == "memory":
                days_old = (now - item.timestamp).days
                recency = max(0.1, 1.0 - (days_old / 7.0))
            else:
                recency = 1.0

            trust = self.SOURCE_TRUST[item.source_type]

            score = item.relevance_score * recency * trust
            scored.append((score, item))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Greedy packing within budget
        selected = []
        remaining = budget
        for score, item in scored:
            if item.token_count <= remaining:
                selected.append(item)
                remaining -= item.token_count

        return selected
```

---

## Provenance Tracking

Every token in context should have a known origin. This enables:
- Audit-time attribution ("why did the agent do X? → because context item Y said Z")
- Trust calibration (live search > memory > stale index)
- Debugging ("the wrong answer came from a stale cache entry from 3 days ago")

```python
@dataclass
class ProvenanceRecord:
    source_id: str              # Unique ID of the context item
    source_type: str            # "persistent_prior" | "memory" | "live_search"
    source_uri: str             # File path, URL, memory entry ID, etc.
    created_at: datetime        # When the content was originally generated
    verified_at: Optional[datetime]  # When it was last verified against live state
    confidence: float           # 0.0–1.0

class ProvenanceTracker:
    def __init__(self):
        self._records: dict[str, ProvenanceRecord] = {}

    def register(self, item: ContextItem) -> str:
        """Register a context item and return its provenance ID."""
        record = ProvenanceRecord(
            source_id=item.source_id,
            source_type=item.source_type,
            source_uri=item.source_uri,
            created_at=item.timestamp,
            verified_at=item.verified_at,
            confidence=item.confidence
        )
        self._records[item.source_id] = record
        return item.source_id

    def explain(self, source_id: str) -> str:
        """Return human-readable provenance for audit."""
        r = self._records.get(source_id)
        if r is None:
            return "Unknown source"
        age = (datetime.utcnow() - r.created_at).days
        return (
            f"Source: {r.source_uri} ({r.source_type}), "
            f"created {age}d ago, confidence={r.confidence:.2f}"
        )
```

---

## Refresh Policy Design

The refresh policy determines when context is considered stale and needs re-fetching.

| Content Type | Refresh Trigger | Strategy |
|-------------|----------------|----------|
| Persistent priors (CLAUDE.md, config) | File changes only | Load once per session; watch for edits |
| Memory entries | >7 days stale OR confidence <0.6 | Re-verify on access before acting |
| Live environment state | Every turn (or every N steps) | Always call live tool; never cache across turns |
| Conversation history | Sliding window | Keep last K turns; summarize earlier turns |
| Tool outputs | Per-call | Never reuse across turns (stale side-effects) |

```python
class RefreshPolicy:
    STALE_THRESHOLDS = {
        "persistent_prior": None,        # Never auto-stale (changed by human edit)
        "memory": timedelta(days=7),     # Re-verify after 7 days
        "live_search": timedelta(hours=0), # Always re-fetch
        "conversation": timedelta(hours=24), # Summarize after 24h
    }

    def is_stale(self, item: ContextItem) -> bool:
        threshold = self.STALE_THRESHOLDS.get(item.source_type)
        if threshold is None:
            return False  # Persistent priors never auto-stale
        age = datetime.utcnow() - item.timestamp
        return age > threshold

    def refresh_action(self, item: ContextItem) -> str:
        """Returns the action to take for a stale item."""
        if item.source_type == "memory":
            return "re_verify_against_live"
        elif item.source_type == "live_search":
            return "re_execute_tool_call"
        elif item.source_type == "conversation":
            return "summarize_and_compress"
        return "reload"
```

---

## Context Compactness: Minimum Sufficient Token Set

The goal is not to maximize context richness, but to find the **minimum sufficient context** for the subproblem.

**Anti-patterns:**
- Loading an entire codebase when only one function is needed
- Preloading all user preferences when only one setting is relevant
- Including full conversation history when only the last 3 turns matter

**Patterns:**
```python
# Anti-pattern: Load everything
context = load_entire_project_codebase()  # 500K tokens

# Pattern: Load minimum sufficient context
context = (
    load_relevant_files(task, max_files=10)     # JIT via glob/grep
    + load_related_tests(task, max_tests=5)
    + load_documentation_section(task)
)
# Total: ~20K tokens, all relevant
```

**Subproblem decomposition for large tasks:**

```python
def construct_subproblem_context(task: str, subtask: str, budget: int) -> Context:
    """
    For multi-step tasks: construct MINIMAL context for each subproblem.
    Don't carry the entire task context into every subagent.
    """
    # What does THIS subproblem actually need?
    required_knowledge = identify_knowledge_requirements(subtask)

    # Retrieve only that knowledge
    context_items = [
        retrieve_relevant_memory(req, budget=budget // len(required_knowledge))
        for req in required_knowledge
    ]

    return flatten_and_deduplicate(context_items, budget)
```

---

## Context Degradation Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| **Lost in the middle** | Model fails to use facts in middle of context window | Place critical facts at start/end |
| **Attention dilution** | Irrelevant content competes with relevant content | Apply relevance filtering with minimum score threshold |
| **Privacy drift** | Sensitive tokens from early context leak into generation | Scope context per subagent; don't pass full context across boundaries |
| **Context poisoning** | Low-quality, irrelevant content displaces useful content | Use minimum-token policy; filter by relevance before loading |
| **Stale index reliance** | Agent uses cached file list instead of live glob | Mandate live search for file system state |
| **Cross-turn contamination** | Context from turn N pollutes turn N+1 | Implement explicit context flush policies |

---

## Evaluation Metrics for Context Governance

| Metric | Formula | Target |
|--------|---------|--------|
| Context efficiency | Useful tokens / total tokens | > 0.7 |
| Retrieval precision | Relevant items / retrieved items | > 0.8 |
| Provenance coverage | Traceable tokens / total tokens | 1.0 |
| Context freshness | % items within staleness threshold | > 0.9 |
| Budget utilization | Tokens used / budget | 0.6–0.9 (not wasteful, not over-stuffed) |
