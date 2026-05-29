# coding

A **practitioner's toolkit for writing, reviewing, shipping, and maintaining code** — from idea clarification through launch and beyond. These skills govern the disciplined development loop: specification, planning, testing, quality, debugging, security, and workflow.

Use this category when the task is *writing or improving code* rather than building agent systems, managing infrastructure, or advising the C-suite.

## Skills in this category

### Discovery & clarification

| Skill | What it does |
| --- | --- |
| [`using-agent-skills`](./using-agent-skills/SKILL.md) | Discovers and invokes agent skills. The meta-skill that governs how all other skills are found and loaded. Start here at the beginning of any session. |
| [`interview-me`](./interview-me/SKILL.md) | Extracts what the user actually wants through one-question-at-a-time interviewing until ~95% confidence. Use when an ask is underspecified before writing any plan or code. |
| [`idea-refine`](./idea-refine/SKILL.md) | Refines raw ideas into sharp, actionable concepts through structured divergent and convergent thinking. Use when an idea is still vague or assumptions need stress-testing before committing to a plan. |

### Specification & planning

| Skill | What it does |
| --- | --- |
| [`spec-driven-development`](./spec-driven-development/SKILL.md) | Creates a spec before coding. Use when starting any new project, feature, or significant change where no specification exists yet. |
| [`planning-and-task-breakdown`](./planning-and-task-breakdown/SKILL.md) | Breaks work into ordered, implementable tasks. Use when a task feels too large to start, when scope needs estimating, or when parallel work is possible. |
| [`api-and-interface-design`](./api-and-interface-design/SKILL.md) | Guides stable API and interface design. Use when designing REST or GraphQL endpoints, module boundaries, type contracts between modules, or frontend/backend interfaces. |

### Development disciplines

| Skill | What it does |
| --- | --- |
| [`test-driven-development`](./test-driven-development/SKILL.md) | Drives development with tests. Use when implementing any logic, fixing any bug, or changing any behavior — write the test first, then make it pass. |
| [`source-driven-development`](./source-driven-development/SKILL.md) | Grounds every implementation decision in official documentation. Use when correctness matters and you want authoritative, source-cited code free from outdated patterns. |
| [`spec-driven-development`](./spec-driven-development/SKILL.md) | Creates specs before coding. Use when starting a new project or feature and no specification exists yet. |
| [`doubt-driven-development`](./doubt-driven-development/SKILL.md) | Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when correctness matters more than speed, in security-sensitive or irreversible operations. |
| [`incremental-implementation`](./incremental-implementation/SKILL.md) | Delivers changes incrementally. Use when a task touches more than one file — land it in small, reviewable steps rather than one big commit. |
| [`karpathy-guidelines`](./karpathy-guidelines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes — surgical changes, surfaced assumptions, verifiable success criteria, and avoiding over-engineering. |
| [`nasa-inspired-coding-rules`](./nasa-inspired-coding-rules/SKILL.md) | Cross-language reliability rules generalized from NASA Glenn programming guidelines — explicit contracts, resource safety, portability, and production-like verification. |
| [`context-engineering`](./context-engineering/SKILL.md) | Optimizes agent context setup. Use when starting a new session, when output quality degrades, when switching tasks, or when configuring rules files and context for a project. |

### Code quality

| Skill | What it does |
| --- | --- |
| [`code-review-and-quality`](./code-review-and-quality/SKILL.md) | Conducts multi-axis code review. Use before merging any change — reviews code across multiple quality dimensions. |
| [`code-simplification`](./code-simplification/SKILL.md) | Simplifies code for clarity without changing behavior. Use when code works but is harder to read, maintain, or extend than it should be. |
| [`security-and-hardening`](./security-and-hardening/SKILL.md) | Hardens code against vulnerabilities. Use when handling user input, authentication, data storage, or external integrations. |
| [`performance-optimization`](./performance-optimization/SKILL.md) | Optimizes application performance. Use when Core Web Vitals or load times need improvement, or when profiling reveals bottlenecks. |
| [`documentation-and-adrs`](./documentation-and-adrs/SKILL.md) | Records architectural decisions and documentation. Use when making architectural changes, modifying public APIs, or shipping features that future engineers and agents will need to understand. |

### Debugging & testing

| Skill | What it does |
| --- | --- |
| [`debugging-and-error-recovery`](./debugging-and-error-recovery/SKILL.md) | Guides systematic root-cause debugging. Use when tests fail, builds break, or behavior doesn't match expectations — diagnose before proposing a fix. |
| [`browser-testing-with-devtools`](./browser-testing-with-devtools/SKILL.md) | Tests in real browsers via Chrome DevTools MCP. Use when inspecting the DOM, capturing console errors, analyzing network requests, profiling performance, or verifying visual output. Requires the chrome-devtools MCP server. |

### UI & frontend

| Skill | What it does |
| --- | --- |
| [`frontend-ui-engineering`](./frontend-ui-engineering/SKILL.md) | Builds production-quality UIs. Use when creating components, implementing layouts, managing state, or when the output needs to look and feel production-quality rather than AI-generated. |

### Workflow & Git

| Skill | What it does |
| --- | --- |
| [`git-workflow-and-versioning`](./git-workflow-and-versioning/SKILL.md) | Structures git workflow practices. Use when committing, branching, resolving conflicts, or organizing work across multiple parallel streams. |
| [`ci-cd-and-automation`](./ci-cd-and-automation/SKILL.md) | Automates CI/CD pipeline setup. Use when setting up or modifying build and deployment pipelines, configuring quality gates, or establishing deployment strategies. |
| [`shipping-and-launch`](./shipping-and-launch/SKILL.md) | Prepares production launches. Use when deploying to production — pre-launch checklists, monitoring setup, staged rollout planning, and rollback strategies. |

### Maintenance & migration

| Skill | What it does |
| --- | --- |
| [`deprecation-and-migration`](./deprecation-and-migration/SKILL.md) | Manages deprecation and migration. Use when removing old systems, APIs, or features, or migrating users from one implementation to another. |

### iOS/macOS — Swift & Instruments _(from steipete/agent-scripts)_

| Skill | What it does |
| --- | --- |
| `swift-concurrency-expert` | Swift concurrency review/fix — compiler errors, Sendable, actor isolation, Swift 6.2+. |
| `swiftui-liquid-glass` | SwiftUI Liquid Glass (iOS 26+) — implement, adopt, refactor, review. |
| `swiftui-performance-audit` | SwiftUI performance audit — render, scroll, CPU/memory, view updates, Instruments. |
| `swiftui-view-refactor` | SwiftUI view refactor — layout ordering, DI, Observation, MV patterns. |
| `hopper-debugger` | Hopper Disassembler debugging — macOS/iOS binaries, ObjC/Swift symbols, LLDB. |
| `instruments-profiling` | Instruments/xctrace profiling — macOS/iOS traces, Time Profiler, exports. |
| `native-app-performance` | Native app performance — xctrace CLI, hotspot analysis, no Instruments UI. |

## Suggested workflow

```
interview-me / idea-refine  →  spec-driven-development  →  planning-and-task-breakdown  →
  api-and-interface-design  →  test-driven-development  →  incremental-implementation  →
    code-review-and-quality  →  security-and-hardening  →  debugging-and-error-recovery  →
      git-workflow-and-versioning  →  ci-cd-and-automation  →  shipping-and-launch
```

## When to use this folder

- "Write / implement / refactor X"
- "Review this code before merging"
- "This test is failing" / "debug this error"
- "Design this API / module boundary"
- "Set up CI/CD for this repo"
- "Prepare to deploy to production"
- "Simplify this code" / "remove the complexity"
- "Secure this endpoint / harden this input handler"

## Related categories

- [`engineering-craft/`](../engineering-craft/) — overlapping discipline skills scoped to the engineering workflow (TDD, code review, brainstorming, senior IC roles, evaluation). Many skills in both categories are complementary.
- [`devops-and-infrastructure/`](../devops-and-infrastructure/) — production infrastructure and deployment (Docker, Helm, Terraform, AWS, security operations).
- [`design-and-ui/`](../design-and-ui/) — visual design, design systems, and creative assets for the frontend layer.
- [`context-engineering/`](../context-engineering/) — context window management and memory systems (broader than the `context-engineering` coding skill here, which focuses on rules files and session setup).
