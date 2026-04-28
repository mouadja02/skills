---
name: project-docs
description: Use when asked to produce technical documentation beyond a README — architecture docs, technical design documents, ADRs, API references, data pipeline docs, onboarding guides, integration specs, or AGENTS.md/CLAUDE.md files. Also use when documenting an AI agent system, a data pipeline, or producing technical reference material for a team. If the output is a technical document other than a README — use this skill.
---

# Project Documentation

Good technical documentation answers the right question for the right reader. Before writing anything, identify: who reads this, what decision or action does it enable, and what's the minimum content needed to enable that?

---

## Documentation Types — Choose the Right One

| Type | Reader | Goal | Format |
|------|--------|------|--------|
| **Architecture Doc** | New engineers, stakeholders | Understand the system at a glance | `ARCHITECTURE.md` |
| **Technical Design Doc (TDD)** | Engineers reviewing a change | Decide whether to approve / how to implement | `docs/design/YYYY-MM-DD-feature.md` |
| **ADR** | Future maintainers | Understand why a decision was made | `docs/decisions/ADR-NNN-title.md` |
| **API Reference** | Developers integrating | Know exactly how to call the API | `docs/api.md` or OpenAPI YAML |
| **Data Pipeline Doc** | Data engineers, analysts | Know what flows where and why | `docs/pipelines/pipeline-name.md` |
| **AGENTS.md / CLAUDE.md** | AI agents working in the repo | Know how to build, test, and navigate the code | `AGENTS.md` at repo root |
| **Onboarding Guide** | New team member | Get from zero to productive | `docs/onboarding.md` |
| **Runbook** | On-call engineer | Diagnose and fix a specific issue | `docs/runbooks/issue-name.md` |

---

## Architecture Document

```markdown
# [Project Name] — Architecture

## Overview
One paragraph: what this system does, for whom, and why it exists.

## System Diagram
[embed SVG or Mermaid diagram here]

## Components

### [Component A]
- **What it does:** one sentence
- **Technology:** Python 3.12 + FastAPI
- **Owned by:** [team or person]
- **Key files:** `backend/main.py`, `services/generator.py`

### [Component B]
...

## Data Flow
1. User uploads a mapping file via the React UI
2. The API receives the file and enqueues a background job
3. The Parser Agent extracts sources and transformations
4. The Generator Agent produces dbt models and YAML
5. Output is stored and the job status is updated

## External Dependencies
| Service | Purpose | Auth |
|---------|---------|------|
| Anthropic API | LLM calls | API key via `ANTHROPIC_API_KEY` |
| Snowflake | Data warehouse | Username + password in `.env` |

## Deployment
[how it runs in production — Docker, cloud, etc.]

## Known Limitations
- [Limitation 1]
- [Limitation 2]
```

---

## Technical Design Document (TDD)

Use before building a significant feature. Write it, share it, get feedback, then build.

```markdown
# [Feature Name] — Technical Design

**Status:** Draft | In Review | Approved | Implemented  
**Author:** [name]  
**Date:** YYYY-MM-DD  
**Reviewers:** [names]

## Problem
What specific problem are we solving? Why does it matter now?

## Goals
- We want to [outcome 1]
- We want to [outcome 2]

## Non-Goals
- We are NOT solving [X] in this change
- [Y] is out of scope

## Proposed Solution
Describe the solution in plain language. Include a diagram if the flow is non-trivial.

### Key Design Decisions
| Decision | Chosen option | Alternatives considered | Reason |
|----------|--------------|------------------------|--------|
| State storage | SQLite | PostgreSQL, Redis | Simplicity — single-server deploy |
| LLM provider | LiteLLM | Direct SDK | Provider-agnostic, easy switching |

### API Changes
[If adding/changing endpoints, document them here]

### Data Model Changes
[Schema changes, new tables/fields]

### Implementation Plan
1. [ ] Phase 1: [what, ~N days]
2. [ ] Phase 2: [what, ~N days]

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM output quality degrades on edge cases | Medium | High | Add eval suite, human review gate |

## Open Questions
- [ ] Should we support XML mappings in v1 or defer to v2?

## References
- [Related PR #123]
- [Relevant doc link]
```

---

## Architecture Decision Record (ADR)

Short, focused, permanent. Captures the why behind an architectural choice.

```markdown
# ADR-001: Use LiteLLM as the LLM abstraction layer

**Date:** 2026-02-15  
**Status:** Accepted  
**Deciders:** [names]

## Context
We need to call LLMs from our Python backend. We currently use Anthropic's Claude, but may switch to or add other providers (OpenAI, Azure, Bedrock) for cost or availability reasons.

## Decision
Use [LiteLLM](https://litellm.ai) as a unified API wrapper over all LLM providers.

## Consequences

**Good:**
- Single interface regardless of provider — switch models by changing a string
- Built-in retry, fallback, rate-limit handling
- Cost tracking and logging built in

**Bad:**
- One more dependency to maintain
- LiteLLM may lag behind provider-specific features (e.g., extended thinking, batch API)

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Direct Anthropic SDK | Too coupled — switching providers requires rewriting call sites |
| LangChain | Too heavy for our use case; adds complexity without value |
| Custom abstraction | Reinventing LiteLLM; maintenance burden |
```

---

## Data Pipeline Documentation

```markdown
# [Pipeline Name] — Data Pipeline

## Purpose
One sentence: what data this moves, from where to where, and why.

## Source
| Property | Value |
|----------|-------|
| System | Salesforce CRM |
| Table | `RAW_DB.SALESFORCE.ACCOUNT` |
| Frequency | Real-time via stream / daily batch |
| Owner | Data Platform team |

## Transformations
1. **Staging** (`stg_salesforce__accounts`) — cast types, rename columns, filter deleted records
2. **Intermediate** (`int_accounts__enriched`) — join with contracts, compute LTV
3. **Mart** (`dim_accounts`) — final shape for BI consumption

## Target
| Property | Value |
|----------|-------|
| Table | `ANALYTICS.MARTS.DIM_ACCOUNTS` |
| Refresh | `dbt run --select dim_accounts` |
| Consumers | Tableau, Finance team SQL queries |

## Data Flow Diagram
[Mermaid or SVG diagram]

## Key Business Rules
- Records with `is_deleted = TRUE` are excluded at staging
- `account_type` is normalized to `['Customer', 'Partner', 'Prospect']`
- LTV is computed as `sum(contract_value)` over the last 24 months

## Monitoring
- dbt source freshness: `dbt source freshness`
- Alert if `DIM_ACCOUNTS` row count drops > 5% day-over-day

## Troubleshooting
| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Missing accounts | Stream offset behind | Check stream lag, re-run staging |
| NULL LTV values | Join on contracts failing | Verify contracts stream freshness |
```

---

## AGENTS.md / CLAUDE.md (AI Agent Context)

This file tells AI agents how to work in your repo. Every project that uses Claude Code or other agents should have one.

```markdown
# Project Context & Agent Guidelines

## What this is
[One paragraph: what the project does]

## Build & Run

### Backend
```bash
pip install -r requirements.txt
uvicorn main:app --reload         # dev server
pytest                            # tests
```

### Frontend
```bash
cd frontend && npm install
npm run dev                       # http://localhost:5173
```

## Key Files
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point |
| `services/generator.py` | Core dbt generation logic |
| `models/requests.py` | Pydantic input schemas |
| `.env.example` | Required environment variables |

## Code Conventions
- Python: PEP 8, type hints on all function signatures, snake_case
- TypeScript: PascalCase for components, camelCase for variables
- All async I/O must use `async/await`
- Secrets never committed — use `.env` only

## Agent Workflow
1. **Read** relevant files before making changes
2. **Plan** changes before implementing (especially for multi-file edits)
3. **Test** after changes: run `pytest` (backend) or `npm run lint` (frontend)
4. **Never** hardcode secrets or API keys
```

---

## Onboarding Guide

```markdown
# [Project Name] — Developer Onboarding

## What you're building
[One paragraph — the product, the users, the problem it solves]

## Architecture in 5 minutes
[Simplified diagram + 3-5 bullet points on how it works]

## Get it running locally

### Prerequisites
- Python 3.12
- Node.js 22 + pnpm
- Docker Desktop

### Steps
```bash
git clone <repo>
cd project
cp .env.example .env
# Fill in .env — ask [name] for the dev credentials
docker compose up --build
```

Open http://localhost:8080 — you should see the UI.

## Where things live
- Business logic: `services/` — start here
- API routes: `routers/`
- Frontend: `apps/web/src/`
- Tests: `tests/`

## First tasks for a new contributor
- [ ] Read this doc top to bottom
- [ ] Run the project locally
- [ ] Run the test suite (`pytest`)
- [ ] Make a trivial change and verify it works

## Who to ask
- Backend questions: [name]
- Data questions: [name]
- Access issues: [name]

## Common gotchas
- `.env` must have `ANTHROPIC_API_KEY` — the app fails silently without it
- Always run from the repo root — relative paths break if you `cd` into a subfolder
- The first `docker compose up` takes ~3 minutes to build; subsequent runs are fast
```

---

## Writing Guidelines

**Write for the reader who has 5 minutes.** They should be able to scan headers and find what they need without reading every word.

**Show, don't describe.** A command that works is worth more than a paragraph explaining what to do.

**Date everything that goes stale.** Design docs, ADRs, and diagrams should have a "last updated" date so readers know whether to trust them.

**One doc, one purpose.** If a doc is trying to do two things (onboarding AND ADR AND API reference), split it.

**Update docs in the same PR as the code change.** Documentation that lags the code is misinformation.
