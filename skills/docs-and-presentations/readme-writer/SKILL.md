---
name: readme-writer
description: Use when asked to write, generate, update, or improve a README.md, add documentation to a project root, or create an onboarding document for a repository. Also use when the user says "document this project", "write the docs", or "create a README" for a Python tool, FastAPI backend, React app, CLI, dbt project, monorepo, or AI agent system. If the output is a README.md — use this skill.
---

# README Writer

A great README answers four questions in order: what is this, why should I care, how do I run it, how do I use it. Everything else is optional — include it only if a new contributor would be blocked without it.

---

## Before Writing

Read these first — don't guess:
- `package.json` / `pyproject.toml` / `requirements.txt` — project name, dependencies, scripts
- `docker-compose.yml` — services, ports, env vars
- `AGENTS.md` / `CLAUDE.md` — existing docs to not duplicate
- Main entry point (e.g., `main.py`, `src/index.ts`) — what it actually does
- `.env.example` — what config is needed

---

## Structure by Project Type

### Python Tool / CLI

```markdown
# project-name

One sentence: what it does and why you'd use it.

## Features
- Bullet of main capability 1
- Bullet of main capability 2

## Requirements
- Python 3.11+
- `pip install -r requirements.txt`

## Setup
```bash
cp .env.example .env
# Edit .env: set API_KEY=...
pip install -r requirements.txt
```

## Usage
```bash
python main.py --input mapping.json --output ./dbt_project/
```

## Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | — | Required. Your LLM API key |
| `MODEL` | `claude-sonnet-4-6` | LLM model to use |

## Project Structure
```
src/
├── parser.py       # Reads input files
├── generator.py    # Generates output
└── main.py         # Entry point
```
```

---

### FastAPI Backend

```markdown
# project-name

One sentence.

## Stack
- Python 3.12 + FastAPI
- [LiteLLM / Anthropic SDK]
- Docker

## Quick Start
```bash
cp .env.example .env
docker compose up --build
```
API available at http://localhost:8000 · Docs at http://localhost:8000/docs

## API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate` | Submit a mapping for generation |
| `GET` | `/api/v1/jobs/{id}` | Check job status |
| `GET` | `/health` | Health check |

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `DATABASE_URL` | No | SQLite path (default: `./db.sqlite`) |

## Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Run tests: `pytest`
```

---

### React / Vite Frontend

```markdown
# project-name

One sentence.

## Tech
Vite + React 18 + TypeScript + Tailwind CSS

## Start
```bash
pnpm install
pnpm dev        # http://localhost:5173
```

## Build
```bash
pnpm build
pnpm preview
```

## Environment
Copy `.env.example` to `.env`:
```
VITE_API_URL=http://localhost:3000
```
```

---

### Monorepo (pnpm workspaces)

```markdown
# project-name

One sentence about the overall system.

## Architecture
```
apps/
├── web/        # React frontend (port 5173)
├── api/        # Fastify API (port 3000)
└── renderer/   # Worker
packages/
├── shared/     # Shared TypeScript types
└── prompt/     # AI prompt builder
```

## Quick Start
```bash
pnpm install
pnpm dev          # starts all services
```

Or with Docker:
```bash
docker compose up --build   # http://localhost:8080
```

## Services
| Service | Port | Description |
|---------|------|-------------|
| web | 5173 | React UI |
| api | 3000 | REST + WebSocket API |
| nginx | 8080 | Reverse proxy |

## Development
Each app has its own `pnpm dev` — run from root to start all, or `cd apps/web && pnpm dev` for just one.

## Environment
Copy `.env.example` → `.env`. Required:
- `ANTHROPIC_API_KEY` — for AI generation
```

---

### dbt Project

```markdown
# project-name

dbt project for [company/domain] on Snowflake.

## Data Sources
| Source | Schema | Description |
|--------|--------|-------------|
| `salesforce` | `RAW_DB.SALESFORCE` | CRM data |
| `oms` | `RAW_DB.OMS` | Order management |

## Models
```
models/
├── staging/     # 1:1 source casts
├── intermediate/# Business logic joins
└── marts/
    ├── core/    # Shared dimensions and facts
    └── finance/ # Finance-specific models
```

## Setup
```bash
pip install dbt-snowflake
cp profiles.yml.example ~/.dbt/profiles.yml
dbt deps
dbt debug
```

## Run
```bash
dbt run                          # all models
dbt run --select tag:daily       # daily models only
dbt test                         # run all tests
dbt docs generate && dbt docs serve
```
```

---

### AI Agent / Tool

```markdown
# project-name

One sentence: what the agent does, what it takes as input, what it produces.

## How it works
1. **Parse** — reads [input format]
2. **Plan** — [what the agent decides]
3. **Generate** — produces [output format]
4. **Validate** — [how output is checked]

## Usage
```bash
python agent.py --input path/to/mapping.json --output ./output/
```

## Input Format
[describe expected input structure]

## Output
[describe what is produced and where]

## Configuration
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required |
| `MODEL` | Default: `claude-sonnet-4-6` |
```

---

## Writing Rules

**Lead with the value, not the name.** The first sentence should tell a stranger what problem this solves. Not "This is a tool for..." — just what it does.

**Assume nothing is installed.** A new person should be able to copy-paste from Quick Start and have something running. Every command must work.

**Use real examples.** Show actual command output, actual file names, actual API responses — not `<your-value-here>` placeholders in the usage section.

**Keep it honest.** If something is broken, in progress, or requires manual steps, say so. A README that lies is worse than no README.

**Don't over-document.** Omit sections that don't apply. A 50-line README that covers what matters beats a 500-line one that includes auto-generated API docs for internal helpers.

**Badges are optional.** Add CI/CD status badge if CI exists. Skip the vanity badges.

---

## Markdown Formatting Conventions

```markdown
# Project Name          ← H1: project name only, once
## Section              ← H2: major sections
### Subsection          ← H3: variants within a section

`inline code`           ← for file names, env vars, values
```code block```        ← for any command or code snippet — always specify language

**bold**                ← for emphasis on important terms
> Note: ...             ← for callouts / warnings

| Col | Col |           ← tables for config vars, endpoints, services
```

## Tone

Write for someone who has never seen this project. Be direct and practical. Skip filler phrases ("This powerful tool..."). Every sentence should convey information a reader needs.
