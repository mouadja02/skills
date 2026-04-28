# engineering-craft

The **disciplined engineering loop** — planning, TDD, code review, debugging, verification, and parallelism. These are the workflow skills the agent should reach for whenever real code is being written or shipped.

Many of these skills come from the *Superpowers* methodology. The entry point is `using-superpowers` — read it first when starting any non-trivial conversation.

## Skills in this category

### Planning & execution

| Skill | What it does |
| --- | --- |
| [`using-superpowers`](./using-superpowers/SKILL.md) | The conversation entry point. Establishes how to discover and use skills before responding. |
| [`brainstorming`](./brainstorming/SKILL.md) | Mandatory creative-work primer. Explores user intent, requirements, and design *before* implementation. |
| [`grill-me`](./grill-me/SKILL.md) | Stress-test a plan or design through relentless interview-style questioning until shared understanding is reached. |
| [`writing-plans`](./writing-plans/SKILL.md) | Turn a spec or set of requirements into a written implementation plan before touching code. |
| [`executing-plans`](./executing-plans/SKILL.md) | Execute a written implementation plan in a fresh session with review checkpoints. |
| [`subagent-driven-development`](./subagent-driven-development/SKILL.md) | Execute implementation plans by dispatching independent tasks to subagents in the current session. |
| [`dispatching-parallel-agents`](./dispatching-parallel-agents/SKILL.md) | Pattern for splitting 2+ truly independent tasks across parallel agents (no shared state, no sequential deps). |

### Quality, testing, and verification

| Skill | What it does |
| --- | --- |
| [`test-driven-development`](./test-driven-development/SKILL.md) | Write the test first, watch it fail, write minimal code, refactor. Use before any feature or bugfix. |
| [`systematic-debugging`](./systematic-debugging/SKILL.md) | Diagnose any bug, test failure, or unexpected behavior *before* proposing a fix. |
| [`verification-before-completion`](./verification-before-completion/SKILL.md) | Run verification commands and confirm output before claiming work is "done", "fixed", or "passing". Evidence before assertions. |
| [`karpathy-guidlines`](./karpathy-guidlines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes — surgical changes, surfaced assumptions, verifiable success criteria. |

### Code review

| Skill | What it does |
| --- | --- |
| [`requesting-code-review`](./requesting-code-review/SKILL.md) | Trigger code review when finishing a task, implementing a major feature, or before merging. |
| [`receiving-code-review`](./receiving-code-review/SKILL.md) | Handle review feedback with technical rigor — verify claims, push back on weak ones, never agree performatively. |

### Branch & PR workflow

| Skill | What it does |
| --- | --- |
| [`using-git-worktrees`](./using-git-worktrees/SKILL.md) | Create isolated git worktrees for feature work or plan execution, with smart directory selection and safety checks. |
| [`finishing-a-development-branch`](./finishing-a-development-branch/SKILL.md) | When all tests pass and you need to integrate the work — choose between merge, PR, or cleanup. |

### Evaluation

| Skill | What it does |
| --- | --- |
| [`evaluation`](./evaluation/SKILL.md) | Build evaluation frameworks — LLM-as-judge, multi-dimensional rubrics, quality gates for agent pipelines. The foundational evaluation skill. |
| [`advanced-evaluation`](./advanced-evaluation/SKILL.md) | Production-grade patterns layered on `evaluation` — direct scoring vs pairwise comparison, position/length/self-enhancement bias mitigation, metric-selection framework, pipeline architecture. |

### Senior IC roles

| Skill | What it does |
| --- | --- |
| [`senior-architect`](./senior-architect/SKILL.md) | System architecture — microservices vs monolith, architecture diagrams, dependency analysis, database choice, scalability and reliability plans. |
| [`senior-frontend`](./senior-frontend/SKILL.md) | React, Next.js, TypeScript, Tailwind — components, performance, bundle analysis, frontend scaffolding. |
| [`senior-backend`](./senior-backend/SKILL.md) | REST APIs, microservices, database architectures, authentication flows, security hardening. |
| [`senior-fullstack`](./senior-fullstack/SKILL.md) | Fullstack scaffolding (Next.js, FastAPI, MERN, Django) plus security/complexity scoring and stack-selection guidance. |
| [`senior-ml-engineer`](./senior-ml-engineer/SKILL.md) | Productionizing ML, MLOps pipelines, model deployment, feature stores, drift monitoring, RAG systems, cost optimization. |
| [`senior-data-engineer`](./senior-data-engineer/SKILL.md) | Data pipelines, ETL/ELT, modern data stack — Python, SQL, Spark, Airflow, dbt, Kafka. Data modeling and pipeline ops. |
| [`senior-data-scientist`](./senior-data-scientist/SKILL.md) | Statistical modeling, experiment design, causal inference, predictive analytics — A/B sample sizing, two-proportion z-tests, lift estimation. |
| [`senior-qa`](./senior-qa/SKILL.md) | Generate Jest + React Testing Library unit tests, integration tests, and E2E tests for React/Next.js — coverage analysis with Istanbul/LCOV. |
| [`senior-pm`](./senior-pm/SKILL.md) | Senior project manager for enterprise software — portfolio management, quantitative risk analysis, resource optimization, stakeholder alignment. |

### Engineering analytics

| Skill | What it does |
| --- | --- |
| [`codebase-onboarding`](./codebase-onboarding/SKILL.md) | Generate onboarding docs for an unfamiliar codebase — architecture overviews, key-file maps, local setup, quick wins for new developers. |
| [`tech-debt-tracker`](./tech-debt-tracker/SKILL.md) | Scan codebases for technical debt, score severity, track trends, generate prioritized remediation plans. |
| [`tech-stack-evaluator`](./tech-stack-evaluator/SKILL.md) | Compare frameworks and stacks — TCO analysis, security assessment, ecosystem health scoring. |

## Suggested workflow

```
brainstorming  →  writing-plans  →  using-git-worktrees  →
  test-driven-development  →  systematic-debugging (if broken)  →
    verification-before-completion  →  requesting-code-review  →
      receiving-code-review  →  finishing-a-development-branch
```

## Related categories

- [`skill-authoring/`](../skill-authoring/) — for the skill files themselves.
- [`ai-agents/bmm-skills/`](../ai-agents/bmm-skills/) — BMad Method, an end-to-end agile framework that overlaps but is heavier weight.
- [`product-management/`](../product-management/) — `senior-pm` lives here for IC-on-engineering-side framing; `agile-product-owner` and `scrum-master` live there for the product-management framing.
