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
| [`framework-nextjs-expert`](./framework-nextjs-expert/SKILL.md) | Comprehensive guidelines and best practices for developing with Next.js App Router, React, TypeScript, Tailwind, and Shadcn UI. |
| [`framework-fastapi-expert`](./framework-fastapi-expert/SKILL.md) | Comprehensive guidelines and best practices for developing scalable APIs with Python, FastAPI, Pydantic, and SQLAlchemy. |
| [`framework-vue-nuxt-expert`](./framework-vue-nuxt-expert/SKILL.md) | Comprehensive guidelines and best practices for developing with Vue 3, Nuxt 3, TypeScript, and TailwindCSS using the Composition API. |
| [`framework-flutter-expert`](./framework-flutter-expert/SKILL.md) | Comprehensive guidelines and best practices for developing mobile applications with Flutter, Dart, and the BLoC state management pattern. |
| [`framework-react-native-expert`](./framework-react-native-expert/SKILL.md) | Comprehensive guidelines and best practices for developing cross-platform applications using React Native and Expo. |

### Engineering analytics

| Skill | What it does |
| --- | --- |
| [`codebase-onboarding`](./codebase-onboarding/SKILL.md) | Generate onboarding docs for an unfamiliar codebase — architecture overviews, key-file maps, local setup, quick wins for new developers. |
| [`tech-debt-tracker`](./tech-debt-tracker/SKILL.md) | Scan codebases for technical debt, score severity, track trends, generate prioritized remediation plans. |
| [`tech-stack-evaluator`](./tech-stack-evaluator/SKILL.md) | Compare frameworks and stacks — TCO analysis, security assessment, ecosystem health scoring. |

### Code migration

| Skill | What it does |
| --- | --- |
| [`ai-code-migrator`](./ai-code-migrator/SKILL.md) | AI-assisted codebase migration at scale — framework upgrades (React class→hooks, Vue 2→3, Next.js 13→15), language conversions (JS→TS, CommonJS→ESM), dependency swaps (Webpack→Vite). 6-phase workflow: analyze → plan → transform → validate → review → ship. |

### Git & version control

| Skill | What it does |
| --- | --- |
| [`conventional-commit`](./conventional-commit/SKILL.md) | Generate conventional commit messages following the Conventional Commits specification. |
| [`commit-message-storyteller`](./commit-message-storyteller/SKILL.md) | Write expressive, narrative commit messages that tell the story of a change. |
| [`git-commit`](./git-commit/SKILL.md) | Execute git commits with intelligent staging, type/scope detection, and conventional messages. |
| [`git-flow-branch-creator`](./git-flow-branch-creator/SKILL.md) | Create correctly-named Git Flow branches for features, releases, and hotfixes. |
| [`gh-cli`](./gh-cli/SKILL.md) | Use the GitHub CLI (`gh`) for issues, PRs, releases, and repository management. |
| [`github-issues`](./github-issues/SKILL.md) | Create, triage, and manage GitHub issues effectively. |
| [`github-release`](./github-release/SKILL.md) | Release a new library version end-to-end with SemVer and Keep a Changelog formatting. |

### Code quality & review

| Skill | What it does |
| --- | --- |
| [`audit-integrity`](./audit-integrity/SKILL.md) | Audit codebase integrity — dead code, circular dependencies, unused exports. |
| [`code-tour`](./code-tour/SKILL.md) | Generate guided code tours for unfamiliar codebases with annotated walkthroughs. |
| [`codeql`](./codeql/SKILL.md) | Write and run CodeQL queries to find security vulnerabilities in code. |
| [`diagnose`](./diagnose/SKILL.md) | Diagnose bugs, errors, and unexpected behavior with systematic root-cause analysis. |
| [`doublecheck`](./doublecheck/SKILL.md) | Verify assumptions and double-check logic before committing to an approach. |
| [`editorconfig`](./editorconfig/SKILL.md) | Create and maintain `.editorconfig` files for consistent code style across editors. |
| [`eyeball`](./eyeball/SKILL.md) | Quickly eyeball code for obvious bugs, style issues, and anti-patterns. |
| [`quality-playbook`](./quality-playbook/SKILL.md) | Establish and enforce quality standards across a project with automated checks. |
| [`refactor`](./refactor/SKILL.md) | Refactor code for readability, maintainability, and performance. |
| [`refactor-method-complexity-reduce`](./refactor-method-complexity-reduce/SKILL.md) | Reduce cyclomatic complexity by extracting methods and simplifying control flow. |
| [`refactor-plan`](./refactor-plan/SKILL.md) | Create a phased refactoring plan with risk assessment and rollback strategy. |
| [`review-and-refactor`](./review-and-refactor/SKILL.md) | Combined review + refactor pass for legacy code or unfamiliar codebases. |
| [`security-review`](./security-review/SKILL.md) | AI-powered security scanner — injection flaws, secrets exposure, CVEs, access control across JS/TS/Python/Java/Go/Ruby/Rust. |
| [`write-coding-standards-from-file`](./write-coding-standards-from-file/SKILL.md) | Extract and formalize coding standards from existing code files. |

### Testing & QA

| Skill | What it does |
| --- | --- |
| [`add-educational-comments`](./add-educational-comments/SKILL.md) | Add educational inline comments that explain non-obvious logic for junior developers. |
| [`automate-this`](./automate-this/SKILL.md) | Identify and automate repetitive manual tasks in a codebase or workflow. |
| [`javascript-typescript-jest`](./javascript-typescript-jest/SKILL.md) | Write Jest unit and integration tests for JavaScript/TypeScript projects. |
| [`playwright-automation-fill-in-form`](./playwright-automation-fill-in-form/SKILL.md) | Automate form filling with Playwright — field detection, validation, submission. |
| [`playwright-explore-website`](./playwright-explore-website/SKILL.md) | Explore and map a website using Playwright automation. |
| [`playwright-generate-test`](./playwright-generate-test/SKILL.md) | Generate Playwright E2E test suites from user stories or page analysis. |
| [`polyglot-test-agent`](./polyglot-test-agent/SKILL.md) | Write tests across multiple languages in a polyglot monorepo. |
| [`pytest-coverage`](./pytest-coverage/SKILL.md) | Write pytest tests with coverage reporting — fixtures, parametrize, mocking. |
| [`resemble-detect`](./resemble-detect/SKILL.md) | Detect visual regressions in UI screenshots using ResembleJS. |
| [`roundup`](./roundup/SKILL.md) | Aggregate and summarize test results, code review feedback, and CI output. |
| [`roundup-setup`](./roundup-setup/SKILL.md) | Set up the Roundup test aggregation and summary toolchain. |
| [`scoutqa-test`](./scoutqa-test/SKILL.md) | Generate QA test plans and exploratory testing checklists. |
| [`shuffle-json-data`](./shuffle-json-data/SKILL.md) | Shuffle, randomize, and anonymize JSON test data. |
| [`unit-test-vue-pinia`](./unit-test-vue-pinia/SKILL.md) | Write unit tests for Vue 3 components with Pinia state management. |
| [`webapp-testing`](./webapp-testing/SKILL.md) | End-to-end testing strategy for web applications — accessibility, performance, cross-browser. |

### .NET / C# ecosystem

| Skill | What it does |
| --- | --- |
| [`csharp-async`](./csharp-async/SKILL.md) | Async/await best practices, Task patterns, cancellation tokens, and deadlock prevention in C#. |
| [`csharp-docs`](./csharp-docs/SKILL.md) | Generate XML documentation comments for C# code. |
| [`csharp-mstest`](./csharp-mstest/SKILL.md) | Write MSTest unit tests for C# projects. |
| [`csharp-nunit`](./csharp-nunit/SKILL.md) | Write NUnit tests for C# projects. |
| [`csharp-tunit`](./csharp-tunit/SKILL.md) | Write TUnit tests for C# projects. |
| [`csharp-xunit`](./csharp-xunit/SKILL.md) | Write xUnit tests for C# projects. |
| [`dotnet-best-practices`](./dotnet-best-practices/SKILL.md) | .NET coding standards, design patterns, performance, and security best practices. |
| [`dotnet-design-pattern-review`](./dotnet-design-pattern-review/SKILL.md) | Review .NET code for appropriate use of design patterns. |
| [`dotnet-mcp-builder`](./dotnet-mcp-builder/SKILL.md) | Build MCP servers using the .NET SDK. |
| [`dotnet-timezone`](./dotnet-timezone/SKILL.md) | Handle time zones correctly in .NET applications with DateTimeOffset and TimeZoneInfo. |
| [`dotnet-upgrade`](./dotnet-upgrade/SKILL.md) | Upgrade .NET projects to newer target frameworks with migration guidance. |
| [`ef-core`](./ef-core/SKILL.md) | Entity Framework Core — migrations, queries, relationships, performance optimization. |
| [`mvvm-toolkit`](./mvvm-toolkit/SKILL.md) | CommunityToolkit.Mvvm — ObservableProperty, RelayCommand, ObservableObject for WPF/WinUI/MAUI/Uno. |
| [`mvvm-toolkit-di`](./mvvm-toolkit-di/SKILL.md) | Dependency injection wiring with CommunityToolkit.Mvvm and Microsoft.Extensions.DI. |
| [`mvvm-toolkit-messenger`](./mvvm-toolkit-messenger/SKILL.md) | Pub/sub messaging between ViewModels using CommunityToolkit.Mvvm.Messaging. |
| [`nuget-manager`](./nuget-manager/SKILL.md) | Manage NuGet packages — search, install, update, audit, and resolve conflicts. |
| [`fluentui-blazor`](../design-and-ui/fluentui-blazor/SKILL.md) | Fluent UI Blazor component library — setup, components, theming, JS interop. *(lives in design-and-ui)* |
| [`winapp-cli`](./winapp-cli/SKILL.md) | Build Windows command-line applications with .NET. |
| [`winmd-api-search`](./winmd-api-search/SKILL.md) | Search and browse WinMD API documentation for Windows development. |
| [`winui3-migration-guide`](./winui3-migration-guide/SKILL.md) | Migrate UWP applications to WinUI 3 with step-by-step guidance. |
| [`msstore-cli`](./msstore-cli/SKILL.md) | Publish Windows apps to the Microsoft Store via the `msstore` CLI — Partner Center, submissions, flights, CI/CD. |

### Java / JVM ecosystem

| Skill | What it does |
| --- | --- |
| [`java-add-graalvm-native-image-support`](./java-add-graalvm-native-image-support/SKILL.md) | Add GraalVM native image compilation support to Java projects. |
| [`java-docs`](./java-docs/SKILL.md) | Generate Javadoc documentation for Java code. |
| [`java-junit`](./java-junit/SKILL.md) | Write JUnit 5 tests for Java projects. |
| [`java-mcp-server-generator`](./java-mcp-server-generator/SKILL.md) | Generate MCP servers using the Java SDK. |
| [`java-refactoring-extract-method`](./java-refactoring-extract-method/SKILL.md) | Extract methods from complex Java functions to improve readability. |
| [`java-refactoring-remove-parameter`](./java-refactoring-remove-parameter/SKILL.md) | Remove unnecessary parameters from Java methods safely. |
| [`java-springboot`](./java-springboot/SKILL.md) | Spring Boot best practices, REST APIs, JPA, testing, and configuration. |
| [`javax-to-jakarta-migration`](./javax-to-jakarta-migration/SKILL.md) | Migrate Java EE `javax.*` packages to Jakarta EE `jakarta.*` namespace. |
| [`kotlin-mcp-server-generator`](./kotlin-mcp-server-generator/SKILL.md) | Generate MCP servers using the Kotlin SDK. |
| [`kotlin-springboot`](./kotlin-springboot/SKILL.md) | Spring Boot with Kotlin — coroutines, idiomatic Kotlin, data classes, testing. |
| [`spring-boot-testing`](./spring-boot-testing/SKILL.md) | Spring Boot testing — unit, integration, slice tests with MockMvc and Testcontainers. |

### Other languages & runtimes

| Skill | What it does |
| --- | --- |
| [`go-mcp-server-generator`](./go-mcp-server-generator/SKILL.md) | Generate MCP servers using the Go SDK. |
| [`php-mcp-server-generator`](./php-mcp-server-generator/SKILL.md) | Generate MCP servers using PHP. |
| [`python-mcp-server-generator`](./python-mcp-server-generator/SKILL.md) | Generate MCP servers using the Python SDK. |
| [`ruby-mcp-server-generator`](./ruby-mcp-server-generator/SKILL.md) | Generate MCP servers using the Ruby SDK. |
| [`rust-mcp-server-generator`](./rust-mcp-server-generator/SKILL.md) | Generate MCP servers using the Rust SDK. |
| [`swift-mcp-server-generator`](./swift-mcp-server-generator/SKILL.md) | Generate MCP servers using the Swift SDK. |
| [`typescript-mcp-server-generator`](./typescript-mcp-server-generator/SKILL.md) | Generate MCP servers using the TypeScript SDK. |
| [`ruff-recursive-fix`](./ruff-recursive-fix/SKILL.md) | Recursively fix Python lint errors using Ruff until the codebase is clean. |

### React ecosystem

| Skill | What it does |
| --- | --- |
| [`react-audit-grep-patterns`](./react-audit-grep-patterns/SKILL.md) | Grep-based audit patterns for React codebases — anti-patterns, performance issues. |
| [`react18-batching-patterns`](./react18-batching-patterns/SKILL.md) | React 18 automatic batching patterns and migration guidance. |
| [`react18-dep-compatibility`](./react18-dep-compatibility/SKILL.md) | Check and fix dependency compatibility for React 18 upgrades. |
| [`react18-enzyme-to-rtl`](./react18-enzyme-to-rtl/SKILL.md) | Migrate Enzyme tests to React Testing Library for React 18. |
| [`react18-legacy-context`](./react18-legacy-context/SKILL.md) | Replace legacy React Context API patterns with modern equivalents. |
| [`react18-lifecycle-patterns`](./react18-lifecycle-patterns/SKILL.md) | Modernize React lifecycle patterns for React 18 concurrent mode. |
| [`react18-string-refs`](./react18-string-refs/SKILL.md) | Migrate string refs to callback refs or `useRef` in React 18. |
| [`react19-concurrent-patterns`](./react19-concurrent-patterns/SKILL.md) | React 19 concurrent mode patterns — `use()`, transitions, deferred values. |
| [`react19-source-patterns`](./react19-source-patterns/SKILL.md) | React 19 data source patterns and suspense integration. |
| [`react19-test-patterns`](./react19-test-patterns/SKILL.md) | Testing patterns for React 19 features and concurrent rendering. |
| [`next-intl-add-language`](./next-intl-add-language/SKILL.md) | Add a new language/locale to a Next.js app using next-intl. |

### Salesforce

| Skill | What it does |
| --- | --- |
| [`salesforce-apex-quality`](./salesforce-apex-quality/SKILL.md) | Code quality standards and best practices for Salesforce Apex. |
| [`salesforce-component-standards`](./salesforce-component-standards/SKILL.md) | Lightning Web Component (LWC) design and coding standards. |
| [`salesforce-flow-design`](./salesforce-flow-design/SKILL.md) | Design and optimize Salesforce Flow automations. |

### Developer tooling & utilities

| Skill | What it does |
| --- | --- |
| [`batch-files`](./batch-files/SKILL.md) | Write and debug Windows batch scripts. |
| [`chrome-devtools`](./chrome-devtools/SKILL.md) | Use Chrome DevTools for debugging, performance profiling, and network inspection. |
| [`cli-mastery`](./cli-mastery/SKILL.md) | Master command-line tools and shell scripting productivity. |
| [`exam-ready`](./exam-ready/SKILL.md) | Generate exam-style questions and study materials from code or documentation. |
| [`game-engine`](./game-engine/SKILL.md) | Game engine patterns and development guidance for custom or commercial engines. |
| [`geofeed-tuner`](./geofeed-tuner/SKILL.md) | Create and validate ARIN/RIPE geofeed files for IP geolocation. |
| [`mentoring-juniors`](./mentoring-juniors/SKILL.md) | Mentor junior developers — code review, explanations, learning paths. |
| [`minecraft-plugin-development`](./minecraft-plugin-development/SKILL.md) | Develop Bukkit/Spigot/Paper Minecraft server plugins in Java. |
| [`noob-mode`](./noob-mode/SKILL.md) | Adapt explanations and responses for beginners with minimal jargon. |
| [`quasi-coder`](./quasi-coder/SKILL.md) | Generate pseudocode and algorithm sketches before writing real code. |
| [`remember-copilot`](./remember-copilot/SKILL.md) | Domain-organized memory keeper for VS Code — persist lessons learned across contexts with `/remember`. |
| [`remember-interactive-programming`](./remember-interactive-programming/SKILL.md) | Remember and recall interactive programming patterns and REPL workflows. |
| [`sandbox-npm-install`](./sandbox-npm-install/SKILL.md) | Safely install npm packages in a sandboxed environment to test for issues. |
| [`vscode-ext-commands`](./vscode-ext-commands/SKILL.md) | Develop VS Code extension commands — activation, registration, contribution points. |
| [`vscode-ext-localization`](./vscode-ext-localization/SKILL.md) | Add localization support to VS Code extensions. |
| [`x-twitter-scraper`](./x-twitter-scraper/SKILL.md) | Scrape and extract data from X (Twitter) using API and scraping techniques. |

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
