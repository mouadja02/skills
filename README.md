# skills

A curated collection of **149 Agent Skills** for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Cursor](https://cursor.com), spanning *how to write code well*, *how to build agents*, *how to design UIs*, *how to ship docs and presentations*, *how to integrate LLMs*, *how to advise the C-suite*, *how to run growth marketing*, *how to operate infrastructure*, *how to manage products*, and *how to talk like a token-efficient caveman*.

> Skills are reusable, model-invocable instruction packages. They auto-load based on the user's request, scoped to a single domain (writing tests, designing logos, querying Snowflake, advising a CEO, designing an experiment, etc.). One folder per skill, one `SKILL.md` per folder.

---

## Quick start

Place this repo's `skills/` directory wherever your agent looks for skills:

| Client | Path |
| --- | --- |
| **Claude Code** (project) | `.claude/skills/` |
| **Claude Code** (user) | `~/.claude/skills/` |
| **Cursor** (project) | `.cursor/skills/` |
| **Cursor** (user) | `~/.cursor/skills/` |

Both clients **walk the tree recursively**, so the category subfolders below don't affect discovery — they exist purely to make this repo browsable on GitHub.

To copy these skills into your own project:

```bash
git clone https://github.com/<your-fork>/skills.git
cp -r skills/skills/* /path/to/your/project/.claude/skills/
```

Or install one category at a time:

```bash
cp -r skills/skills/engineering-craft/* /path/to/your/project/.claude/skills/
```

---

## Categories

The 149 skills are grouped into 13 thematic categories. Click any category to see its full per-skill table.

| Category | Skills | What lives here |
| --- | --- | --- |
| [**`skill-authoring/`**](./skills/skill-authoring/) | 2 | Building, editing, and benchmarking the skills themselves. |
| [**`engineering-craft/`**](./skills/engineering-craft/) | 29 | The disciplined development loop: planning, brainstorming, TDD, debugging, code review, git worktrees, verification — plus senior IC roles (architect, frontend, backend, fullstack, ML, data, QA, PM). |
| [**`ai-agents/`**](./skills/ai-agents/) | 13 | Designing, scaffolding, and operating AI agents — single and multi-agent, headless and TUI. Includes the **BMad Method** with 30 sub-skills and 6 named personas, the canonical `senior-prompt-engineer` (with A/B testing + versioning), and `mcp-server-builder`. |
| [**`context-engineering/`**](./skills/context-engineering/) | 6 | Context windows, compression, persistence, memory frameworks, lost-in-middle mitigation. |
| [**`llm-integrations/`**](./skills/llm-integrations/) | 5 | OpenRouter family — TypeScript SDK, model discovery, image generation, OAuth, migration. |
| [**`design-and-ui/`**](./skills/design-and-ui/) | 10 | Frontend craft, design systems, brand identity, themes, banners, narrative portfolio sites. |
| [**`docs-and-presentations/`**](./skills/docs-and-presentations/) | 6 | READMEs, technical docs, ADRs, HTML slides, .pptx files, SVG diagrams. |
| [**`data-and-backend/`**](./skills/data-and-backend/) | 5 | FastAPI + LLM, Snowflake SQL, dbt, ETL-to-dbt migration, Streamlit (with nested sub-skills). |
| [**`business-and-strategy/`**](./skills/business-and-strategy/) | 22 | The full C-suite — CEO, CFO, CTO, COO, CPO, CMO, CRO, CISO, CHRO advisors plus chief-of-staff routing, board-meeting protocol, company OS, scenario war room, executive mentor. |
| [**`marketing-and-growth/`**](./skills/marketing-and-growth/) | 22 | A complete marketing operating system — strategy, content, SEO, paid acquisition, copywriting, conversion-rate optimization. |
| [**`devops-and-infrastructure/`**](./skills/devops-and-infrastructure/) | 14 | CI/CD, Docker, Helm, Terraform, AWS, database design, dependency auditing, incident command, observability, Stripe integration, secops. |
| [**`product-management/`**](./skills/product-management/) | 9 | PM toolkit, discovery, **canonical `experiment-designer`** (product *and* marketing A/B), agile delivery, UX research, roadmap communication. |
| [**`caveman/`**](./skills/caveman/) | 6 | Token-efficient terse mode (~75% fewer output tokens) — plus `caveman-commit`, `caveman-review`, `caveman-compress`, and `find-skills`. |

---

## Highlight skills

A handful of skills you might want to load first:

| Skill | Why it matters |
| --- | --- |
| [`engineering-craft/using-superpowers`](./skills/engineering-craft/using-superpowers/SKILL.md) | The conversation entry point. Establishes how the agent finds and uses other skills. |
| [`engineering-craft/brainstorming`](./skills/engineering-craft/brainstorming/SKILL.md) | Mandatory primer before any creative work. Forces requirements & design exploration. |
| [`engineering-craft/test-driven-development`](./skills/engineering-craft/test-driven-development/SKILL.md) | Test-first discipline before writing any feature or bugfix. |
| [`ai-agents/bmm-skills`](./skills/ai-agents/bmm-skills/SKILL.md) | BMad Method router — full agile AI-development workflow with 30 sub-skills. |
| [`ai-agents/senior-prompt-engineer`](./skills/ai-agents/senior-prompt-engineer/SKILL.md) | Prompt optimization, A/B testing, versioning, RAG eval, agent orchestration — the canonical prompt-engineering skill. |
| [`business-and-strategy/chief-of-staff`](./skills/business-and-strategy/chief-of-staff/SKILL.md) | C-suite router — pick the right exec advisor or trigger a multi-role board meeting. |
| [`product-management/experiment-designer`](./skills/product-management/experiment-designer/SKILL.md) | The canonical home for any A/B / multivariate / split test — product *or* marketing. |
| [`design-and-ui/impeccable`](./skills/design-and-ui/impeccable/SKILL.md) | Critique, polish, and harden any frontend interface. |
| [`skill-authoring/skill-creator`](./skills/skill-authoring/skill-creator/SKILL.md) | The meta-skill for creating, evaluating, and benchmarking new skills. |

---

## Repo layout

```
.
├── README.md                                  (you are here)
└── skills/
    ├── README.md                              (skills index)
    │
    ├── skill-authoring/             (2)
    ├── engineering-craft/           (29)
    ├── ai-agents/                   (13, includes nested bmm-skills/ with 30 sub-skills)
    ├── context-engineering/         (6)
    ├── llm-integrations/            (5)
    ├── design-and-ui/               (10)
    ├── docs-and-presentations/      (6)
    ├── data-and-backend/            (5, includes nested developing-with-streamlit/skills/)
    ├── business-and-strategy/       (22)
    ├── marketing-and-growth/        (22)
    ├── devops-and-infrastructure/   (14)
    ├── product-management/          (9)
    └── caveman/                     (6, plus rules/caveman.mdc Cursor rule)
```

---

## How a skill works

Every skill folder contains a `SKILL.md` with YAML frontmatter:

```yaml
---
name: my-skill
description: Use when the user asks to do X. Triggers on keywords X, Y, Z.
---

# My Skill

Instructions, references, and examples for the agent...
```

The agent client (Claude Code or Cursor) scans these files at startup, builds an index of `name + description`, and loads the body of a skill *only* when the user's request matches its description. This keeps the context window small while making a large library of expertise available on demand.

A skill folder may also contain:

- `references/` — supporting markdown the agent reads on demand
- `scripts/` — runnable scripts (Python, Node, shell)
- `templates/` — starter files the skill produces
- `assets/` — images, fonts, data files

---

## Authoring a new skill

Use the meta-skills:

```text
skills/skill-authoring/skill-creator/   ← create, eval, benchmark
skills/skill-authoring/writing-skills/  ← style guide & conventions
```

Both follow strict conventions on file size, frontmatter format, naming, and progressive disclosure. Read `writing-skills` first, then `skill-creator` for the tooling.

---

## License

Skills here come from a mix of personal authorship and adapted public sources — Anthropic Claude Code skills, BMad Method, Cursor skill examples, OpenRouter docs, the Alireza Rezvani skill collection, and others. Individual skill folders contain their own `LICENSE.txt` where applicable.
