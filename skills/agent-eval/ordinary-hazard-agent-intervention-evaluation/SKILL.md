---
name: ordinary-hazard-agent-intervention-evaluation
description: >-
  Use when a non-adversarial AI agent incident must be reproduced offline and an intervention tested causally. Builds matched hazard/no-hazard worlds, state-based harm oracles, neutral and informative warning conditions, repeated trials, and a deployment decision packet.
version: "1.0.0"
license: MIT
source: "https://arxiv.org/abs/2611.26553v1; https://arxiv.org/abs/2605.30777v3; https://arxiv.org/abs/2606.01317v2; https://arxiv.org/abs/2605.19149v2"
attribution: "Original workflow derived from ROGUE-AI, SABER, operational coding-agent incident research, and Agent Meltdowns"
---

# Ordinary-Hazard Agent Intervention Evaluation

Turn a reported agent incident into an isolated, repeatable causal experiment. The output is an **intervention decision packet**, not a claim that prompt wording alone makes an agent safe.

## When to Use

- A benign task caused harm because the agent missed an ordinary environmental hazard.
- A team needs to reproduce an incident without touching production.
- A warning, tool-output annotation, policy, or structural control needs matched evaluation.
- Harm can be determined from final environment state.

Do **not** activate during ongoing harm: contain the agent, preserve evidence, and recover through the incident-response process first. Do not use this workflow to build exploit payloads, recreate sensitive production data, or run untrusted downloaded incident code.

## Prerequisites

- A source-linked incident report and authority to use its evidence.
- An isolated disposable environment with synthetic or redacted data.
- A reset mechanism that restores the same starting state before every trial.
- A deterministic state inspection that can identify harm without asking the agent.
- Frozen model, agent, tools, decoding, timeouts, and trial budget.

## Workflow

### 1. Write the claim card

Use [the claim-card template](templates/claim-card.md). Separate:

- directly sourced facts;
- the report's proposed cause;
- evaluator assumptions;
- unknowns that the experiment cannot resolve.

Define the harmful final state and the decision the evaluation will support. A report is a lead, not proof of mechanism.

### 2. Build the incident world and matched control

Create two offline worlds from one fixture:

- **Incident world:** contains the suspected ordinary hazard.
- **No-hazard control:** differs only by removal of that hazard.

Keep task text, names, permissions, data volume, tool responses, latency, and reset state identical unless one is the tested hazard. Record every allowed leaf-level difference. Run:

```bash
python3 scripts/validate_scenario_pair.py scenario-pair.json
```

The validator checks structural minimal difference; it does not prove semantic equivalence. Review the full fixture diff manually. See [design checklist](references/design-checklist.md).

### 3. Prove reachability before agent trials

Use deterministic scripted policies to prove both directions:

1. the normal task path can reach the hazard in the incident world;
2. the same path does not produce harm in the control;
3. the harm oracle fires on a known-harm state;
4. it stays clear on a known-safe state;
5. reset returns both worlds to the frozen baseline.

A scenario that cannot satisfy these checks is not ready for model evaluation.

### 4. Define a state-based harm oracle

Compute harm from persistent environment state: database rows, resource existence, permissions, balances, published artifacts, or another task-specific invariant. Agent text, exit status, and self-reported success may be observations but cannot be the oracle.

Freeze the oracle before trials. Include false-positive and false-negative fixtures. Keep the oracle independent of treatment labels and model output wording.

### 5. Freeze matched intervention conditions

At minimum compare:

1. **Baseline:** original observation.
2. **Equal-length neutral:** same placement and approximate length, no hazard information.
3. **Fact-only:** names the relevant environmental fact without its consequence.
4. **Hazard plus consequence:** names both the hazard and resulting harm.
5. **Structural remediation:** removes or blocks the hazardous path without relying on model attention.

Keep permissions and capabilities unchanged across text-only conditions. If a treatment changes authority, tool schemas, or world state, classify it as structural rather than textual.

### 6. Run repeated matched trials

Randomize condition order and use independent sessions. Reset and verify state before every run. Pair trials by scenario and seed where supported. Record:

- model/agent/tool versions and decoding settings;
- condition, seed, exit reason, actions, and final oracle result;
- incomplete or censored runs separately from safe runs;
- latency, token/tool cost, and intervention overhead.

Stop on contamination, failed reset, oracle disagreement, unexpected network access, or evidence that a trial touched a non-disposable target.

### 7. Analyze causally and conservatively

For each condition report completed trials, harm rate, paired difference from baseline, uncertainty interval, refusal/abstention rate, and cost. Slice only prespecified factors. Do not claim causality when worlds differ beyond the hazard, treatments change capabilities unexpectedly, or the oracle depends on agent narration.

Prefer structural remediation when it is feasible and effective. Treat warning text as defense in depth, not as authorization to leave a preventable hazard in place.

### 8. Produce the decision packet

Use [the decision-packet template](templates/decision-packet.md). Include source traceability, fixture hashes, pair validation, reachability evidence, frozen conditions, trial accounting, uncertainty, costs, limitations, and a deploy/revise/reject decision with rollback criteria.

## Completion Gate

Complete only when:

- incident and control worlds pass deterministic reachability and reset checks;
- the only documented world differences are the suspected hazard;
- the harm oracle reads final state and passes positive/negative fixtures;
- all five conditions use frozen, reviewable payloads;
- repeated matched trials account for every run;
- the recommendation reports uncertainty and does not overrule structural controls.

## Related Skills

- `incident-commander` for active containment and recovery.
- `agentic-eval` for general output-quality evaluation.
- `stateful-agent-security-monitoring` for adversarial or cross-context monitoring rather than ordinary-hazard replication.

## Sources

- [ROGUE-AI: Replication of Agentic Security Events](https://arxiv.org/abs/2611.26553v1)
- [ROGUE-AI research artifact](https://rogue-ai.surge.sh/)
- [What Breaks When LLMs Code?](https://arxiv.org/abs/2605.30777v3)
- [SABER](https://arxiv.org/abs/2606.01317v2)
- [Agent Meltdowns](https://arxiv.org/abs/2605.19149v2)
