---
name: harness-scaling
description: >
  Use when designing or auditing an agentic AI system holistically. Activates the six-component
  harness framework (ℛ Reasoning, ℳ Memory, 𝒞 Context, 𝒮 Skills, 𝒪 Orchestration, 𝒢 Governance)
  from arXiv:2605.26112. Trigger phrases: "design an agent system", "why is my agent unreliable",
  "harness architecture", "system-level agent design", "beyond model scaling", "agentic infrastructure",
  "scale my agent system", "agent performance bottleneck".
source: "https://arxiv.org/abs/2605.26112v1"
attribution: "Shangding Gu, UC Berkeley — 'From Model Scaling to System Scaling: Scaling the Harness in Agentic AI' (arXiv:2605.26112v1, May 2026)"
---

> **Attribution:** Derived from [arXiv:2605.26112v1](https://arxiv.org/abs/2605.26112v1) — *From Model Scaling to System Scaling: Scaling the Harness in Agentic AI* by Shangding Gu (UC Berkeley), May 2026. Reference implementation: [CheetahClaws](https://github.com/SafeRL-Lab/cheetahclaws).

# Harness Scaling for Agentic AI

Agent performance emerges from the **interaction among multiple components**, not from model capability alone. This skill encodes the insight that investing only in stronger foundation models while neglecting the surrounding harness — memory, context assembly, skill routing, and governance — yields unreliable agents regardless of model strength.

## When to Activate

Activate this skill when:
- Designing a new agentic system from scratch and choosing architectural components
- Debugging persistent agent failures that survive model upgrades
- Evaluating whether to invest in a stronger model vs. improving harness design
- Auditing a production agent for reliability, auditability, or safety gaps
- Implementing multi-agent coordination systems
- Choosing memory, context, or routing strategies for an agent deployment
- Answering: "why does my agent confidently do the wrong thing?"

## Core Concepts

### The Harness Equation

Agent harness performance is a function of six interacting components:

```
𝒫_H = Φ(ℛ, ℳ, 𝒞, 𝒮, 𝒪, 𝒢)
```

| Symbol | Component | Role |
|--------|-----------|------|
| **ℛ** | Reasoning Substrate | The foundation model; improved via model scaling |
| **ℳ** | Memory Store | Persistent information with precision, durability, retrievability, verifiability |
| **𝒞** | Context Constructor | Input assembly: relevance, compactness, traceability, refresh policy |
| **𝒮** | Skill-Routing Layer | Tool & subagent dispatch: specificity, selectivity, composability, verifiability |
| **𝒪** | Orchestration Loop | Control flow coordination across all components |
| **𝒢** | Verification & Governance | Gates reasoning outputs and external actions |

**Key insight:** Scaling 𝒮 (skills) without scaling 𝒢 (governance) produces faster but less reliable progress. Each component must scale together.

### The Three Primary Bottlenecks

The paper identifies three failure modes that survive model upgrades:

1. **Exposure without access** (context governance failure) — large context windows create *signal dilution*, not improved access
2. **Stale-but-confident** (memory trust failure) — outdated facts remain highly ranked; the agent acts destructively on invalidated assumptions
3. **Confident-but-unchecked** (skill routing failure) — specialized subagents return plausible outputs without downstream validation

### Why Model Scaling Alone Is Insufficient

Three objections and their rebuttals:

- **"Stronger models will solve system problems"** → Stale memory, over-broad permissions, missing provenance, and unsafe execution are *system failures*, not prediction failures. Stronger models don't eliminate the need for governance.
- **"End-to-end training will replace modular systems"** → Deployed agents require auditability, permission control, rollback, and provenance — these aren't optional, they're deployment requirements.
- **"System evaluation is too expensive"** → Cost and standardization challenges are precisely why evaluation is needed. Real agents face latency, monetary cost, tool risk, and memory drift.

## Detailed Topics

### Component 1: Memory Store (ℳ)

Memory has four quality axes that must be actively maintained:

| Axis | Definition | Failure Mode |
|------|-----------|--------------|
| **Precision** | Accuracy within defined scope | Overgeneralized facts |
| **Durability** | Resistance to target drift | Silent rewrites |
| **Retrievability** | Cost-effective access | Important facts buried |
| **Verifiability** | Ability to validate against live environment | Stale-but-confident |

**System move:** Make trust a *runtime decision*, not a stored property. Retrieved content is a *hypothesis* until re-checked.

**Retrieval ranking formula (CheetahClaws):**
```
rank = relevance × (1 - staleness_penalty) × confidence_factor
```

**Implementation pattern:**
```python
@dataclass
class MemoryEntry:
    content: str
    confidence: float          # 0.0 – 1.0
    last_verified: datetime    # When was this last checked against live env?
    valid_until: Optional[datetime]  # None = no expiry
    source: str               # Provenance

def retrieve(query: str, entries: list[MemoryEntry]) -> list[MemoryEntry]:
    now = datetime.utcnow()
    ranked = []
    for e in entries:
        staleness = (now - e.last_verified).total_seconds() / 86400  # days
        staleness_penalty = min(staleness / 30, 0.9)  # cap at 90% penalty
        score = semantic_similarity(query, e.content) \
                * (1 - staleness_penalty) \
                * e.confidence
        ranked.append((score, e))
    ranked.sort(reverse=True)
    # Treat top results as hypotheses — re-verify before acting
    return [e for _, e in ranked[:5]]
```

### Component 2: Context Constructor (𝒞)

Context has four quality axes:

| Axis | Definition | Failure Mode |
|------|-----------|--------------|
| **Relevance** | Pertinence to current task | Noise displaces signal |
| **Compactness** | Minimal sufficient token set | Token waste, attention dilution |
| **Traceability** | Source provenance per token | No audit trail |
| **Refresh Policy** | Adaptation to environmental changes | Stale indices |

**System move:** Treat each turn's context as output of a *selection policy*, not a fixed buffer.

**Context assembly policy:**
```python
def assemble_context(task: str, budget: int) -> Context:
    # Layer 1: Persistent priors (loaded at session start)
    persistent = load_persistent_priors()  # e.g., CLAUDE.md equivalent

    # Layer 2: Just-in-time retrieval (not static index)
    jit_facts = retrieve_verified_memory(task)

    # Layer 3: Live environment search (always fresh)
    live_state = search_live_env(task)  # glob/grep/tool calls

    # Assemble with token budget enforcement
    context = pack_by_relevance(
        sources=[persistent, jit_facts, live_state],
        budget=budget,
        weight_fn=lambda x: semantic_score(task, x) * recency_weight(x)
    )
    return context  # Every token has a source ID and timestamp
```

**The "lost in the middle" problem:** Attention degrades for content in the middle of the context window. Place most critical facts at the start or end.

### Component 3: Skill-Routing Layer (𝒮)

Skill routing has four quality axes:

| Axis | Definition | Failure Mode |
|------|-----------|--------------|
| **Specificity** | Clear capability scope per skill | Ambiguous routing |
| **Selectivity** | Correct skill invocation | Wrong tool chosen |
| **Composability** | Sequential integration across skills | Broken pipelines |
| **Verifiability** | Explicit post-condition validation | Confident-but-unchecked |

**System move:** Couple learned routing policy with verification at every step.

**Routing with post-condition verification:**
```python
async def route_and_verify(task: SubTask) -> Result:
    # Estimate task type from available context
    task_type = classify_task(task)
    confidence = task_type.confidence

    # Confidence-aware escalation
    if confidence < 0.7:
        skill = FALLBACK_SKILL  # more capable / general
    else:
        skill = SKILL_REGISTRY[task_type.label]

    result = await skill.execute(task)

    # Post-condition check — mandatory, not optional
    if not skill.verify_postcondition(task, result):
        result = await VERIFICATION_AGENT.recheck(task, result)

    return result
```

### Component 4: Orchestration (𝒪) and Governance (𝒢)

The orchestration loop coordinates all components. Governance gates:
- Intermediate reasoning outputs (before accepting a plan step)
- External action effects (before committing a file write, API call, etc.)
- Memory write-backs (traced and auditable)

**Governance checklist before any external action:**
```
□ Has the relevant memory been re-verified against live state?
□ Does the skill's post-condition check pass?
□ Is there an audit trace for this action?
□ Is rollback available if the action has side effects?
□ Is the permission scope appropriate (principle of least privilege)?
```

## Practical Guidance

### Three Production Harness Comparisons

The paper compares three reference harnesses with similar frontier models but different harness designs:

| Harness | Memory | Context Governance | Distinctive Design |
|---------|--------|-------------------|-------------------|
| **Claude Code** | Persistent text + auto-extraction | User/project/session layers (CLAUDE.md + JIT tools) | Subagent specialization with per-agent context windows and permissions |
| **OpenClaw** | Conversation history + vector retrieval | User/channel/session | Multi-channel gateway (Discord, Slack, iMessage) |
| **CheetahClaws** | Structured entries with explicit confidence + recency fields | User/project/session | Transparency-first; confidence/recency as first-class queryable fields |

**Key insight:** Similar frontier models yield radically different agents based on harness design alone.

### Temporal Lever Framework

Three levers operating at different timescales:

| Lever | Timescale | Primary Role | Failure Mode |
|-------|-----------|--------------|--------------|
| **Prompt** | Local/immediate | Specify goal, constraints, style | Brittle over long horizons; poor transfer |
| **Skill** | Task-level | Reusable procedure or workflow | Wrong routing; poor composition |
| **Memory** | Longitudinal | Preserve durable facts, experience | Drift, over-generalization, pollution |

Design all three levers together. Prompt tuning without memory governance leads to tasks succeeding in isolation but failing across sessions.

### Multi-Agent Performance Data

From Anthropic research cited in the paper:
- Multi-agent (Opus 4 lead + Sonnet 4 subagents) outperformed single-agent Opus 4 by **90.2%** on internal research tasks
- **Token usage explained 80%** of performance variance; adding tool-call count and model choice raised it to **95%**
- Breadth-first tasks show strongest gains through parallel context windows

**Multi-agent failure modes to design against:**
- Decomposition is easier than collaboration
- Inter-agent misalignment (no shared state)
- Inadequate task verification between agents
- Missing: uncertainty communication, contradiction detection, task de-duplication, conflict resolution

## Examples

**Example: Diagnosing a failing agent with the harness framework**

```text
Agent symptom: Confidently deletes files based on outdated assumptions.

Diagnosis checklist:
  ℳ Memory: Was the file-existence assumption re-verified before action?
             → NO. Stale-but-confident failure.
  𝒞 Context: Was the file listing freshly retrieved (JIT) or from a stale index?
              → STALE INDEX. Exposure-without-access failure.
  𝒮 Skills: Did the delete skill have a post-condition check?
             → NO. Confident-but-unchecked failure.
  𝒢 Governance: Was rollback available for the delete action?
                 → NO.

Fix:
  ℳ: Add staleness check — re-verify file existence via tool call before destructive action
  𝒞: Replace static file index with JIT glob/ls tool call
  𝒮: Add post-condition: verify file is gone after delete AND previous state was as expected
  𝒢: Require user confirmation for irreversible actions OR implement soft-delete
```

**Example: Harness design review checklist**

```markdown
## Harness Review: [System Name]

### ℳ Memory
- [ ] Confidence and recency tracked as first-class fields?
- [ ] Retrieval ranking penalizes staleness?
- [ ] Retrieved content treated as hypothesis until re-verified?
- [ ] Periodic re-verification against live environment?

### 𝒞 Context
- [ ] Context assembled by selection policy (not fixed buffer)?
- [ ] Persistent priors + JIT retrieval + live search (three layers)?
- [ ] Every token has source provenance?
- [ ] Token budget enforced with relevance ranking?

### 𝒮 Skill Routing
- [ ] Each skill has documented capability scope?
- [ ] Post-condition checks defined per skill?
- [ ] Confidence-aware escalation to more capable models?
- [ ] Composition verification between chained skills?

### 𝒢 Governance
- [ ] Audit trace for memory writes?
- [ ] Audit trace for routing decisions?
- [ ] Audit trace for tool permissions?
- [ ] Rollback available for side-effecting actions?
```

## Guidelines

1. **Design all six components together** — a strong ℛ model with weak ℳ/𝒞/𝒮/𝒢 produces unreliable agents
2. **Make memory trust a runtime decision** — retrieved content is a hypothesis until re-verified against live environment
3. **Assemble context as a selection policy** — weight semantic relevance + compactness + recency
4. **Couple every skill invocation with a post-condition check** — fluent output ≠ correct output
5. **Scale 𝒮 (skills) and 𝒢 (governance) together** — adding capabilities without governance adds speed but reduces reliability
6. **Use three context layers** — persistent priors (loaded upfront) + JIT retrieval + live environment search
7. **Propagate provenance** — every token in context should have a traceable source and timestamp
8. **Design for audit** — inspectable traces for memory writes, routing changes, tool permissions, agent failures

## Gotchas

1. **Model upgrades masking system problems** — a stronger model can paper over a bad harness temporarily, until edge cases expose the underlying failure. Audit the harness, don't just upgrade the model.
2. **Stale-but-confident is silent** — outdated memory entries that remain highly ranked via semantic similarity are the most dangerous failure: the agent acts with high confidence on wrong assumptions. Add explicit staleness penalties.
3. **Context exposure ≠ context access** — longer context windows do not improve retrieval; they dilute signal. Treat context as output of a ranking policy, not a dump buffer.
4. **Governance debt** — adding skills/tools without corresponding governance (audit traces, rollback, permission scoping) creates compounding risk. Each new capability needs a governance counterpart.
5. **Pass-k collapse** — agents that score well on single-shot benchmarks collapse under repeated rollouts (pass^k). Design for consistency, not just peak performance.
6. **Decomposition ≠ collaboration** — multi-agent systems easily decompose tasks but struggle to collaborate (shared state, uncertainty communication, contradiction detection). Decomposition is a solved problem; collaboration is not.
7. **Reward hacking in longitudinal evaluation** — optimizing for benchmark proxy metrics instead of actual task quality. Track regression and earlier-failure recurrence alongside rolling success rates.

## Integration

This skill provides the architectural foundation for:
- [memory-systems](../../context-engineering/memory-systems/SKILL.md) — implements ℳ in depth
- [multi-agent-patterns](../multi-agent-patterns/SKILL.md) — implements 𝒪 coordination patterns
- [context-fundamentals](../../context-engineering/context-fundamentals/SKILL.md) — implements 𝒞 in depth
- [agentic-eval](../../agent-eval/agentic-eval/SKILL.md) — measures harness quality

## References

Internal references:
- [Six-Component Architecture](./references/six-component-architecture.md) — detailed breakdown of ℛ, ℳ, 𝒞, 𝒮, 𝒪, 𝒢 with sub-axes and implementation patterns
- [Context Governance Patterns](./references/context-governance.md) — context selection policies, JIT refresh, provenance tracking
- [Trustworthy Memory Design](./references/trustworthy-memory.md) — confidence/staleness fields, verification loops, conflict resolution
- [Skill Routing & Verification](./references/skill-routing-verification.md) — adaptive routing policies, post-condition specs, escalation
- [Safe Agent Evolution](./references/safe-agent-evolution.md) — the four-pillar maturity framework: persist, update, measure, audit

External resources:
- [Paper: arXiv:2605.26112v1](https://arxiv.org/abs/2605.26112v1) — primary source
- [CheetahClaws reference implementation](https://github.com/SafeRL-Lab/cheetahclaws) — Python harness with explicit trust axes
- [SWE-bench](https://swe-bench.github.io/) — coding agent benchmark showing interface design matters as much as models
- [τ-bench](https://github.com/sierra-research/tau-bench) — pass^k evaluation for agent reliability across repeated rollouts

---

## Skill Metadata

**Created**: 2026-05-26
**Source Paper**: arXiv:2605.26112v1 — Shangding Gu, UC Berkeley
**Version**: 1.0.0
