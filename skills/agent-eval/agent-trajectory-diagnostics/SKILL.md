---
name: agent-trajectory-diagnostics
description: >
  Use when diagnosing agent benchmarks or runtime failures from trajectories instead of aggregate
  pass rates. Builds shared action-observation decision landscapes, identifies productive cores and
  trap regions, profiles Access/Trap/Repair behavior, and designs conservative trap-triggered recovery
  experiments.
source: "https://arxiv.org/abs/2605.31308"
attribution: "Derived from TraceGraph: Shared Decision Landscapes for Diagnosing and Improving Agent Trajectories (arXiv:2605.31308)"
---

# Agent Trajectory Diagnostics

Pass rate hides how an agent navigates. Use shared decision landscapes to identify where agents reach
productive states, enter recurring failure regions, and recover.

## When to Activate

Activate when:
- Aggregate agent scores do not explain failures
- Comparing agent models or harnesses on the same task suite
- Looking for recurring loops, dead ends, invalid tool choices, or repair behavior
- Building a conservative runtime recovery trigger from historical trajectories
- Auditing whether a benchmark rewards avoidance, exploration, or recovery

## Paper-Backed Vocabulary

| Event | Meaning |
| --- | --- |
| Access | Trajectory reaches a productive core |
| Trap exposure | Trajectory enters a low-outcome region |
| Repair | Trajectory enters a trap and later reaches a productive core |

Trap regions are descriptive, not universal proof of a bad action. Some traps contain legitimate exploration.

## Workflow

### Step 1: Collect Comparable Trajectories

Capture:
- Task ID
- Outcome or reward
- Ordered actions
- Tool calls
- Environment observations
- File, URL, command, or entity cues
- Model and harness identity

Pool rollouts across models or harness variants before adding model identity to the analysis.

### Step 2: Canonicalize Observable States

Create sparse action-observation signatures:

```yaml
action: edit|read|search|execute|delegate
tool: tool-name
observation: success|error|timeout|empty|conflict
resource: normalized-path-or-entity
phase: optional-workflow-phase
```

Strip volatile identifiers. Keep enough structure to recognize recurring contexts.

### Step 3: Build the Shared Landscape

1. Create a similarity graph over pooled observable states.
2. Group densely related states.
3. Identify articulation gates where trajectories branch between phases or strategies.
4. Overlay outcome information only after graph construction.
5. Mark productive cores and low-outcome trap regions.

Model identity should be traffic over the shared landscape, not an input to landscape construction.

### Step 4: Profile Supply and Demand

For each model or harness:
- Access rate
- Trap-exposure rate
- Repair rate
- Time to access
- Time spent in traps
- Repeated trap loops

For each benchmark:
- Does success mostly require reaching productive states?
- Does success require avoiding traps?
- Does success require repairing after traps?

### Step 5: Validate the Landscape

Manually inspect samples:
- Within-region state pairs should be more similar than cross-region pairs.
- Articulation gates should often correspond to strategy or phase changes.
- Productive cores should be enriched for progress.
- Trap regions should be enriched for loops, dead ends, or low-outcome transitions.

### Step 6: Test Conservative Recovery

When historical traps are repeatable:

1. Run the live agent normally.
2. Detect a canonical state matching a historical trap region.
3. Fork from the same prefix.
4. Compare small single-factor interventions such as a diagnosis note, increased sampling diversity, or a
   provider-specific continuation policy.
5. Promote only an intervention that improves paired outcomes on fired states.

Do not apply recovery globally without evidence.

## Output Format

```markdown
## Trajectory Corpus
[Tasks, rollouts, models, harnesses]

## Shared Landscape
[State signature, graph construction, cores, traps, gates]

## Process Profiles
[Access, Trap, Repair by model and benchmark]

## Failure Regions
[Recurring states and examples]

## Recovery Experiment
[Trigger, prefix fork, treatment arms, paired results]

## Limits
[Where signatures or interventions may not generalize]
```

## Guidelines

1. Build shared landscapes before overlaying model identity.
2. Keep runtime triggers observable and conservative.
3. Test recovery on the same fired prefixes.
4. Report paired outcome changes, not anecdotes.
5. Preserve trap false positives for review.
6. Treat process profiles as diagnostics, not a replacement leaderboard.

## Gotchas

1. **Scalar-score tunnel vision** - Equal pass rates can hide different failure and recovery modes.
2. **Outcome leakage** - Do not construct the state graph from model identity or labels.
3. **Trap absolutism** - Low-outcome regions may include useful exploration.
4. **Global repair policies** - Trigger recovery only where historical evidence supports it.
5. **Over-specific signatures** - Volatile IDs prevent matching recurring states.
6. **Over-general signatures** - Removing too much structure creates noisy triggers.

## Reference

- [TraceGraph: Shared Decision Landscapes for Diagnosing and Improving Agent Trajectories](https://arxiv.org/abs/2605.31308)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.0.0
