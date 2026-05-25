# Skills Index

A curated collection of **650+ Agent Skills** for Claude Code and Cursor, organized into **29 focused categories** (10–28 skills each).

Each skill lives in its own folder with a `SKILL.md` file (YAML frontmatter for `name` + `description`, then the body of instructions). The agent auto-discovers and loads them when the description matches your request — both Claude Code and Cursor walk the directory tree recursively, so the category subfolders are transparent to discovery; they exist purely to keep things browsable on GitHub.

> **Sources**: Original *Superpowers* collection + [awesome-copilot](https://github.com/awesome-copilot/copilot-skills) skills library + GSAP official skills + [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

## Categories

### Agent & AI systems

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 1 | [`agent-design/`](./agent-design/) | 21 | Agent architecture, patterns, BMad, browser automation, RAG, governance |
| 2 | [`agent-eval/`](./agent-eval/) | 9 | Memory, evaluation, autoresearch, local AI stack |
| 3 | [`mcp/`](./mcp/) | 13 | MCP server builders (10 languages) + tooling + security |
| 4 | [`microsoft-agents/`](./microsoft-agents/) | 11 | Microsoft Copilot agents, Foundry, declarative agents |
| 5 | [`prompting/`](./prompting/) | 15 | Prompt engineering + creative thinking & ideation |

### Software engineering

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 6 | [`coding/`](./coding/) | 24 | The disciplined coding loop: spec, TDD, debugging, security, CI/CD |
| 7 | [`engineering-craft/`](./engineering-craft/) | 37 | Senior IC roles, planning, mentoring, cross-cutting practices |
| 8 | [`dotnet/`](./dotnet/) | 19 | C#, .NET, WinUI, MVVM, NuGet, VS Code extensions |
| 9 | [`java-kotlin/`](./java-kotlin/) | 11 | Java, Kotlin, Spring Boot |
| 10 | [`react-frontend/`](./react-frontend/) | 17 | React 18/19, Vue, Next.js, Flutter, React Native |
| 11 | [`testing/`](./testing/) | 12 | Playwright, pytest, systematic debugging, QA |
| 12 | [`code-quality/`](./code-quality/) | 15 | Code review, refactoring, security audit, CodeQL |
| 13 | [`dev-workflow/`](./dev-workflow/) | 22 | Git, GitHub CLI, automation, CLI tooling |

### Infrastructure & cloud

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 14 | [`devops/`](./devops/) | 28 | CI/CD, Docker, Helm, Terraform, Linux, security operations |
| 15 | [`cloud-azure/`](./cloud-azure/) | 18 | Azure services, AWS, IoT, cloud design patterns |

### Data & backend

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 16 | [`databases/`](./databases/) | 22 | SQL, PostgreSQL, Oracle migration, Snowflake, BigQuery, dbt |
| 17 | [`microsoft-data/`](./microsoft-data/) | 17 | Power BI, Power Apps, Power Automate, Dataverse |
| 18 | [`api-backend/`](./api-backend/) | 11 | TypeSpec, OpenAPI, FastAPI, Stripe, GDPR |

### LLM & AI tooling

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 19 | [`llm-tooling/`](./llm-tooling/) | 26 | Arize, Phoenix, Qdrant, OpenRouter, model recommendation |
| 20 | [`context-engineering/`](./context-engineering/) | 15 | Context windows, compression, memory, deep research |

### Design & UI

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 21 | [`design-and-ui/`](./design-and-ui/) | 31 | Frontend design, UI systems, brand, GSAP animation |

### Docs & communications

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 22 | [`documentation/`](./documentation/) | 26 | READMEs, ADRs, API docs, llms.txt, markdown tools |
| 23 | [`diagrams-slides/`](./diagrams-slides/) | 12 | Slides, draw.io, PlantUML, presentations, professional comms |

### Business & product

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 24 | [`business-strategy/`](./business-strategy/) | 25 | C-suite advisors, board, company OS, M&A |
| 25 | [`go-to-market/`](./go-to-market/) | 11 | GTM strategy, PLG, enterprise sales, positioning |
| 26 | [`marketing-and-growth/`](./marketing-and-growth/) | 25 | Content, SEO, paid ads, CRO, copywriting |
| 27 | [`product-management/`](./product-management/) | 29 | PM toolkit, discovery, specifications, agile delivery |

### Platform skills

| # | Folder | Skills | Theme |
| --- | --- | ---: | --- |
| 28 | [`streamlit/`](./streamlit/) | 1 | Streamlit apps, dashboards, custom components, theming |
| 29 | [`skills-management/`](./skills-management/) | 24 | Skill authoring, Copilot config, caveman terse mode |

Each category folder has its own `README.md` with a full per-skill table.

## Usage

Skills are picked up automatically by:

- **Claude Code** when placed in `.claude/skills/<name>/SKILL.md`
- **Cursor** when placed in `.cursor/skills/<name>/SKILL.md` (project) or `~/.cursor/skills/<name>/SKILL.md` (user)

To use this collection:

```bash
# Whole collection (one-shot)
cp -r skills/* /path/to/your/project/.claude/skills/

# A single category
cp -r skills/engineering-craft/* /path/to/your/project/.claude/skills/

# A single skill
cp -r skills/ai-agents/senior-prompt-engineer /path/to/your/project/.claude/skills/
```

## Adding or editing a skill

Use the meta-skills:

- [`skills-management/skill-creator/`](./skills-management/skill-creator/) — create, evaluate, and benchmark skills
- [`skills-management/writing-skills/`](./skills-management/writing-skills/) — the how-to-write-a-skill discipline

## File tree at a glance

```
skills/
├── README.md                         (this file)
│
├── skill-authoring/         (2)      — meta-skills for authoring skills
├── coding/                  (24)     — disciplined coding loop (spec → TDD → review → ship)
├── engineering-craft/       (35)     — dev discipline + senior IC skills + evaluation
├── ai-agents/               (18)     — agent design, includes BMM (30 sub-skills)
├── context-engineering/     (6)      — context windows, memory, compression
├── openrouter/              (5)      — OpenRouter SDK, models, OAuth, images
├── design-and-ui/           (10)     — frontend, brand, design systems
├── docs-and-presentations/  (7)      — docs, slides, diagrams
├── data-and-backend/        (4)      — FastAPI, Snowflake, dbt, ETL
├── streamlit/               (18)     — Streamlit apps + 17 sub-skills
├── research-and-development/ (1)     — deep research, systematic reviews
├── business-and-strategy/   (23)     — C-suite advisors, board protocols
├── marketing-and-growth/    (22)     — full marketing operating system
├── devops-and-infrastructure/ (14)   — CI/CD, IaC, security, observability
├── product-management/      (10)     — PM toolkit, experiments, agile
└── caveman/                 (6)      — token-efficient terse mode + find-skills
```

Total: **280+ skills** (run `npm run build:manifest` for the exact current count).
