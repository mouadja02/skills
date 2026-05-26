# Six-Component Harness Architecture

Reference for the formal framework from arXiv:2605.26112v1 (Shangding Gu, UC Berkeley, May 2026).

**Formula:** `𝒫_H = Φ(ℛ, ℳ, 𝒞, 𝒮, 𝒪, 𝒢)`

---

## ℛ — Reasoning Substrate (Foundation Model)

The base LLM. This is the component improved by traditional "model scaling."

**Sub-axes:**
- Raw language understanding and generation capability
- Tool use / function calling proficiency
- Instruction following fidelity
- Context length utilization efficiency

**Scaling levers:** Model size, training data quality, RLHF/RLAIF alignment, inference compute (chain-of-thought, extended thinking)

**Harness implication:** ℛ improvements are necessary but not sufficient. The same ℛ produces radically different agents depending on ℳ, 𝒞, 𝒮, 𝒪, 𝒢 design.

---

## ℳ — Memory Store

Persistent information layer enabling the agent to accumulate knowledge across turns and sessions.

### Four Quality Axes

| Axis | Definition | Measurement | Failure Mode |
|------|-----------|-------------|--------------|
| **Precision** | Accuracy within defined scope | Recall@k on retrieval benchmark | Overgeneralized or hallucinated facts stored |
| **Durability** | Resistance to target drift | Delta between entry-write and entry-retrieval quality over time | Silent rewrites; facts mutate without audit |
| **Retrievability** | Cost-effective access to correct facts | Latency + precision of retrieval | Important facts buried; retrieval too expensive |
| **Verifiability** | Ability to validate content against live environment | % of entries with valid verification timestamp | Stale-but-confident; confident action on outdated state |

### Memory Types by Timescale

```
Working Memory     → Context window (volatile)
                       ↓ auto-extract on session end
Short-term Memory  → Session file / in-memory cache (session-scoped)
                       ↓ confidence-gated consolidation
Long-term Memory   → Structured store with confidence + recency fields (persistent)
                       ↓ periodic re-verification against live environment
```

### CheetahClaws Memory Entry Schema

```python
@dataclass
class MemoryEntry:
    id: str                        # Unique identifier
    content: str                   # The stored fact
    confidence: float              # 0.0–1.0, explicit or derived
    last_verified: datetime        # Last time checked against live env
    created_at: datetime           # When first written
    source: str                    # Provenance: which tool/agent wrote this
    scope: str                     # "user" | "project" | "session"
    valid_until: Optional[datetime]  # None = no hard expiry
    tags: list[str]               # For categorical retrieval
    conflict_id: Optional[str]    # Points to superseded entry
```

### Retrieval Ranking with Staleness Penalty

```python
def rank_memories(query: str, entries: list[MemoryEntry], now: datetime) -> list[MemoryEntry]:
    """
    Rank memory entries by composite score:
      score = semantic_similarity × (1 - staleness_penalty) × confidence
    """
    scored = []
    for entry in entries:
        # Staleness in days since last verification
        days_stale = (now - entry.last_verified).total_seconds() / 86400

        # Staleness penalty: 0.0 (fresh) to 0.9 (30+ days stale)
        staleness_penalty = min(days_stale / 30.0, 0.9)

        # Composite score
        score = (
            semantic_similarity(query, entry.content)
            * (1 - staleness_penalty)
            * entry.confidence
        )
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored]
```

### Verification Loop Pattern

```python
async def retrieve_and_verify(query: str, memory: MemoryStore, env: LiveEnvironment):
    """Retrieve memory entries and re-verify freshness before acting."""
    candidates = memory.retrieve(query)

    verified = []
    for entry in candidates:
        if needs_verification(entry):  # e.g., >7 days stale or high-risk action
            live_check = await env.verify(entry)
            if live_check.contradicts(entry):
                memory.flag_stale(entry, live_check)
                # Use live_check result instead
                verified.append(live_check.as_entry())
            else:
                memory.refresh_timestamp(entry)
                verified.append(entry)
        else:
            verified.append(entry)

    return verified

def needs_verification(entry: MemoryEntry, threshold_days: int = 7) -> bool:
    """Return True if entry is stale enough to require re-verification."""
    days_stale = (datetime.utcnow() - entry.last_verified).days
    return days_stale >= threshold_days or entry.confidence < 0.6
```

---

## 𝒞 — Context Constructor

The input assembly mechanism: what gets loaded into the context window and how.

### Four Quality Axes

| Axis | Definition | Measurement | Failure Mode |
|------|-----------|-------------|--------------|
| **Relevance** | Pertinence to current task | Precision of retrieved content | Noise displaces signal; attention diluted |
| **Compactness** | Minimal sufficient token set | Tokens used / tokens needed ratio | Over-stuffing; "lost in the middle" degradation |
| **Traceability** | Source provenance per token | % of context tokens with known source | No audit trail; can't trace wrong answers |
| **Refresh Policy** | Adaptation to environmental changes | Staleness of loaded content | Stale static indices used instead of live state |

### Context Assembly Strategy (Hybrid)

```python
class ContextConstructor:
    """
    Three-layer context assembly:
      Layer 1: Persistent priors (loaded at session start, rarely changed)
      Layer 2: JIT retrieval (memory store, task-specific)
      Layer 3: Live environment search (always fresh, never cached)
    """

    def assemble(self, task: str, token_budget: int) -> AssembledContext:
        budget_remaining = token_budget

        # Layer 1: Persistent priors (e.g., CLAUDE.md, project config)
        # These are stable and can be loaded once per session
        priors = self.load_persistent_priors()
        priors_tokens = count_tokens(priors)
        budget_remaining -= priors_tokens

        # Layer 2: JIT retrieval from memory store
        # Only pull what's needed for this specific task
        retrieved = self.retrieve_from_memory(task, budget=budget_remaining // 2)
        retrieved_tokens = count_tokens(retrieved)
        budget_remaining -= retrieved_tokens

        # Layer 3: Live environment search
        # Glob/grep/tool calls — never stale, always accurate
        live_state = self.search_live_environment(task, budget=budget_remaining)

        # Combine with provenance tracking
        return AssembledContext(
            priors=priors,
            retrieved=retrieved,
            live=live_state,
            provenance={
                item.id: ContextSource(
                    source_type=item.source_type,
                    timestamp=item.timestamp,
                    verification_status=item.verified
                )
                for item in [*retrieved, *live_state]
            }
        )
```

### Token Budget Allocation

```python
# Recommended allocation for a 100K-token context window
CONTEXT_BUDGET = {
    "persistent_priors": 0.15,    # 15K: system prompt, project config
    "task_instructions": 0.10,   # 10K: current task specification
    "memory_retrieval": 0.25,    # 25K: relevant historical knowledge
    "live_state": 0.30,          # 30K: fresh environment data (files, tool outputs)
    "conversation_history": 0.15, # 15K: recent turns
    "output_buffer": 0.05,       # 5K: reserve for model output
}
```

### The "Lost in the Middle" Mitigation

```python
def pack_context_with_attention_awareness(items: list[ContextItem], budget: int) -> str:
    """
    Place highest-priority items at START and END of context.
    The model attends poorly to middle-context content.
    """
    ranked = sorted(items, key=lambda x: x.priority, reverse=True)

    high_priority = ranked[:len(ranked)//3]   # Top third → context start
    medium_priority = ranked[len(ranked)//3:2*len(ranked)//3]  # Middle → context middle
    low_priority = ranked[2*len(ranked)//3:]  # Bottom third → between high and end

    # Place high priority at start, medium in middle, bring critical facts back to end
    critical_for_end = [x for x in high_priority if x.must_be_near_end]
    start_items = [x for x in high_priority if not x.must_be_near_end]

    ordered = start_items + medium_priority + low_priority + critical_for_end
    return truncate_to_budget(ordered, budget)
```

---

## 𝒮 — Skill-Routing Layer

Tool and subagent dispatch mechanism.

### Four Quality Axes

| Axis | Definition | Measurement | Failure Mode |
|------|-----------|-------------|--------------|
| **Specificity** | Clear capability scope per skill | % of invocations where skill matches task type | Ambiguous routing; wrong tool selected |
| **Selectivity** | Correct skill invocation rate | Top-1 routing accuracy | Skill chosen doesn't match task |
| **Composability** | Sequential integration across skills | End-to-end pipeline success rate | Upstream output format breaks downstream skill |
| **Verifiability** | Explicit post-condition validation | % of invocations with passing post-condition | Confident-but-unchecked outputs accepted |

### Skill Specification Template

```python
@dataclass
class SkillSpec:
    name: str
    description: str

    # Capability scope — what this skill CAN do
    capability_scope: list[str]

    # Input contract
    input_schema: dict  # JSON Schema

    # Output contract
    output_schema: dict  # JSON Schema

    # Post-conditions: must pass after execution
    postconditions: list[Callable]

    # Confidence threshold for routing to this skill
    min_confidence: float = 0.7

    # Escalation target if confidence below threshold
    escalation_skill: Optional[str] = None

# Example skill spec
read_file_skill = SkillSpec(
    name="read_file",
    description="Read a file from the filesystem and return its contents",
    capability_scope=["file_read", "content_retrieval"],
    input_schema={"path": {"type": "string", "description": "Absolute file path"}},
    output_schema={"content": {"type": "string"}, "exists": {"type": "boolean"}},
    postconditions=[
        lambda task, result: result.get("exists") is not None,  # existence confirmed
        lambda task, result: not result.get("exists") or len(result.get("content", "")) >= 0,
    ],
    min_confidence=0.8,
)
```

### Adaptive Routing with Escalation

```python
class SkillRouter:
    def __init__(self, skill_registry: dict[str, SkillSpec]):
        self.registry = skill_registry
        self.routing_history: list[RoutingDecision] = []

    async def route(self, task: SubTask) -> Result:
        # Estimate task type
        task_type, confidence = self.classify_task(task)

        # Confidence-aware escalation
        skill_name = task_type.label
        skill = self.registry.get(skill_name)

        if skill is None or confidence < skill.min_confidence:
            # Route to more capable / general skill
            skill_name = skill.escalation_skill or "general_agent"
            skill = self.registry[skill_name]

        # Execute
        result = await skill.execute(task)

        # Post-condition verification — MANDATORY
        all_pass = all(
            postcond(task, result)
            for postcond in skill.postconditions
        )

        if not all_pass:
            # Don't accept unverified output — escalate or retry
            result = await self.handle_postcondition_failure(task, result, skill)

        # Log routing decision for audit
        self.routing_history.append(RoutingDecision(
            task=task,
            skill_chosen=skill_name,
            confidence=confidence,
            postconditions_passed=all_pass,
            timestamp=datetime.utcnow(),
        ))

        return result
```

---

## 𝒪 — Orchestration Loop

The control flow coordinator. Manages the execution sequence across ℛ, ℳ, 𝒞, 𝒮, and 𝒢.

**Responsibilities:**
- Decompose high-level tasks into subtasks
- Dispatch subtasks to appropriate 𝒮 skills
- Aggregate results while tracking provenance
- Manage context budget across multi-step tasks
- Handle errors, retries, and escalation
- Coordinate between multiple agents in multi-agent setups

**Orchestration Loop Pseudocode:**

```python
async def orchestration_loop(objective: str, max_steps: int = 50) -> FinalResult:
    context = context_constructor.assemble(objective, TOKEN_BUDGET)
    memory_entries = memory_store.retrieve_verified(objective)
    step = 0

    while step < max_steps:
        # Plan next action using ℛ with assembled context
        plan_step = reasoning_substrate.plan(context, memory_entries, objective)

        if plan_step.type == "TERMINAL":
            return plan_step.result

        # Route plan step to appropriate skill
        skill_result = await skill_router.route(plan_step.subtask)

        # Governance gate — before accepting result into state
        if not governance.approve(plan_step, skill_result):
            # Request human review or rollback
            governance.escalate(plan_step, skill_result)
            continue

        # Update memory with verified new facts
        memory_store.write_verified(skill_result.new_facts)

        # Refresh context for next step
        context = context_constructor.refresh(context, skill_result)
        step += 1

    raise MaxStepsExceeded(f"Did not complete in {max_steps} steps")
```

---

## 𝒢 — Verification and Governance

Gates intermediate reasoning and external actions. The safety and auditability layer.

**Responsibilities:**
- Verify intermediate reasoning outputs before accepting them
- Verify external action effects before committing
- Maintain audit traces for memory writes, routing changes, permissions
- Enforce permission scoping (principle of least privilege per subagent)
- Enable rollback for side-effecting actions

### Governance Gate Implementation

```python
class GovernanceGate:
    def __init__(self, audit_log: AuditLog, permission_registry: PermissionRegistry):
        self.audit = audit_log
        self.permissions = permission_registry

    def approve(self, action: PlannedAction, result: Optional[Result] = None) -> bool:
        """Gate an action. Returns True if approved, False if blocked."""

        # 1. Check permission scope
        if not self.permissions.allows(action.agent_id, action.action_type):
            self.audit.log_blocked(action, reason="permission_denied")
            return False

        # 2. Check action risk level
        if action.risk_level == "HIGH" and not action.human_approved:
            self.audit.log_pending_review(action)
            return False  # Require human approval

        # 3. Verify result if provided
        if result is not None:
            if not self.verify_result_integrity(action, result):
                self.audit.log_blocked(action, reason="result_verification_failed")
                return False

        # Approved — log for audit
        self.audit.log_approved(action, result)
        return True

    def verify_result_integrity(self, action: PlannedAction, result: Result) -> bool:
        """Check that result is consistent with expected post-conditions."""
        return action.skill.all_postconditions_pass(action.subtask, result)
```

### Audit Trail Schema

```python
@dataclass
class AuditEntry:
    timestamp: datetime
    entry_type: str  # "memory_write" | "routing_decision" | "tool_call" | "permission_change"
    agent_id: str
    action: dict
    outcome: str    # "approved" | "blocked" | "escalated"
    reason: Optional[str]
    rollback_available: bool
    rollback_id: Optional[str]  # References rollback snapshot
```

---

## Component Interaction Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestration Loop (𝒪)                      │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │    ℛ     │───▶│    𝒞     │───▶│    𝒮     │───▶│    𝒢     │  │
│  │Reasoning │    │ Context  │    │  Skills  │    │Governance│  │
│  │Substrate │    │Construct │    │ Routing  │    │    &     │  │
│  │          │    │          │    │          │    │Verificat.│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│         ▲                ▲               │               │      │
│         │                │               ▼               ▼      │
│         │         ┌──────────────────────────────────────┐      │
│         └─────────│          ℳ  Memory Store             │      │
│                   │  (confidence, recency, provenance)    │      │
│                   └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

**Data flows:**
1. ℛ plans next action using 𝒞-assembled context
2. 𝒮 executes planned action with post-condition verification
3. 𝒢 gates 𝒮 results before accepting into state
4. ℳ receives verified new facts from 𝒢-approved 𝒮 results
5. 𝒞 refreshes context from ℳ for next ℛ planning step
6. 𝒪 coordinates all of the above across steps
