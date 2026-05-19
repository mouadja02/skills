# Skills Index

A curated collection of **280+ Agent Skills** for Claude Code and Cursor, organized into **16 thematic categories**.

Each skill lives in its own folder with a `SKILL.md` file (YAML frontmatter for `name` + `description`, then the body of instructions). The agent auto-discovers and loads them when the description matches your request — both Claude Code and Cursor walk the directory tree recursively, so the category subfolders are transparent to discovery; they exist purely to keep things browsable on GitHub.

## Categories

| # | Folder | Skills | Theme |
| --- | --- | --- | --- |
| 1 | [`skill-authoring/`](./skill-authoring/) | 2 | Building, editing, and benchmarking skills themselves |
| 2 | [`coding/`](./coding/) | 24 | The disciplined coding loop: spec, planning, TDD, review, debugging, security, CI/CD, launch |
| 3 | [`engineering-craft/`](./engineering-craft/) | 35 | Planning, TDD, code review, debugging, verification, senior IC roles, evaluation |
| 4 | [`ai-agents/`](./ai-agents/) | 18 | Agent architecture, scaffolds, prompt engineering, MCP, BMad Method |
| 5 | [`context-engineering/`](./context-engineering/) | 6 | Context windows, compression, memory, persistence |
| 6 | [`openrouter/`](./openrouter/) | 5 | OpenRouter SDK, models, OAuth, image generation |
| 7 | [`design-and-ui/`](./design-and-ui/) | 10 | Frontend, design systems, brand, themes, banners |
| 8 | [`docs-and-presentations/`](./docs-and-presentations/) | 7 | READMEs, technical docs, slides, diagrams |
| 9 | [`data-and-backend/`](./data-and-backend/) | 4 | Python/FastAPI, Snowflake, dbt, ETL |
| 10 | [`streamlit/`](./streamlit/) | 18 | Streamlit apps, dashboards, custom components, theming (1 hub + 17 sub-skills) |
| 11 | [`research-and-development/`](./research-and-development/) | 1 | Deep research, systematic reviews, multi-agent research pipelines |
| 12 | [`business-and-strategy/`](./business-and-strategy/) | 23 | C-suite advisors, board meetings, company OS, scenario modeling |
| 13 | [`marketing-and-growth/`](./marketing-and-growth/) | 22 | Strategy, content, SEO, paid ads, CRO, copywriting |
| 14 | [`devops-and-infrastructure/`](./devops-and-infrastructure/) | 14 | CI/CD, Docker, Helm, Terraform, AWS, security, observability |
| 15 | [`product-management/`](./product-management/) | 10 | PM toolkit, discovery, experiments, agile delivery, UX research |
| 16 | [`caveman/`](./caveman/) | 6 | Token-efficient terse mode (~75% fewer output tokens) + skill discovery |

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
