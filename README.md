# skills

<!-- generated:catalog-metrics:start -->
A curated collection of **811 Agent Skills** across **36 categories** for Claude Code, Cursor, and other clients that discover `SKILL.md` files recursively.
<!-- generated:catalog-metrics:end -->

Each skill is a reusable instruction package with YAML frontmatter and an agent-readable body. Category
folders keep the repository browsable without changing recursive skill discovery.

Browse the searchable site at [mouadja02.github.io/skills](https://mouadja02.github.io/skills/), the
complete generated Markdown index at [`SKILLS.md`](./SKILLS.md), or the focused category indexes under
[`skills/`](./skills/).

## Quick Start

Install a single skill with the provided scripts.

```bash
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- engineering-craft/test-driven-development \
      -d ~/.claude/skills
```

```powershell
$content = irm https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1
iex $content
Install-Skill engineering-craft/test-driven-development -Dest $HOME\.claude\skills
```

Selectors may be an exact install path, a category, a quoted glob, or `--all` / `-All`. Use
`--dry-run` / `-DryRun` to preview an installation.

Skills may also be installed from the Pages ZIP artifacts:

```text
https://mouadja02.github.io/skills/zips/skill/<install-path>.zip
https://mouadja02.github.io/skills/zips/category/<category>.zip
https://mouadja02.github.io/skills/zips/all.zip
```

## Client Paths

| Client | Project path | User path |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |

## Categories

This table is generated from `docs/manifest.json`.

<!-- generated:category-catalog:start -->
| Category | Skills | Scope |
| --- | ---: | --- |
| [`agent-design`](./skills/agent-design/) | 58 | Agent architecture, orchestration, harnesses, safety, scaffolding, and coding-agent interfaces. |
| [`agent-eval`](./skills/agent-eval/) | 24 | Agent evaluation, RAG evaluation, memory, autoresearch, benchmarking, and lifecycle improvement. |
| [`api-backend`](./skills/api-backend/) | 12 | API design, backend implementation, OpenAPI, TypeSpec, FastAPI, and integrations. |
| [`business-strategy`](./skills/business-strategy/) | 64 | Executive advisory, board preparation, operating systems, and strategic decision support. |
| [`cloud-aws`](./skills/cloud-aws/) | 84 | AWS services and agentic workflows: Bedrock, Lambda/serverless, databases, analytics/data lake, storage, networking, IAM, CDK/CloudFormation, cost, and observability. |
| [`cloud-azure`](./skills/cloud-azure/) | 18 | Azure, AWS, cloud architecture, IoT, pricing, deployment, and operations. |
| [`code-quality`](./skills/code-quality/) | 17 | Code review, refactoring, static analysis, security review, and integrity checks. |
| [`coding`](./skills/coding/) | 33 | Language-agnostic implementation workflows, planning, debugging, security, and shipping. |
| [`communication`](./skills/communication/) | 1 | Decision frameworks, stakeholder communication, proposals, and concise trade-off analysis. |
| [`context-engineering`](./skills/context-engineering/) | 17 | Context design, compression, evolving memory, provenance, and codebase knowledge acquisition. |
| [`creative`](./skills/creative/) | 2 | Creative ideation, concept visualization, generative methods, and reusable design prompts. |
| [`databases`](./skills/databases/) | 22 | Database design, SQL optimization, migrations, analytics, Snowflake, PostgreSQL, and dbt. |
| [`design-and-ui`](./skills/design-and-ui/) | 34 | Frontend design, UI systems, visual artifacts, animation, branding, and accessibility. |
| [`dev-workflow`](./skills/dev-workflow/) | 29 | Git, GitHub, CLI tooling, release workflows, local automation, and developer productivity. |
| [`devops`](./skills/devops/) | 37 | CI/CD, containers, infrastructure as code, Linux operations, observability, and security. |
| [`diagrams-slides`](./skills/diagrams-slides/) | 14 | Diagrams, presentations, meeting artifacts, and professional visual communication. |
| [`documentation`](./skills/documentation/) | 28 | READMEs, ADRs, project documentation, Markdown tooling, conversion, and publishing. |
| [`dotnet`](./skills/dotnet/) | 19 | .NET, C#, WinUI, MVVM, NuGet, testing, and VS Code extension development. |
| [`engineering-craft`](./skills/engineering-craft/) | 37 | Senior engineering practices, planning, mentoring, verification, and cross-cutting craft. |
| [`finance`](./skills/finance/) | 7 | Financial modeling, valuation, Excel authoring, investment analysis, and presentation workflows. |
| [`go-to-market`](./skills/go-to-market/) | 11 | Launch planning, positioning, pricing, partnerships, enterprise sales, and PLG. |
| [`java-kotlin`](./skills/java-kotlin/) | 11 | Java, Kotlin, Spring Boot, testing, refactoring, and migration workflows. |
| [`llm-tooling`](./skills/llm-tooling/) | 47 | LLM observability, evaluation, serving, vector search, OpenRouter, Phoenix, Arize, Qdrant, and vLLM. |
| [`marketing-and-growth`](./skills/marketing-and-growth/) | 26 | Marketing strategy, content, acquisition, SEO, CRO, and lifecycle growth. |
| [`mcp`](./skills/mcp/) | 15 | Model Context Protocol server generation, tooling, deployment, and security. |
| [`messaging`](./skills/messaging/) | 1 | Messaging integrations and relay workflows. |
| [`microsoft-agents`](./skills/microsoft-agents/) | 11 | Microsoft Copilot agents, declarative agents, Foundry, Entra, and MCP tooling. |
| [`microsoft-data`](./skills/microsoft-data/) | 17 | Power BI, Power Apps, Power Automate, Dataverse, and Power Platform architecture. |
| [`personal-productivity`](./skills/personal-productivity/) | 10 | Personal productivity, reminders, communication, notes, and connected tools. |
| [`product-management`](./skills/product-management/) | 29 | Product discovery, specifications, delivery planning, analytics, and agile workflows. |
| [`prompting`](./skills/prompting/) | 15 | Prompt engineering, optimization, safety review, and creative-thinking frameworks. |
| [`react-frontend`](./skills/react-frontend/) | 17 | React, Vue, Next.js, mobile frontend frameworks, migrations, and testing. |
| [`research`](./skills/research/) | 1 | Research workflows, public-record investigation, source collection, and evidence synthesis. |
| [`skills-management`](./skills/skills-management/) | 13 | Skill authoring, discovery, cleanup, Copilot configuration, and terse interaction modes. |
| [`streamlit`](./skills/streamlit/) | 18 | Streamlit applications, dashboards, chat UIs, components, layouts, and performance. |
| [`testing`](./skills/testing/) | 12 | Testing, QA, Playwright, pytest, debugging, and evaluation strategy. |
<!-- generated:category-catalog:end -->

## Local MCP Discovery

Use the local stdio MCP server when an agent should discover or install skills without loading the full
library into context. See [Local Skills MCP Quickstart](./docs/skills-mcp.md).

The intended flow is:

```text
list_categories -> list_skills or search_skills -> get_skill -> read_skill_doc -> install_skill
```

## Machine-Readable Index

The canonical generated indexes are:

- [`docs/manifest.json`](./docs/manifest.json)
- [`docs/manifest.tsv`](./docs/manifest.tsv)
- [`SKILLS.md`](./SKILLS.md)

Regenerate them, the category READMEs, and the root catalog with:

```bash
npm run build:manifest
```

## Local Development

```bash
npm install
npm run build:manifest
npm run check:docs
npm run build:zips
npm run preview
```

`npm run build` performs manifest generation, documentation validation, and ZIP packaging in order.

## Adding Or Editing Skills

Follow [`CONTRIBUTING.md`](./CONTRIBUTING.md). Every skill must contain a `SKILL.md` file with `name` and
`description` frontmatter. Category READMEs are generated from the manifest; do not hand-edit them.

## Repository Layout

```text
skills/<category>/<skill>/SKILL.md   skill instructions
skills/<category>/README.md          generated category index
scripts/build-manifest.mjs           manifests and documentation indexes
scripts/check-docs.mjs               documentation coverage audit
scripts/build-zips.mjs               ZIP artifacts for Pages
docs/                               Pages site and machine-readable manifests
```

## License

Skills come from a mix of original work and adapted public sources. Check individual skill folders for
license files and attribution before redistributing a selected package. See
[`docs/third-party-sources.md`](./docs/third-party-sources.md) for repo-level imported source notes.
