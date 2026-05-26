# Safe Agent Evolution Standards

From arXiv:2605.26112v1 — Shangding Gu, UC Berkeley, May 2026.

As agentic systems accumulate experience and update themselves — learning new skills, refining memories, adjusting routing policies — they face a class of problems that traditional ML evaluation misses. This reference encodes the **four-pillar maturity framework** for governing how an agent evolves over time.

---

## Why Agent Evolution Is Dangerous

Unlike static software, agentic systems may:
- Update their memory stores with new facts (sometimes wrong ones)
- Acquire new skills or modify existing routing policies
- Change tool permissions through self-modification
- Accumulate behavioral drift across sessions without any single "update" event

**The compounding risk:** Early errors become training signal. Slightly wrong memory entries become more confidently wrong over time. A routing policy optimized for one distribution of tasks may degrade silently when the task distribution shifts.

**The steeper risk:** Behavioral evaluation alone is insufficient for persistent threats like:
- **Sleeper agents** — behaviors only triggered by specific conditions
- **Training-resistant deception** — agents that game evaluation while maintaining covert behaviors
- **Reward hacking** — agents optimizing proxy metrics instead of true objectives

---

## The Four-Pillar Framework

### Pillar 1: What Persists?

**Question:** Which components of the agent are allowed to change across sessions, and which are immutable?

**Governance:**
```
Component         | Persistence Policy         | Change Mechanism
──────────────────┬────────────────────────────┬─────────────────────
Foundation model  | Immutable per deployment   | Explicit upgrade/rollback
Memory store      | Mutable with versioning    | Confidence-gated writes
Skills/tools      | Versioned, audited         | Reviewed PRs + replay tests
User preferences  | Mutable, user-controlled   | User commands only
Guardrails        | Immutable except by review | Manual approval required
Routing policies  | Versioned, auditable       | A/B tested before deploying
Tool permissions  | Immutable except by review | Manual approval required
```

**Implementation — prevent silent component rewrites:**
```python
class AgentComponentRegistry:
    IMMUTABLE_COMPONENTS = {"foundation_model", "guardrails", "tool_permissions"}
    VERSIONED_COMPONENTS = {"memory", "skills", "routing_policy"}
    MUTABLE_COMPONENTS = {"user_preferences", "session_state"}

    def update_component(self, component_name: str, update: ComponentUpdate) -> bool:
        if component_name in self.IMMUTABLE_COMPONENTS:
            raise ImmutableComponentError(
                f"Component '{component_name}' requires manual review and approval to change"
            )
        if component_name in self.VERSIONED_COMPONENTS:
            # Create versioned snapshot before updating
            self.snapshot(component_name)
            self.audit_log.record_update(component_name, update)
        return self._apply_update(component_name, update)
```

---

### Pillar 2: What Updates?

**Question:** Which updates can happen automatically (online learning), and which require human review?

**Online adaptation allowed (low risk):**
- Adding new memory entries from tool call observations
- Adjusting routing confidence scores from observed outcomes
- Compressing and consolidating memory (without altering facts)
- Updating cached context indices

**Review required (high risk):**
- Adding new tools or changing tool permissions
- Modifying guardrail logic
- Changing governance boundaries
- Updating routing policies for production systems
- Any change that affects what external actions the agent can take

```python
class UpdateGovernor:
    ONLINE_ALLOWED = {
        "memory.add_entry",
        "memory.refresh_verification",
        "routing.update_confidence_score",
        "context.refresh_index",
    }
    REVIEW_REQUIRED = {
        "tools.add_permission",
        "tools.remove_permission",
        "guardrails.modify",
        "routing.change_policy",
        "skills.add",
        "skills.modify",
    }

    def approve(self, update_type: str, update: dict) -> ApprovalResult:
        if update_type in self.ONLINE_ALLOWED:
            return ApprovalResult(approved=True, mode="automatic")

        if update_type in self.REVIEW_REQUIRED:
            review_id = self.create_review_request(update_type, update)
            return ApprovalResult(
                approved=False,
                mode="pending_review",
                review_id=review_id,
                message=f"Update type '{update_type}' requires human review. Review ID: {review_id}"
            )

        return ApprovalResult(approved=False, mode="unknown_type",
                             message=f"Unknown update type: {update_type}")
```

---

### Pillar 3: What Is Measured?

**Question:** How do you know if the agent is improving, degrading, or drifting?

The paper identifies three failure modes in longitudinal measurement:

1. **Success rate obsession** — optimizing rolling success rate while missing regressions on earlier tasks
2. **Reward hacking** — agent learns to pass evals without actually improving at the real objective
3. **Distribution shift blindness** — metrics look fine because the task distribution changed, not because performance improved

**Required longitudinal metrics:**

| Metric | What It Measures | Why It's Necessary |
|--------|----------------|-------------------|
| **Memory retrieval precision** | % retrieved memories that are accurate | Detects stale-but-confident drift |
| **Memory hygiene under reuse** | Quality of entries after N retrieval cycles | Detects confidence inflation |
| **Minimal-context efficiency** | Ratio of useful/total tokens in context | Detects context bloat |
| **Communication fidelity** | Accuracy of cross-agent information transfer | Detects telephone-game degradation |
| **Drift across long trajectories** | Performance delta between session start and end | Detects within-session degradation |
| **Verification-aware recovery** | Success rate of actions after stale memory detected | Measures verification loop quality |
| **Earlier-failure recurrence** | Rate of previously-fixed bugs re-appearing | Catches regressions |
| **pass^k reliability** | Success rate across K independent rollouts | Reveals consistency vs. lucky-shot performance |

```python
class LongitudinalEvaluator:
    def measure_pass_k(self, task: Task, k: int = 10) -> float:
        """
        Run the task K times independently. Report pass^k.
        pass^k = fraction of runs where ALL attempts in a set of k succeed.
        Distinguishes consistent agents from lucky-shot agents.
        """
        results = [self.run_once(task) for _ in range(k)]
        return sum(1 for r in results if r.success) / k

    def measure_drift(self, agent: Agent, task_suite: list[Task]) -> DriftReport:
        """
        Measure agent performance at session start vs. end.
        Detects context accumulation degradation.
        """
        start_scores = [self.evaluate(agent, t, reset_context=True) for t in task_suite]

        # Simulate a long session — fill context with unrelated work
        agent.run_long_session(NOISE_TASKS, n=50)

        end_scores = [self.evaluate(agent, t, reset_context=False) for t in task_suite]

        drift = [(s - e) for s, e in zip(start_scores, end_scores)]
        return DriftReport(
            avg_drift=sum(drift) / len(drift),
            max_drift=max(drift),
            tasks_degraded=[task_suite[i] for i, d in enumerate(drift) if d > 0.1]
        )

    def detect_reward_hacking(self, agent: Agent, eval_suite: EvalSuite) -> bool:
        """
        Check if agent scores improve on eval tasks but not on held-out equivalents.
        A large gap suggests reward hacking.
        """
        eval_score = self.evaluate_on(agent, eval_suite.eval_tasks)
        held_out_score = self.evaluate_on(agent, eval_suite.held_out_tasks)

        gap = eval_score - held_out_score
        if gap > 0.15:  # 15% gap suggests gaming
            logging.warning(
                f"Potential reward hacking detected: eval={eval_score:.2f}, "
                f"held_out={held_out_score:.2f}, gap={gap:.2f}"
            )
            return True
        return False
```

---

### Pillar 4: What Is Auditable?

**Question:** For any behavior the agent exhibits, can you trace exactly why it happened?

**Required audit surfaces:**

```python
class AgentAuditSystem:
    """
    Creates inspectable traces for all agent state changes.
    Enables post-hoc attribution of any behavior.
    """

    def log_memory_write(self, entry: MemoryEntry, triggered_by: str):
        self.audit_log.append(AuditEntry(
            type="memory_write",
            timestamp=datetime.utcnow(),
            entry_id=entry.id,
            content_hash=hash(entry.content),
            confidence=entry.confidence,
            source=entry.source,
            triggered_by=triggered_by,  # Which action caused this write
        ))

    def log_routing_change(self, old_policy: RoutingPolicy, new_policy: RoutingPolicy, reason: str):
        self.audit_log.append(AuditEntry(
            type="routing_change",
            timestamp=datetime.utcnow(),
            policy_diff=compute_diff(old_policy, new_policy),
            reason=reason,
            requires_review=True,
        ))

    def log_tool_permission_change(
        self, agent_id: str, permission: str, action: str, approved_by: str
    ):
        self.audit_log.append(AuditEntry(
            type="permission_change",
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            permission=permission,
            action=action,  # "grant" | "revoke"
            approved_by=approved_by,
        ))

    def log_collaboration_failure(
        self, agent_a: str, agent_b: str, failure_type: str, context: dict
    ):
        self.audit_log.append(AuditEntry(
            type="collaboration_failure",
            timestamp=datetime.utcnow(),
            agents=[agent_a, agent_b],
            failure_type=failure_type,  # "misalignment" | "contradiction" | "de-sync"
            context=context,
        ))

    def explain_behavior(self, behavior_id: str) -> BehaviorExplanation:
        """
        Given a behavior ID, trace back the chain of decisions that caused it.
        """
        behavior = self.audit_log.get_behavior(behavior_id)
        chain = []

        # Walk backwards through audit log
        current = behavior
        while current is not None:
            chain.append(current)
            current = self.audit_log.get_cause(current)

        return BehaviorExplanation(
            behavior_id=behavior_id,
            causal_chain=chain,
            root_cause=chain[-1] if chain else None,
        )
```

**Why behavioral evaluation alone is insufficient:**
> "Behavioral evaluation alone [is] insufficient for persistent risks (sleeper agents, training-resistant deception)."
> — arXiv:2605.26112v1, Section 5.3

Audit traces provide the alternative: even if behavior looks correct during evaluation, traces show whether the *process* was sound.

---

## Evolution Maturity Levels

Use this maturity model to assess and improve an agent system's evolution safety:

| Level | What's True | Risks |
|-------|------------|-------|
| **0 — Uncontrolled** | Agent updates itself freely; no audit | Silent drift, stale memory, reward hacking |
| **1 — Logged** | All state changes logged but not reviewed | Drift detected after the fact; no prevention |
| **2 — Versioned** | Components versioned; rollback available | Can recover; still no proactive governance |
| **3 — Governed** | Online vs. review-required split; human approval for high-risk changes | Slow for low-risk changes; requires review process |
| **4 — Measured** | Longitudinal metrics tracked; drift detected before user impact | Requires evaluation infrastructure; pass^k testing |
| **5 — Auditable** | Full causal trace for any behavior; sleeper agent detection feasible | High storage/compute cost; requires trace tooling |

**Target for production agents: Level 4 minimum; Level 5 for high-stakes deployments.**

---

## Quick Checklist: Is Your Agent Evolving Safely?

```markdown
## Safe Evolution Checklist

### Pillar 1: What Persists?
- [ ] Foundation model version pinned per deployment?
- [ ] Guardrail logic immutable except by reviewed PR?
- [ ] Tool permissions require explicit human approval to change?
- [ ] Memory store versioned with rollback capability?

### Pillar 2: What Updates?
- [ ] Online-allowed updates enumerated and enforced programmatically?
- [ ] Review-required updates trigger a blocking review queue?
- [ ] Any permission-scope-expanding update requires review?

### Pillar 3: What Is Measured?
- [ ] pass^k tracked (not just pass@1)?
- [ ] Earlier-failure recurrence rate tracked?
- [ ] Memory hygiene measured over time (not just at eval time)?
- [ ] Held-out task suite separate from eval suite?
- [ ] Long-session drift measured?

### Pillar 4: What Is Auditable?
- [ ] Every memory write has a causal trace?
- [ ] Every routing decision logged with confidence and outcome?
- [ ] Every tool permission change logged with approver?
- [ ] Collaboration failures between agents logged?
- [ ] Audit traces retained for at least 90 days?
```
