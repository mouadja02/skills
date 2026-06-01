---
name: expert-trace-skill-distillation
description: >
  Use when turning expert materials, execution traces, repository evidence, or long-form documents
  into an inspectable, correctable, and empirically verified agent skill. Covers source governance,
  capability-vs-behavior separation, contrastive induction from successes and failures, intervention
  testing, versioning, rollback, and task-conditioned vs. reusable-library evaluation.
source: "https://arxiv.org/abs/2605.31264; https://arxiv.org/abs/2605.10999; https://arxiv.org/abs/2605.18693"
attribution: "Derived from COLLEAGUE.SKILL (arXiv:2605.31264), SkillGen (arXiv:2605.10999), and SkillGenBench (arXiv:2605.18693)"
---

# Expert Trace Skill Distillation

Build skills from evidence, not from a single unconstrained generation pass. The output must be an
inspectable software artifact whose sources, boundaries, evaluation results, corrections, and rollback
points remain visible.

## When to Activate

Activate when:
- Distilling a teammate's procedures, review standards, or decision heuristics into a skill
- Generating a skill from successful and failed agent trajectories
- Turning a repository, manual, API specification, or research paper into reusable procedures
- Creating a role-grounded skill without open-ended impersonation
- Evaluating whether a generated skill actually helps instead of merely sounding plausible

## Paper-Backed Principles

The cited papers support these principles:

1. **Skills are interventions.** Compare the same tasks with and without the candidate skill.
2. **Failures and successes both matter.** Contrast nearby successful and failed trajectories to isolate
   missing checks, reusable procedures, and regression risks.
3. **Capability and behavior are separate tracks.** Encode work practices separately from bounded style
   or interaction rules.
4. **Skill generation is a pipeline-level problem.** Evaluate the generator, backbone, source type,
   executor, and verifier together.
5. **Repository-grounded and document-grounded extraction are different.** Repositories hide operational
   knowledge across code, config, and scripts. Documents often state rules explicitly but distribute them
   across sections.
6. **Task-conditioned and task-agnostic generation are different regimes.** A focused skill generated
   after a task is known is easier than a reusable library generated before downstream tasks are visible.

## Workflow

### Step 1: Define the Distillation Contract

Record:

```markdown
## Distillation Contract
- Target capability:
- Intended users and agent hosts:
- In-scope source materials:
- Out-of-scope materials:
- Source rights and consent:
- Private-by-default artifacts:
- Allowed behavior constraints:
- Explicitly prohibited identity claims:
- Evaluation tasks:
- Rollback owner:
```

Do not claim to recreate a person. Distill selected procedures, mental models, and bounded interaction
preferences into a correctable package.

### Step 2: Collect and Normalize Evidence

Use only authorized materials. Typical sources:
- Work documents, runbooks, code review comments, incident notes, and design records
- Repository files, scripts, configuration, tests, and command history
- Manuals, API docs, specifications, and research papers
- Successful and failed agent trajectories with tool calls and environment observations

For each item, record provenance:

```yaml
source_id: source-001
uri: path-or-url
source_type: repository|document|trajectory|human-feedback
rights: private|internal|public
captured_at: ISO-8601
scope: capability|bounded-behavior|both
notes: why this evidence is relevant
```

### Step 3: Run Dual Distillation

Generate two inspectable tracks:

| Track | Include | Exclude |
| --- | --- | --- |
| Capability | workflows, standards, review criteria, heuristics, recovery patterns | unsupported claims, generic filler |
| Bounded behavior | communication posture, interaction rules, correction history, explicit limits | identity substitution, invented motives |

Keep behavior optional. A capability-only variant should remain usable.

### Step 4: Run Contrastive Trajectory Induction

When trajectories exist:

1. Group comparable attempts by task.
2. Identify baseline failures and nearby successes.
3. Extract procedures present in successes but missing from failures.
4. Extract recurring failure modes and checks that would catch them.
5. Produce candidate rules at the pattern level, not as task-specific anecdotes.

```markdown
## Contrastive Pattern
- Task family:
- Failure signature:
- Nearby success:
- Missing behavior:
- Candidate reusable rule:
- Verification check:
- Evidence IDs:
```

### Step 5: Render the Skill Package

Minimum package:

```text
skill-name/
  SKILL.md
  references/
    capability.md
    behavior-boundaries.md
    evidence-ledger.md
    correction-log.md
    evaluation-report.md
```

`SKILL.md` should stay compact and route to references through progressive disclosure.

### Step 6: Verify as an Intervention

Evaluate the same task instances with and without the skill:

| Outcome | Meaning |
| --- | --- |
| Baseline fail -> skill pass | Repair |
| Baseline pass -> skill fail | Regression |
| Both pass | Preserved success |
| Both fail | No improvement |

Report:
- Net success delta
- Repair count
- Regression count
- Held-out performance
- Cross-model transfer
- Task-conditioned vs. task-agnostic performance
- Repository-grounded vs. document-grounded performance
- Artifact completeness and provenance coverage

Use deterministic execution checks where possible. Use judges only when deterministic checks cannot
represent valid outputs.

### Step 7: Correct, Version, and Roll Back

Treat feedback as a patch:

```markdown
## Correction Record
- Version:
- Trigger:
- Evidence:
- Track changed: capability|bounded-behavior
- Sections patched:
- Expected improvement:
- Regression suite:
- Rollback target:
```

Every correction must create a new version and preserve the previous artifact.

## Output Format

```markdown
## Source Boundary
[Authorized evidence and exclusions]

## Extracted Tracks
[Capability and optional bounded behavior]

## Contrastive Patterns
[Success/failure-derived reusable rules]

## Generated Package
[Files and entrypoints]

## Intervention Evaluation
[Repairs, regressions, held-out results, provenance coverage]

## Lifecycle
[Version, correction history, rollback path]
```

## Guidelines

1. Require provenance for every extracted rule.
2. Keep capability and behavior separately inspectable.
3. Test generated skills against hidden or held-out tasks.
4. Prefer deterministic execution checks.
5. Measure regressions, not only repaired failures.
6. Keep task-conditioned and reusable-library claims separate.
7. Default sensitive source materials and generated artifacts to local/private storage.

## Gotchas

1. **Single-pass summarization** - A summary is not an operational skill.
2. **Identity replacement** - A role-grounded artifact must not claim to reproduce a person.
3. **No baseline** - Without a no-skill comparison, the net effect is unknown.
4. **Task leakage** - Do not expose verifier internals, hidden tests, or held-out tasks to the generator.
5. **Append-only corrections** - Patch reusable patterns at the right abstraction level instead of accumulating
   contradictory notes.
6. **Repository blindness** - Read config, scripts, and tests; procedures are rarely contained in one README.

## References

- [COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Distillation](https://arxiv.org/abs/2605.31264)
- [SkillGen: Verified Inference-Time Agent Skill Synthesis](https://arxiv.org/abs/2605.10999)
- [SkillGenBench: Benchmarking Skill Generation Pipelines for LLM Agents](https://arxiv.org/abs/2605.18693)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.0.0
