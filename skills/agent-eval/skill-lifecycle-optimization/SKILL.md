---
name: skill-lifecycle-optimization
description: >
  Use when improving, evolving, benchmarking, or maintaining agent skills over time. Treats skills
  as long-lived structured artifacts: execute tasks, diagnose trajectory evidence, accumulate textual
  momentum, patch at the correct abstraction layer, test per model and harness, canary changes, and
  roll back regressions.
source: "https://arxiv.org/abs/2605.27760; https://arxiv.org/abs/2605.27366; https://arxiv.org/abs/2605.30723; https://arxiv.org/abs/2605.30621; https://arxiv.org/abs/2605.31408; https://arxiv.org/abs/2605.23657"
attribution: "Derived from SkillGrad, MUSE-Autoskill, MASA, Harness Updating Is Not Harness Benefit, SkillsBench granularity study, and OpenSkillEval"
---

# Skill Lifecycle Optimization

Treat each skill as a versioned, testable artifact that can improve or regress. Optimize from execution
evidence, not from stylistic preference.

## When to Activate

Activate when:
- A skill exists but is unreliable, incomplete, stale, or model-sensitive
- Maintaining a growing skill library
- Evaluating third-party or generated skills before deployment
- Designing a self-evolving agent harness
- Deciding whether a skill rewrite actually improved task performance

## Paper-Backed Principles

1. **Availability matters more reliably than presentation granularity.** A controlled SkillsBench study found
   a clear benefit from access to task-relevant skills, while tested abstraction-level and example-format
   rewrites had smaller, uncertain, model-dependent effects.
2. **Skills can be optimized as structured parameters.** SkillGrad uses trajectory loss evidence, textual
   diagnoses, momentum, and layer-aware patches.
3. **Skills need a lifecycle.** MUSE-Autoskill emphasizes creation, memory, management, evaluation, and
   refinement with unit tests and runtime feedback.
4. **Skill effectiveness is model-dependent.** MASA reports that a skill that helps one backbone can harm
   another.
5. **Updating and benefiting are separate capabilities.** Harness evolution research distinguishes an
   evolver's ability to write a useful update from an executor's ability to load and follow it.
6. **Popularity is not quality.** OpenSkillEval reports that public skills do not consistently outperform
   no-skill agents and should be evaluated dynamically under realistic tasks.

## Lifecycle State

Maintain:

```yaml
skill_id: example
version: 1.2.0
source: curated|generated|third-party
compatible_models: []
compatible_harnesses: []
evaluation_suite: path-or-id
last_evaluated_at: ISO-8601
repair_count: 0
regression_count: 0
known_failure_modes: []
rollback_target: 1.1.0
```

## Optimization Loop

### Step 1: Pin the Evaluation Surface

Define:
- Training tasks for update evidence
- Construction-time verification tasks
- Held-out tasks
- Models and harnesses under test
- Fixed executor configuration
- Deterministic postconditions
- Budget for iterations, tokens, and tool calls

Do not optimize against the held-out suite.

### Step 2: Run the Current Skill

Capture:
- Task outcome
- Tool calls and environment observations
- Loaded skill sections
- Skill activation success or failure
- Whether instructions were followed faithfully
- Postcondition results
- Latency and token cost

Separate two executor failures:

| Failure | Meaning |
| --- | --- |
| Activation failure | Relevant skill was not loaded |
| Adherence failure | Skill loaded, but the executor did not follow it |

### Step 3: Produce Textual Gradients

For each task:

```markdown
## Diagnosis
- Task:
- Outcome:
- Failure or success signal:
- Missing, weak, ignored, or preserved guidance:
- Reusable mechanism:
- Suggested layer:
- Evidence:
```

Use both:
- Failed trajectories for repair evidence
- Contrastive successes for behaviors worth preserving

### Step 4: Update Textual Momentum

Maintain `momentum_memory.md`:

```markdown
## Pattern: [stable-slug]
- status: new|recurring|unresolved|absorbed
- evidence:
- affected skill sections:
- reusable rule:
- remedy log:
```

Momentum reduces churn. Consolidate recurring semantic directions instead of reacting to the latest task
in isolation.

### Step 5: Patch by Abstraction Layer

Patch patterns, not individual examples.

| Layer | Contents |
| --- | --- |
| `SKILL.md` | concise always-loaded routing and core procedure |
| `references/*.md` | conditional edge cases, long procedures, examples, domain specifics |
| `scripts/` | executable helpers where deterministic automation is appropriate |

Prefer small targeted edits. Do not continuously expand the always-loaded file.

### Step 6: Evaluate Net Effect

Report per model and harness:
- Baseline pass rate
- Candidate pass rate
- Repairs
- Regressions
- Activation rate
- Harness-following rate
- Runtime and token cost
- Cross-model transfer
- Performance with no skill

Canary new versions before promotion. Roll back when regressions exceed the defined budget.

### Step 7: Allocate Capability Wisely

Do not automatically spend the strongest model on skill evolution. Test whether a cheaper evolver produces
equivalent reusable procedures. Allocate strong-model budget to the task-solving executor when executor
activation or adherence is the bottleneck.

## Output Format

```markdown
## Skill Baseline
[Version, source, models, harnesses, evaluation suite]

## Trajectory Evidence
[Failures, contrastive successes, activation and adherence failures]

## Textual Momentum
[Recurring patterns and status]

## Patch Plan
[Layer-aware targeted edits]

## Net-Effect Report
[Repairs, regressions, held-out results, cost, per-model behavior]

## Promotion Decision
[Promote, canary, revise, or rollback]
```

## Guidelines

1. Keep evaluation configurations pinned.
2. Compare against no-skill behavior.
3. Evaluate each target model and harness separately.
4. Measure activation and adherence.
5. Preserve contrastive success patterns.
6. Keep rollback available for every promoted change.
7. Prefer execution-based verification over document similarity.

## Gotchas

1. **Formatting theater** - Rewriting abstraction level or adding examples is not automatically an improvement.
2. **Model-agnostic assumptions** - A useful skill can harm another backbone.
3. **Latest-batch overfitting** - Without textual momentum, patches chase local incidents.
4. **Append-only bloat** - Put conditional material in references.
5. **Strong-evolver waste** - Executor capability may be the real bottleneck.
6. **Popularity bias** - Community usage is not a substitute for controlled evaluation.

## References

- [SkillGrad: Optimizing Agent Skills Like Gradient Descent](https://arxiv.org/abs/2605.27760)
- [MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation](https://arxiv.org/abs/2605.27366)
- [Skill is Not One-Size-Fits-All: Model-Aware Skill Alignment for LLM Agents](https://arxiv.org/abs/2605.30723)
- [Harness Updating Is Not Harness Benefit](https://arxiv.org/abs/2605.30621)
- [Skill Availability and Presentation Granularity in LLM Agents](https://arxiv.org/abs/2605.31408)
- [OpenSkillEval](https://arxiv.org/abs/2605.23657)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.0.0
