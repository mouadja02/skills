# Skills Index

A curated collection of **258 Agent Skills** for Claude Code and Cursor, organized into **13 thematic categories**.

Each skill lives in its own folder with a `SKILL.md` file (YAML frontmatter for `name` + `description`, then the body of instructions). The agent auto-discovers and loads them when the description matches your request — both Claude Code and Cursor walk the directory tree recursively, so the category subfolders are transparent to discovery; they exist purely to keep things browsable on GitHub.

## Categories

| # | Folder | Skills | Theme |
| --- | --- | --- | --- |
| 1 | [`skill-authoring/`](./skill-authoring/) | 2 | Building, editing, and benchmarking skills themselves |
| 2 | [`engineering-craft/`](./engineering-craft/) | 35 | Planning, TDD, code review, debugging, verification, senior IC roles |
| 3 | [`ai-agents/`](./ai-agents/) | 18 | Agent architecture, scaffolds, prompt engineering, MCP, BMad Method |
| 4 | [`context-engineering/`](./context-engineering/) | 6 | Context windows, compression, memory, persistence |
| 5 | [`llm-integrations/`](./llm-integrations/) | 5 | OpenRouter SDK, models, OAuth, image generation |
| 6 | [`design-and-ui/`](./design-and-ui/) | 10 | Frontend, design systems, brand, themes, banners |
| 7 | [`docs-and-presentations/`](./docs-and-presentations/) | 7 | READMEs, technical docs, slides, diagrams |
| 8 | [`data-and-backend/`](./data-and-backend/) | 5 | Python/FastAPI, Snowflake, dbt, ETL, Streamlit |
| 9 | [`business-and-strategy/`](./business-and-strategy/) | 23 | C-suite advisors, board meetings, company OS, scenario modeling |
| 10 | [`marketing-and-growth/`](./marketing-and-growth/) | 22 | Strategy, content, SEO, paid ads, CRO, copywriting |
| 11 | [`devops-and-infrastructure/`](./devops-and-infrastructure/) | 14 | CI/CD, Docker, Helm, Terraform, AWS, security, observability |
| 12 | [`product-management/`](./product-management/) | 10 | PM toolkit, discovery, experiments, agile delivery, UX research |
| 13 | [`caveman/`](./caveman/) | 6 | Token-efficient terse mode (~75% fewer output tokens) + skill discovery |

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

- [`skill-authoring/skill-creator/`](./skill-authoring/skill-creator/) — create, evaluate, and benchmark skills
- [`skill-authoring/writing-skills/`](./skill-authoring/writing-skills/) — the how-to-write-a-skill discipline

## File tree at a glance

```
skills/
├── README.md                       (this file)
│
├── skill-authoring/         (2)    — meta-skills for authoring skills
├── engineering-craft/       (35)   — dev discipline + senior IC skills
├── ai-agents/               (18)   — agent design, includes BMM (30 sub-skills)
├── context-engineering/     (6)    — context windows, memory, compression
├── llm-integrations/        (5)    — OpenRouter family
├── design-and-ui/           (10)   — frontend, brand, design systems
├── docs-and-presentations/  (7)    — docs, slides, diagrams
├── data-and-backend/        (5)    — FastAPI, Snowflake, dbt, Streamlit
├── business-and-strategy/   (23)   — C-suite advisors, board protocols
├── marketing-and-growth/    (22)   — full marketing operating system
├── devops-and-infrastructure/ (14) — CI/CD, IaC, security, observability
├── product-management/      (10)    — PM toolkit, experiments, agile
└── caveman/                 (6)    — token-efficient terse mode + find-skills
```

Total: **258 skills** (plus 30 BMM sub-skills nested under `ai-agents/bmm-skills/`, and the Streamlit sub-skills nested under `data-and-backend/developing-with-streamlit/skills/`).
