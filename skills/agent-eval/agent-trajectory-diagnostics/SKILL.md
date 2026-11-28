---
name: agent-trajectory-diagnostics
description: >
  Use when diagnosing agent benchmarks or runtime failures from trajectories instead of aggregate
  pass rates. Builds shared action-observation decision landscapes, identifies productive cores and
  trap regions, profiles Access/Trap/Repair behavior, and designs conservative trap-triggered recovery
  experiments.
source: "https://arxiv.org/abs/2605.31308"
attribution: "Derived from TraceGraph: Shared Decision Landscapes for Diagnosing and Improving Agent Trajectories (arXiv:2605.31308)"
version: "1.1.0"
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
- Auditing which intended tool, capability, and failure-case behaviors a selected trace corpus actually measures

## Paper-Backed Vocabulary

| Event | Meaning |
| --- | --- |
| Access | Trajectory reaches a productive core |
| Trap exposure | Trajectory enters a low-outcome region |
| Repair | Trajectory enters a trap and later reaches a productive core |

Trap regions are descriptive, not universal proof of a bad action. Some traps contain legitimate exploration.

## Workflow

### Step 1: Freeze the Diagnostic Contract

Before reading outcomes, define a finite denominator of intended behavior. Give every item a stable ID, a
kind (`tool`, `capability`, or `failure_case`), its source requirement, and the evidence needed to count it as
covered. For failure cases, state both the trigger evidence and the expected safe response; a trace that never
contains the trigger cannot prove the failure behavior.

Keep the denominator versioned and reviewable. Do not silently add items after seeing weak results. If it
changes, create a new denominator revision and do not aggregate measurements across revisions.

### Step 2: Select and Bind Comparable Trajectories

Capture:
- Task ID
- Run or attempt ID
- Outcome or reward
- Ordered actions
- Tool calls
- Environment observations
- File, URL, command, or entity cues
- Model and harness identity
- Evidence class: agent under test, reference solution, no-op, or control

Write a selection manifest before measurement. Record included and excluded paths, selection rules, task/run
IDs, evidence class, trace format, and the SHA-256 digest of each exact trace. Bind manual or model-authored
judgments to the trace digest and the denominator digest. A changed trace, denominator, or judgment is stale
evidence and must be remeasured rather than silently reused.

Pool comparable rollouts across models or harness variants before adding model identity to the analysis. Keep
reference, no-op, and control traces separate from agent-under-test coverage totals.

### Step 3: Canonicalize Observable States

Create sparse action-observation signatures:

```yaml
action: edit|read|search|execute|delegate
tool: tool-name
observation: success|error|timeout|empty|conflict
resource: normalized-path-or-entity
phase: optional-workflow-phase
```

Strip volatile identifiers. Keep enough structure to recognize recurring contexts.

### Step 4: Build the Shared Landscape

1. Create a similarity graph over pooled observable states.
2. Group densely related states.
3. Identify articulation gates where trajectories branch between phases or strategies.
4. Overlay outcome information only after graph construction.
5. Mark productive cores and low-outcome trap regions.

Model identity should be traffic over the shared landscape, not an input to landscape construction.

### Step 5: Measure Coverage and Process Behavior

Measure each denominator item against the selected corpus before interpreting the landscape:

- **Covered:** selected evidence satisfies every required predicate for the item.
- **Uncovered:** the relevant trigger or opportunity was measured, but required behavior was absent or failed.
- **Unmeasured:** no selected trace exercises the item or its trigger; this is not a failure.
- **Stale:** evidence is bound to different trace, denominator, or judgment bytes.
- **Unproven:** the trace is suggestive, but the required evidence or verifier control is insufficient.

Report tool, capability, and failure-case coverage separately. Reconcile verifier evidence with observable trace
and environment evidence; a passing verifier does not override contradictory state or tool-call evidence.

Then, for each model or harness:
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

### Step 6: Validate the Landscape and Coverage

Manually inspect samples:
- Within-region state pairs should be more similar than cross-region pairs.
- Articulation gates should often correspond to strategy or phase changes.
- Productive cores should be enriched for progress.
- Trap regions should be enriched for loops, dead ends, or low-outcome transitions.
- Covered items should have evidence locators in selected traces.
- Uncovered items should name the failed predicate, while unmeasured items should name the missing scenario.
- Reference/control evidence should not inflate agent-under-test coverage.
- Recompute a sample from exact bytes and confirm all recorded digests still match.

### Step 7: Test Conservative Recovery

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
[Selection rules, tasks, runs, evidence classes, models, harnesses, trace digests]

## Intended-Behavior Denominator
[Revision/digest, source requirements, stable tool/capability/failure-case IDs]

## Coverage Audit
[Covered, uncovered, unmeasured, stale, and unproven items by evidence class, with trace locators]

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
7. Freeze the denominator and trace selection before measurement.
8. Bind judgments to exact trace and denominator bytes.
9. Never combine unmeasured items with measured failures.

## Gotchas

1. **Scalar-score tunnel vision** - Equal pass rates can hide different failure and recovery modes.
2. **Outcome leakage** - Do not construct the state graph from model identity or labels.
3. **Trap absolutism** - Low-outcome regions may include useful exploration.
4. **Global repair policies** - Trigger recovery only where historical evidence supports it.
5. **Over-specific signatures** - Volatile IDs prevent matching recurring states.
6. **Over-general signatures** - Removing too much structure creates noisy triggers.
7. **Coverage by task count** - Many tasks can repeatedly exercise the same behavior while leaving others unmeasured.
8. **Control leakage** - Reference solutions and no-op/control traces are evidence checks, not agent-under-test coverage.
9. **Digest-free judgments** - A judgment detached from exact trace bytes cannot be safely reused after artifacts change.
10. **Verifier absolutism** - A verifier pass is one evidence class; reconcile it with tool, output, and state evidence.

## Reference

- [TraceGraph: Shared Decision Landscapes for Diagnosing and Improving Agent Trajectories](https://arxiv.org/abs/2605.31308)
- [NVIDIA NeMo Eval Author audit workflow](https://github.com/NVIDIA-NeMo/eval-author/tree/0f618435ad2ccd4592182069e59fe61047e45ee4/skills/eval-author-audit)
- [Turning agent failures into tests and harness fixes](https://developer.nvidia.com/blog/use-nvidia-nemo-to-turn-agent-failures-into-tests-and-harness-fixes)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.1.0
