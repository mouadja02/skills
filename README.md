# skills

A curated collection of **622 Agent Skills** for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Cursor](https://cursor.com), spanning *how to write code well*, *how to build agents*, *how to design UIs*, *how to ship docs and presentations*, *how to integrate LLMs*, *how to advise the C-suite*, *how to run growth marketing*, *how to operate infrastructure*, *how to manage products*, *how to think boldly and creatively*, and *how to talk like a token-efficient caveman*.

> Skills are reusable, model-invocable instruction packages. They auto-load based on the user's request, scoped to a single domain (writing tests, designing logos, querying Snowflake, advising a CEO, designing an experiment, etc.). One folder per skill, one `SKILL.md` per folder.

**Three ways to grab a skill:** one-line installer · `npx degit` · direct `.zip` download from [the browser](https://mouadja02.github.io/skills/).

---

## Quick start

Skills go in whichever folder your agent already looks at:

| Client | Path |
| --- | --- |
| **Claude Code** (project) | `.claude/skills/` |
| **Claude Code** (user) | `~/.claude/skills/` |
| **Cursor** (project) | `.cursor/skills/` |
| **Cursor** (user) | `~/.cursor/skills/` |

Both clients walk the tree recursively, so the category subfolders below don't affect discovery — they exist purely to make this repo browsable on GitHub.

### Browse and install

Open the searchable index — it gives every skill a copy-paste install command **and a one-click `.zip` download**:

**[mouadja02.github.io/skills](https://mouadja02.github.io/skills/)** *(once Pages is enabled — see [Setup](#setup-github-pages-one-time))*

Or browse the markdown table at [`SKILLS.md`](./SKILLS.md), or the per-category READMEs under [`skills/`](./skills/).

### Install skills (no full clone)

The installer scripts accept three kinds of selector:

| Selector | What it installs | Example |
| --- | --- | --- |
| Exact install path | one skill | `engineering-craft/test-driven-development` |
| Category name | every skill in that category | `engineering-craft` (29 skills) |
| Glob pattern (quoted) | every install path that matches | `"*bmad*"`, `"ai-agents/*"`, `"*-advisor"` |
| All skills | every skill, preserving category paths | `--all` / `-All` |

`-d` / `-Dest` is required. For single-skill installs, `<dest>` can be the final skill folder or an existing parent folder; parent folders install the skill under `<dest>/<skill-name>`. For category and glob installs, `<dest>` is the parent folder; each matched skill gets its own subfolder underneath. Use `--force` / `-Force` to overwrite existing destinations.

#### Option A — installer scripts (recommended)

**bash / zsh / WSL / Git Bash:**

```bash
# one skill
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- engineering-craft/test-driven-development \
      -d ~/.claude/skills

# whole category
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- engineering-craft -d ~/.claude/skills/engineering-craft

# glob pattern, flattened by skill name
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- "*bmad*" -d ~/.claude/skills/bmad --flat

# all skills
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- --all -d ~/.claude/skills

# preview what would happen
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- "ai-agents/*" -d ~/.claude/skills/ai --dry-run

# discover what's available
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- --list-categories
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- --help
```

**PowerShell (Windows / macOS / Linux):**

```powershell
$content = irm https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1
iex $content

# one skill
Install-Skill engineering-craft/test-driven-development `
              -Dest $HOME\.claude\skills

# whole category
Install-Skill engineering-craft -Dest $HOME\.claude\skills\engineering-craft

# glob pattern, flattened by skill name
Install-Skill "*bmad*" -Dest $HOME\.claude\skills\bmad -Flat

# all skills
Install-Skill -All -Dest $HOME\.claude\skills

# preview what would happen
Install-Skill "ai-agents/*" -Dest $HOME\.claude\skills\ai -DryRun

# discover what's available
Install-Skill -ListCategories
Install-Skill -List
Install-Skill -Help              # full Get-Help output
```

**Flags (both installers):**

| bash | PowerShell | Purpose |
| --- | --- | --- |
| `-d <path>` | `-Dest <path>` | destination (required) |
| `--branch <name>` | `-Branch <name>` | install from a non-default branch |
| `--force` | `-Force` | overwrite existing destinations |
| `--flat` | `-Flat` | glob mode: place each skill at `<dest>/<name>/` instead of preserving install paths (errors on collision) |
| `--all` | `-All` | install every skill, preserving category paths |
| `--dry-run` | `-DryRun` | resolve selector and print plan only |
| `--list` | `-List` | list every skill, grouped by category |
| `--list-categories` | `-ListCategories` | list categories with skill counts |
| `-h` / `--help` | `-Help` | show usage |

Override the source repo / branch with the `SKILLS_REPO` and `SKILLS_BRANCH` env vars. Use `SKILLS_DOWNLOAD_BASE` to point installers at an alternate public ZIP artifact base; the default is discovered from the published ZIP summary and falls back to GitHub Pages.

#### Option B — `degit` (requires Node.js, single skill or folder)

```bash
# one skill
npx degit mouadja02/skills/skills/engineering-craft/test-driven-development \
  ~/.claude/skills/test-driven-development

# whole category
npx degit mouadja02/skills/skills/engineering-craft \
  ~/.claude/skills/engineering-craft
```

#### Option C — `git sparse-checkout` (git only)

```bash
git clone --no-checkout --depth 1 --filter=blob:none \
  https://github.com/mouadja02/skills.git skills-tmp
cd skills-tmp
git sparse-checkout init --cone
git sparse-checkout set skills/engineering-craft/test-driven-development
git checkout
mv skills/engineering-craft/test-driven-development \
  ~/.claude/skills/test-driven-development
cd .. && rm -rf skills-tmp
```

#### Option D — direct `.zip` download

Every skill, every category, and the full library are published as downloadable `.zip` files on the
Pages site. No tools required — click the **`↓ .zip`** button on any card,
or grab a stable URL:

```text
https://mouadja02.github.io/skills/zips/skill/<install-path>.zip
https://mouadja02.github.io/skills/zips/category/<category>.zip
https://mouadja02.github.io/skills/zips/all.zip
```

Examples:

```bash
curl -LO https://mouadja02.github.io/skills/zips/skill/engineering-craft/test-driven-development.zip
unzip test-driven-development.zip -d ~/.claude/skills/

curl -LO https://mouadja02.github.io/skills/zips/category/ai-agents.zip
unzip ai-agents.zip -d ~/.claude/skills/
```

Each zip unpacks to a single named folder ready to drop into your skills
directory. A machine-readable index of every zip (URL + size + SHA-256) lives at
`https://mouadja02.github.io/skills/zips/_summary.json`.

#### Option E — full clone

If you want everything at once:

```bash
git clone https://github.com/mouadja02/skills.git
cp -r skills/skills/* ~/.claude/skills/
```

### Machine-readable index

Every skill's `name`, `description`, `category`, and `install_path` lives in
[`docs/manifest.json`](./docs/manifest.json) (and a tab-separated
[`docs/manifest.tsv`](./docs/manifest.tsv) for shell tools). Two ways to
fetch it:

```bash
# from a clone:
node scripts/build-manifest.mjs           # regenerate locally

# from anywhere:
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/docs/manifest.json
curl -fsSL https://mouadja02.github.io/skills/manifest.json
```

The CI workflow at
[`.github/workflows/build-manifest.yml`](./.github/workflows/build-manifest.yml)
regenerates it on every push that touches a `SKILL.md`.

### Setup: GitHub Pages (one-time)

To publish the searchable index at `https://<user>.github.io/skills/`:

1. **Settings → Pages** → *Source*: **GitHub Actions**.
2. Push any change to `main`. The
   [`Deploy Pages`](./.github/workflows/deploy-pages.yml) workflow builds
   the manifest, generates per-skill, per-category, and all-skills `.zip`
   archives into `docs/zips/`, then uploads `docs/` as the Pages artifact.
3. Wait ~1 minute for the first deploy.

`docs/zips/` is `.gitignore`d — the archives only exist inside the Pages
artifact, so the main branch stays lean.

---

## Categories

The 258 skills (counting nested sub-skills as their own installable units)
are grouped into 13 thematic categories. Click any category to see its full
per-skill table; counts come from the auto-generated
[`docs/manifest.json`](./docs/manifest.json).

| Category | Skills | What lives here |
| --- | --- | --- |
| [**`skill-authoring/`**](./skills/skill-authoring/) | 2 | Building, editing, and benchmarking the skills themselves. |
| [**`engineering-craft/`**](./skills/engineering-craft/) | 138 | The disciplined development loop: planning, brainstorming, TDD, debugging, code review, git worktrees, verification — plus senior IC roles (architect, frontend, backend, fullstack, ML, data, QA, PM) and AI-powered code migration. |
| [**`ai-agents/`**](./skills/ai-agents/) | 90 | Designing, scaffolding, and operating AI agents — single and multi-agent, headless and TUI. Includes the **BMad Method** with 30 sub-skills and 6 named personas, the canonical `senior-prompt-engineer`, `mcp-server-builder`, browser automation, durable workflows, local AI stack, and trading agents. |
| [**`context-engineering/`**](./skills/context-engineering/) | 14 | Context windows, compression, persistence, memory frameworks, lost-in-middle mitigation. |
| [**`creative-thinking/`**](./skills/creative-thinking/) | 8 | Bold ideation, lateral thinking, first-principles deconstruction, reverse brainstorming, idea velocity, cognitive frame-shifting, creative constraints, and deep focus productivity. |
| [**`llm-integrations/`**](./skills/llm-integrations/) | 41 | OpenRouter family — TypeScript SDK, model discovery, image generation, OAuth, migration. |
| [**`design-and-ui/`**](./skills/design-and-ui/) | 22 | Frontend craft, design systems, brand identity, themes, banners, narrative portfolio sites. |
| [**`docs-and-presentations/`**](./skills/docs-and-presentations/) | 41 | READMEs, technical docs, ADRs, HTML slides, .pptx files, SVG diagrams. |
| [**`data-and-backend/`**](./skills/data-and-backend/) | 70 | FastAPI + LLM, Snowflake SQL, dbt, ETL-to-dbt migration, Streamlit (with nested sub-skills for charts, dashboards, theming). |
| [**`business-and-strategy/`**](./skills/business-and-strategy/) | 74 | The full C-suite — CEO, CFO, CTO, COO, CPO, CMO, CRO, CISO, CHRO advisors plus chief-of-staff routing, board-meeting protocol, company OS, scenario war room, executive mentor. |
| [**`marketing-and-growth/`**](./skills/marketing-and-growth/) | 25 | A complete marketing operating system — strategy, content, SEO, paid acquisition, copywriting, conversion-rate optimization. |
| [**`devops-and-infrastructure/`**](./skills/devops-and-infrastructure/) | 46 | CI/CD, Docker, Helm, Terraform, AWS, database design, dependency auditing, incident command, observability, Stripe integration, secops. |
| [**`product-management/`**](./skills/product-management/) | 29 | PM toolkit, discovery, **canonical `experiment-designer`** (product *and* marketing A/B), agile delivery, UX research, roadmap communication. |
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
├── README.md                       (you are here)
├── CONTRIBUTING.md                 (how to add or edit a skill)
├── SKILLS.md                       (auto-generated browsable markdown index)
├── package.json                    (devDeps for scripts/*)
├── install.sh                      (one-liner installer for bash/zsh)
├── install.ps1                     (one-liner installer for PowerShell)
│
├── scripts/
│   ├── build-manifest.mjs          (regenerates docs/manifest.{json,tsv} + SKILLS.md)
│   ├── build-zips.mjs              (generates docs/zips/ for the Pages site)
│   └── preview.mjs                 (zero-dep static server for docs/)
│
├── docs/                           (GitHub Pages site — single source of truth)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── manifest.json               (canonical, machine-readable)
│   ├── manifest.tsv                (canonical, tab-separated for shell tools)
│   └── zips/                       (.gitignored — generated by deploy workflow)
│       ├── _summary.json
│       ├── skill/<install_path>.zip
│       └── category/<category>.zip
│
├── .github/workflows/
│   ├── build-manifest.yml          (auto-regenerate manifest on SKILL.md changes)
│   └── deploy-pages.yml            (build + zip + deploy docs/ to Pages)
│
└── skills/
    ├── README.md                   (skills index)
    │
    ├── skill-authoring/             (2)
    ├── engineering-craft/           (35)
    ├── ai-agents/                   (58, includes nested bmm-skills/, claude-skills/, cursor-skills/)
    ├── context-engineering/         (6)
    ├── llm-integrations/            (5)
    ├── design-and-ui/               (10)
    ├── docs-and-presentations/      (7)
    ├── data-and-backend/            (22, includes nested developing-with-streamlit/skills/)
    ├── business-and-strategy/       (61, includes Anthropic exec advisors and BMM business roles)
    ├── marketing-and-growth/        (22)
    ├── devops-and-infrastructure/   (14)
    ├── product-management/          (10)
    └── caveman/                     (6, plus rules/caveman.mdc Cursor rule)
```

## Local development

```bash
npm install                  # one-time
npm run build:manifest       # regenerate docs/manifest.{json,tsv} + SKILLS.md
npm run build:zips           # generate docs/zips/* (requires manifest first)
npm run build                # both, in order
npm run preview              # serve docs/ at http://localhost:4173
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
