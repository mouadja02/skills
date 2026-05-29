---
name: harness-benchmarking
description: >
  Use when designing evaluation suites for agentic systems, choosing agent benchmarks,
  measuring multi-agent performance, or critiquing single-score evaluation of agents.
  Based on arXiv:2605.26112v1. Trigger phrases: "evaluate my agent", "benchmark agent",
  "measure agent reliability", "pass^k evaluation", "agent metrics beyond success rate",
  "trajectory quality", "memory hygiene metric", "longitudinal agent eval", "why my agent
  scores well on benchmarks but fails in production".
source: "https://arxiv.org/abs/2605.26112v1"
attribution: "Shangding Gu, UC Berkeley — 'From Model Scaling to System Scaling: Scaling the Harness in Agentic AI' (arXiv:2605.26112v1, May 2026)"
---

> **Attribution:** Derived from [arXiv:2605.26112v1](https://arxiv.org/abs/2605.26112v1) — *From Model Scaling to System Scaling: Scaling the Harness in Agentic AI* by Shangding Gu (UC Berkeley), May 2026.

# Harness-Level Agent Benchmarking

Current agentic benchmarks (SWE-bench, AgentBench, WebArena, Terminal-Bench) measure single-score endpoint success. This obscures whether performance gains come from stronger models or better harness design, and fails to capture the systemic qualities that determine production reliability.

This skill encodes the move from **outcome metrics** to **process metrics** and from **single-episode evaluation** to **longitudinal evaluation**.

## When to Activate

Activate this skill when:
- Designing an evaluation suite for an agentic system
- Choosing which benchmarks to run and how to interpret results
- Agents perform well in benchmarks but fail in production
- Comparing two agent systems and wanting a fair comparison
- Measuring whether a harness improvement actually helped
- Evaluating memory quality, context efficiency, or routing accuracy
- Building multi-agent evaluation setups
- Understanding the pass^k vs. pass@1 distinction

## Core Concepts

### The Single-Score Problem

Single endpoint success rate is necessary but insufficient for agentic evaluation:

```
What single-score HIDES:
  - Did the agent succeed via a reliable process or a lucky path?
  - Did it use 10K tokens or 500K tokens?
  - Did it verify its own work or just produce output?
  - Would it succeed again on a different rollout?
  - Did memory drift contribute to the failure?

What single-score SHOWS:
  - Whether the final output is correct (once)
```

**Field finding (Kapoor et al., 2024):** Agent results often conflate capability with costs, prompting quality, and demonstrations. Many published results are non-Pareto-optimal when controlled for these factors.

### Pass^k: The Reliability Metric

Pass@1 = "did the agent succeed on this one attempt?" — the default benchmark.

Pass^k = "did the agent succeed on all k independent rollouts?" — the production-reliability metric.

```
Agent A: pass@1 = 0.90, pass^10 = 0.35  ← High peak, low consistency
Agent B: pass@1 = 0.75, pass^10 = 0.65  ← Lower peak, high consistency

Production verdict: Agent B is more reliable despite lower benchmark score.
```

**τ-bench finding:** Agents strong under single-shot pass rates collapse under pass^k — revealing that apparent capability was partly luck, not reliability.

### Process Metrics

| Metric Category | Specific Metrics | Why It Matters |
|----------------|----------------|----------------|
| **Token efficiency** | Tokens/task, useful-tokens ratio | High token use ≠ better performance |
| **Tool use** | Tool calls/task, tool failure rate | Reveals skill routing quality |
| **Memory quality** | Retrieval precision, memory hygiene over time | Detects stale-but-confident failure |
| **Context quality** | Context efficiency, provenance coverage | Detects noise loading and attention dilution |
| **Trajectory quality** | Steps to completion, backtrack rate | Reveals planning quality |
| **Verification** | Post-condition pass rate, verification cost | Reveals confident-but-unchecked risk |
| **Communication** | Cross-agent fidelity (in multi-agent) | Detects telephone-game degradation |
| **Safety** | Irreversible action rate, permission escalation rate | Governance quality |

## Detailed Topics

### Tier 1: Minimum Viable Evaluation

Start with these three metrics beyond pass@1:

```python
class MinimumViableEval:
    def evaluate(self, agent: Agent, task_suite: list[Task]) -> MVEReport:
        results = []
        for task in task_suite:
            run = agent.run(task)
            results.append({
                "task_id": task.id,
                # Tier 1 must-haves:
                "success": run.succeeded,
                "token_count": run.total_tokens,
                "tool_calls": len(run.tool_calls),
                # Pass^k via multiple rollouts
                "pass_k": self.compute_pass_k(agent, task, k=5),
            })

        return MVEReport(
            pass_at_1=sum(r["success"] for r in results) / len(results),
            pass_at_5=sum(r["pass_k"] for r in results) / len(results),
            avg_tokens=sum(r["token_count"] for r in results) / len(results),
            avg_tool_calls=sum(r["tool_calls"] for r in results) / len(results),
        )

    def compute_pass_k(self, agent: Agent, task: Task, k: int) -> float:
        runs = [agent.run(task, seed=i) for i in range(k)]
        return sum(1 for r in runs if r.succeeded) / k
```

### Tier 2: Harness-Level Process Metrics

```python
class HarnessLevelEval:
    def evaluate_memory_quality(self, agent: Agent, tasks: list[Task]) -> MemoryReport:
        """Measure memory quality before and after task execution."""
        before = agent.memory.snapshot()
        results = [agent.run(t) for t in tasks]
        after = agent.memory.snapshot()

        # Memory hygiene: how many entries are still accurate after tasks?
        stale_count = sum(
            1 for entry in after.entries
            if agent.env.verify(entry.content).contradicts(entry)
        )

        return MemoryReport(
            entries_added=len(after.entries) - len(before.entries),
            stale_entries=stale_count,
            hygiene_score=1 - (stale_count / max(1, len(after.entries))),
            retrieval_precision=self.measure_retrieval_precision(agent, tasks),
        )

    def evaluate_context_efficiency(self, agent: Agent, tasks: list[Task]) -> ContextReport:
        """Measure how efficiently agent uses its context budget."""
        runs = [agent.run_with_context_logging(t) for t in tasks]

        efficiency_scores = []
        for run in runs:
            total_tokens = run.context_stats.total_tokens
            useful_tokens = run.context_stats.tokens_actually_referenced
            efficiency_scores.append(useful_tokens / max(1, total_tokens))

        return ContextReport(
            avg_efficiency=sum(efficiency_scores) / len(efficiency_scores),
            avg_total_tokens=sum(r.context_stats.total_tokens for r in runs) / len(runs),
            provenance_coverage=sum(
                r.context_stats.provenance_coverage for r in runs
            ) / len(runs),
        )

    def evaluate_verification_quality(self, agent: Agent, tasks: list[Task]) -> VerificationReport:
        """Measure how well the agent verifies its own outputs."""
        runs = [agent.run_with_verification_logging(t) for t in tasks]

        return VerificationReport(
            postcondition_pass_rate=sum(
                r.verification_stats.all_passed for r in runs
            ) / len(runs),
            avg_verification_cost_tokens=sum(
                r.verification_stats.tokens_spent for r in runs
            ) / len(runs),
            unverified_action_rate=sum(
                r.verification_stats.unverified_actions for r in runs
            ) / sum(r.verification_stats.total_actions for r in runs),
        )
```

### Tier 3: Longitudinal Evaluation

```python
class LongitudinalEval:
    """Evaluate agent stability over time and across sessions."""

    def measure_session_drift(
        self, agent: Agent, task_suite: list[Task], session_length: int = 50
    ) -> DriftReport:
        """
        Measure how agent performance degrades within a single long session.
        Reveals context accumulation problems.
        """
        # Run task suite fresh (no prior context)
        fresh_scores = [agent.evaluate_fresh(t) for t in task_suite]

        # Simulate a long session of unrelated work
        agent.run_filler_session(n_tasks=session_length)

        # Now re-evaluate same tasks with accumulated context
        accumulated_scores = [agent.evaluate_with_history(t) for t in task_suite]

        drift_per_task = [f - a for f, a in zip(fresh_scores, accumulated_scores)]

        return DriftReport(
            avg_drift=sum(drift_per_task) / len(drift_per_task),
            max_drift=max(drift_per_task),
            degraded_tasks=[
                task_suite[i] for i, d in enumerate(drift_per_task) if d > 0.1
            ]
        )

    def measure_cross_session_memory_quality(
        self, agent: Agent, n_sessions: int = 10
    ) -> MemoryDriftReport:
        """
        Measure whether memory quality degrades across repeated sessions.
        Detects stale-but-confident accumulation.
        """
        precision_by_session = []

        for session_num in range(n_sessions):
            # Run a session
            agent.run_session(session_num)

            # Measure retrieval precision
            precision = self.measure_retrieval_precision(agent)
            precision_by_session.append(precision)

        trend = compute_linear_trend(precision_by_session)
        return MemoryDriftReport(
            precision_by_session=precision_by_session,
            trend=trend,  # Negative = degrading over time
            sessions_before_degradation=next(
                (i for i, p in enumerate(precision_by_session) if p < 0.8),
                n_sessions  # No degradation within n_sessions
            )
        )

    def measure_regression_rate(
        self, agent_v1: Agent, agent_v2: Agent, regression_suite: list[Task]
    ) -> RegressionReport:
        """
        Compare two agent versions. Identify tasks v2 FAILS that v1 PASSED.
        Rolling success rate improvements can hide regressions.
        """
        v1_results = {t.id: agent_v1.run(t).succeeded for t in regression_suite}
        v2_results = {t.id: agent_v2.run(t).succeeded for t in regression_suite}

        regressions = [
            t for t in regression_suite
            if v1_results[t.id] and not v2_results[t.id]
        ]
        improvements = [
            t for t in regression_suite
            if not v1_results[t.id] and v2_results[t.id]
        ]

        return RegressionReport(
            v1_pass_rate=sum(v1_results.values()) / len(v1_results),
            v2_pass_rate=sum(v2_results.values()) / len(v2_results),
            regression_count=len(regressions),
            improvement_count=len(improvements),
            net_delta=len(improvements) - len(regressions),
            regressed_tasks=regressions,
        )
```

### Multi-Agent Evaluation

```python
class MultiAgentEval:
    """
    Evaluates multi-agent system performance beyond single-agent metrics.
    Based on Anthropic research finding: token usage explains 80% of variance.
    """

    def evaluate_coordination_quality(
        self, system: MultiAgentSystem, tasks: list[Task]
    ) -> CoordinationReport:
        runs = [system.run(t) for t in tasks]

        return CoordinationReport(
            # Communication fidelity: does info survive agent-to-agent handoffs?
            communication_fidelity=self.measure_fidelity(runs),

            # De-duplication: do agents avoid doing the same work twice?
            deduplication_rate=self.measure_deduplication(runs),

            # Shared state consistency: do agents agree on world state?
            shared_state_consistency=self.measure_state_consistency(runs),

            # Contradiction rate: how often do agents contradict each other?
            contradiction_rate=self.measure_contradictions(runs),

            # Token breakdown: per-agent token distribution
            token_distribution=self.measure_token_distribution(runs),
        )

    def measure_fidelity(self, runs: list[MultiAgentRun]) -> float:
        """Measure information preservation across agent handoffs."""
        fidelity_scores = []
        for run in runs:
            for handoff in run.handoffs:
                # Compare: what agent A sent vs. what agent B received/reported
                sent = handoff.sent_content
                received_and_used = handoff.downstream_references
                score = content_overlap(sent, received_and_used)
                fidelity_scores.append(score)
        return sum(fidelity_scores) / max(1, len(fidelity_scores))
```

## Practical Guidance

### Benchmark Selection Guide

| Benchmark | What It Measures | Limitation | Use When |
|-----------|----------------|------------|---------|
| **SWE-bench** | Coding task success (GitHub issues) | Single-score; doesn't measure process quality | Evaluating coding agents' endpoint capability |
| **AgentBench** | Multi-domain agentic task success | No token efficiency or reliability metrics | Broad capability survey |
| **WebArena** | Web navigation task success | No memory or context metrics | Evaluating web-browsing capability |
| **Terminal-Bench** | Terminal/CLI task success | No longitudinal or multi-session metrics | Evaluating CLI agents |
| **τ-bench** | pass^k reliability across rollouts | Infrastructure-intensive | Measuring production reliability |
| **LoCoMo** | Memory retention over long conversations | Only measures memory, not full harness | Evaluating memory quality specifically |
| **LongMemEval** | Temporal memory accuracy | Evaluates retrieval, not action quality | Memory system benchmarking |

### Pareto-Optimal Evaluation

When comparing two agents, don't just compare pass@1. Check the Pareto frontier:

```
Better agent: higher success AND lower token cost AND higher pass^k
Dominated agent: any agent that can be beaten on all three axes

Plot: token_cost (x) vs. success_rate (y) vs. pass^10 (bubble size)
```

**From the paper (Kapoor et al., 2024):** Many published agent results are non-Pareto-optimal when controlled for token costs, prompting, and demonstrations.

### Interpreting Multi-Agent Results

From Anthropic research (cited in paper):
- Multi-agent outperformed single-agent by **90.2%** on internal research tasks
- **Token usage explained 80%** of this variance
- Adding tool-call count and model choice: **95%** explained
- **Implication:** More tokens ≠ better architecture. Measure token cost alongside success.

```python
def compute_efficiency_adjusted_score(
    success_rate: float, token_cost: int, baseline_tokens: int = 10000
) -> float:
    """
    Adjust success rate by token efficiency.
    Agents spending 10x tokens should be held to higher success standards.
    """
    efficiency = baseline_tokens / max(1, token_cost)
    return success_rate * efficiency
```

## Guidelines

1. **Always report pass^k alongside pass@1** — pass@1 alone is insufficient for production-reliability claims
2. **Report token costs** — a more expensive agent must show proportionally higher quality
3. **Use held-out task suites** separate from eval suites to detect reward hacking
4. **Measure regression rate** when comparing versions — net improvement can hide important regressions
5. **Track longitudinal metrics** — memory hygiene, context efficiency, and drift degrade across sessions
6. **Evaluate multi-agent communication fidelity** explicitly — telephone-game degradation is invisible to endpoint metrics
7. **Use process metrics, not just outcome metrics** — trajectory quality, verification rate, and tool-use patterns reveal harness quality
8. **Interpret benchmark results in context** — understand what each benchmark measures and what it does not

## Gotchas

1. **Single-score overconfidence** — a 90% pass@1 sounds great until pass^10 reveals 35% consistency. Always compute both.
2. **Benchmark overfitting** — agents tuned on benchmark tasks may perform well there but fail on slight variations. Always have held-out tasks.
3. **Token cost invisibility** — publishing pass@1 without token costs allows 10x-more-expensive agents to appear equivalent.
4. **Latency blindness** — token cost and latency are both real constraints in production. Measure wall-clock time, not just token count.
5. **Multi-agent winner's curse** — multi-agent systems often appear better because they use more tokens, not because the architecture is superior. Normalize by token budget.
6. **Session drift invisibility** — agents may score 90% on fresh evaluation but 60% after a long session. Longitudinal evaluation catches this.
7. **Memory quality → behavior gap** — poor memory quality may not appear in next-action accuracy until the agent takes a wrong action based on stale facts. Test memory quality separately from downstream success.

## Integration

This skill complements:
- [harness-scaling](../../agent-design/harness-scaling/SKILL.md) — the framework being evaluated
- [multi-agent-patterns](../../agent-design/multi-agent-patterns/SKILL.md) — multi-agent coordination being measured
- [memory-systems](../../context-engineering/memory-systems/SKILL.md) — memory quality being measured

## References

- [Paper: arXiv:2605.26112v1](https://arxiv.org/abs/2605.26112v1) — primary source for evaluation framework
- [τ-bench](https://github.com/sierra-research/tau-bench) — pass^k evaluation framework for reliability
- [SWE-bench](https://swe-bench.github.io/) — coding agent benchmark
- [Kapoor et al., 2024 — "Are Language Model Benchmarks Reliable?"](https://arxiv.org/abs/2404.01747) — agent benchmark critique
- [LoCoMo benchmark](https://snap-research.github.io/locomo/) — long-conversation memory evaluation
- [LongMemEval](https://arxiv.org/abs/2410.10813) — temporal memory accuracy benchmark

---

## Skill Metadata

**Created**: 2026-05-26
**Source Paper**: arXiv:2605.26112v1 — Shangding Gu, UC Berkeley
**Version**: 1.0.0
