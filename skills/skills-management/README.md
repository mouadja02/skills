# skills-management

Meta-skills about **building, editing, and benchmarking** Agent Skills themselves, plus GitHub Copilot setup, tooling, and AI-readiness assessment.

If you want to write a new skill, optimize an existing one, or configure GitHub Copilot for your project — start here.

## Skills in this category

### Skill authoring

| Skill | What it does |
| --- | --- |
| [`skill-creator`](./skill-creator/SKILL.md) | Create new skills, modify existing ones, run evaluations, and benchmark skill performance with variance analysis. Includes scripts for description optimization, eval loops, and packaging. |
| [`writing-skills`](./writing-skills/SKILL.md) | The how-to-write-a-skill discipline. Covers progressive disclosure, frontmatter rules, naming conventions, sub-skill linking, and verification before deployment. |
| [`make-skill-template`](./make-skill-template/SKILL.md) | Generate skill template files with proper YAML frontmatter and structure. |
| [`microsoft-skill-creator`](./microsoft-skill-creator/SKILL.md) | Create Microsoft Copilot-compatible skills following Microsoft's schema and guidelines. |

### GitHub Copilot setup & tooling

| Skill | What it does |
| --- | --- |
| [`github-copilot-starter`](./github-copilot-starter/SKILL.md) | Set up GitHub Copilot in a project — configuration, `.github/copilot-instructions.md`, best practices. |
| [`copilot-cli-quickstart`](./copilot-cli-quickstart/SKILL.md) | Get started with the GitHub Copilot CLI — installation, authentication, commands. |
| [`copilot-instructions-blueprint-generator`](./copilot-instructions-blueprint-generator/SKILL.md) | Generate `.github/copilot-instructions.md` files tailored to your project's stack and conventions. |
| [`copilot-sdk`](./copilot-sdk/SKILL.md) | Build extensions and integrations using the GitHub Copilot SDK. |
| [`copilot-spaces`](./copilot-spaces/SKILL.md) | Use GitHub Copilot Spaces for shared context and collaborative AI workspaces. |
| [`copilot-usage-metrics`](./copilot-usage-metrics/SKILL.md) | Track and analyze GitHub Copilot usage metrics across your organization. |
| [`vardoger-analyze`](./vardoger-analyze/SKILL.md) | Personalize Copilot CLI by analyzing session history — extracts patterns, writes personalization to `~/.copilot/copilot-instructions.md`. |
| [`find-skills`](./find-skills/SKILL.md) | Discover and install agent skills from the awesome-copilot catalog. |

### AI readiness assessment

| Skill | What it does |
| --- | --- |
| [`acreadiness-assess`](./acreadiness-assess/SKILL.md) | Assess a codebase's AI-Copilot readiness score across multiple dimensions. |
| [`acreadiness-generate-instructions`](./acreadiness-generate-instructions/SKILL.md) | Generate Copilot instructions to improve AI-readiness for a project. |
| [`acreadiness-policy`](./acreadiness-policy/SKILL.md) | Define and enforce AI-readiness policies for development teams. |

### Skill discovery

| Skill | What it does |
| --- | --- |
| [`suggest-awesome-github-copilot-agents`](./suggest-awesome-github-copilot-agents/SKILL.md) | Suggest relevant agents from the awesome-copilot repository for a task. |
| [`suggest-awesome-github-copilot-instructions`](./suggest-awesome-github-copilot-instructions/SKILL.md) | Suggest relevant Copilot instructions for a project from the awesome-copilot catalog. |
| [`suggest-awesome-github-copilot-skills`](./suggest-awesome-github-copilot-skills/SKILL.md) | Suggest relevant skills from the awesome-copilot catalog for a use case. |

## When to use this folder

- "Create a skill for X"
- "Improve the description of this skill so it triggers better"
- "Benchmark this skill's accuracy"
- "Should this be a skill, a sub-skill, or just a script?"
- "Set up GitHub Copilot for my project"
- "How AI-ready is my codebase?"
- "What skills/agents are available for X?"

## Related categories

- [`engineering-craft/`](../engineering-craft/) — once your skill exists, the craft skills cover TDD, code review, and verification for the implementation inside it.
- [`ai-agents/`](../ai-agents/) — agent-focused skills that complement Copilot tooling.
- [`docs-and-presentations/readme-writer/`](../docs-and-presentations/readme-writer/) — for documenting the project that wraps the skill.
