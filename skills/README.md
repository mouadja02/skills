# Skills Index

A curated collection of **622 Agent Skills** for Claude Code and Cursor, organized into **14 thematic categories**.

Each skill lives in its own folder with a `SKILL.md` file (YAML frontmatter for `name` + `description`, then the body of instructions). The agent auto-discovers and loads them when the description matches your request — both Claude Code and Cursor walk the directory tree recursively, so the category subfolders are transparent to discovery; they exist purely to keep things browsable on GitHub.

> **Sources**: Original *Superpowers* collection + [awesome-copilot](https://github.com/awesome-copilot/copilot-skills) skills library (341 skills ingested May 2026).

## Categories

| # | Folder | Skills | Theme |
| --- | --- | --- | --- |
| 1 | [`skills-management/`](./skills-management/) | 18 | Skill authoring, Copilot setup, AI tooling meta-skills |
| 2 | [`engineering-craft/`](./engineering-craft/) | 138 | Planning, TDD, code review, debugging, languages, frameworks, testing |
| 3 | [`ai-agents/`](./ai-agents/) | 90 | Agent architecture, scaffolds, prompt engineering, MCP, structured autonomy |
| 4 | [`context-engineering/`](./context-engineering/) | 14 | Context windows, compression, memory, persistence, visual thinking |
| 5 | [`creative-thinking/`](./creative-thinking/) | 8 | Bold ideation, lateral thinking, first-principles, reverse brainstorm, idea velocity, frame-shifting, constraints, deep focus |
| 6 | [`llm-integrations/`](./llm-integrations/) | 41 | OpenRouter, Arize, Phoenix, Qdrant, model selection |
| 7 | [`design-and-ui/`](./design-and-ui/) | 22 | Frontend, design systems, brand, themes, banners, UI tools |
| 8 | [`docs-and-presentations/`](./docs-and-presentations/) | 41 | READMEs, technical docs, slides, diagrams, specifications |
| 9 | [`data-and-backend/`](./data-and-backend/) | 70 | APIs, databases, ETL, Power Platform, cloud data services |
| 10 | [`business-and-strategy/`](./business-and-strategy/) | 74 | C-suite advisors, GTM strategy, board protocols, company OS |
| 11 | [`marketing-and-growth/`](./marketing-and-growth/) | 25 | Strategy, content, SEO, paid ads, CRO, copywriting |
| 12 | [`devops-and-infrastructure/`](./devops-and-infrastructure/) | 46 | CI/CD, Docker, Terraform, Azure/AWS, Linux, security |
| 13 | [`product-management/`](./product-management/) | 29 | PM toolkit, specs, GitHub workflows, discovery, agile delivery |
| 14 | [`caveman/`](./caveman/) | 6 | Token-efficient terse mode (~75% fewer output tokens) |

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
├── README.md                           (this file)
│
├── skills-management/          (18)    — meta-skills, Copilot setup, skill authoring
├── engineering-craft/          (138)   — dev discipline, languages, frameworks, testing
├── ai-agents/                  (90)    — agent design, MCP, structured autonomy, prompts
├── context-engineering/        (14)    — context windows, memory, compression, napkin
├── creative-thinking/          (8)     — bold ideation, lateral thinking, first-principles, frame-shift, deep focus
├── llm-integrations/           (41)    — OpenRouter, Arize, Phoenix, Qdrant
├── design-and-ui/              (22)    — frontend, brand, design systems, UI tools
├── docs-and-presentations/     (41)    — docs, slides, diagrams, specs, blueprints
├── data-and-backend/           (70)    — APIs, databases, ETL, Power Platform, migrations
├── business-and-strategy/      (74)    — C-suite advisors, GTM, board protocols
├── marketing-and-growth/       (25)    — full marketing operating system
├── devops-and-infrastructure/  (46)    — CI/CD, IaC, Azure/AWS, Linux, containers, security
├── product-management/         (29)    — PM toolkit, specs, GitHub workflows, agile
└── caveman/                    (6)     — token-efficient terse mode + skill discovery
```

Total: **622 skills** (plus nested sub-skills in `ai-agents/bmm-skills/`, `ai-agents/auto-memory-pro/`, `data-and-backend/developing-with-streamlit/`, and `ai-agents/autoresearch-agent/`).
