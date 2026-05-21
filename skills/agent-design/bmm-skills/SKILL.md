---
name: bmm-skills
description: BMad Method (BMM) — AI-driven agile development framework. Top-level router for the full BMad workflow, organized in 4 phases (Analysis → Planning → Solutioning → Implementation) with 30 sub-skills and 6 named agents (Mary the analyst, Paige the tech writer, John the PM, Sally the UX designer, Winston the architect, Amelia the developer). Use when the user mentions BMad, BMM, BMad Method, "talk to Mary/Paige/John/Sally/Winston/Amelia", PRDs, PRFAQs, product briefs, market/domain/technical research, UX design specs, architecture, epics and stories, sprint planning/status, story implementation, code review, retrospectives, or any phase-tagged ask like "lets create a PRD", "implement the next story", "run a retrospective", "document this project". Loads no workflow content directly — routes to the right sub-skill folder.
---

# BMad Method (BMM) — Master router

This is the top-level entry point for the BMad Method framework installed under `.claude/skills/bmm-skills/`. **It does not contain workflow logic.** Its job is to route the agent to the correct sub-skill folder based on the user's intent and to expose the four-phase mental model.

The framework is organized in four sequential phases. Each phase produces artifacts the next phase consumes:

```
1-analysis/        → discovery, research, problem framing
2-plan-workflows/  → PRDs, UX specs (the "what")
3-solutioning/     → architecture, epics & stories (the "how")
4-implementation/  → story execution, review, sprint tracking (the "ship")
```

Module-level configuration (output folders, user skill level, full agent roster with personas) lives in `module.yaml` at the root of this folder. **Read it once at the start of any BMad session** to load shared variables (`{output_folder}`, `{planning_artifacts}`, `{implementation_artifacts}`, `{project_knowledge}`).

---

## How to use this index

1. Identify the user's intent (use the routing tables below).
2. Open the matching sub-skill's `SKILL.md` and follow its instructions.
3. Each sub-skill self-resolves its own `customize.toml` on activation — you don't need to do that here.
4. Most sub-skills consume artifacts from earlier phases. If the user asks for phase 3 work but phase 2 artifacts are missing, surface that gap first.

**Don't dump the whole framework into context.** Read only the sub-skill that matches the current request, plus any artifacts it needs.

---

## Phase 1 — Analysis (`1-analysis/`)

Discovery, research, and problem framing. Outputs feed the planning phase.

| Trigger | Sub-skill | Read |
|---|---|---|
| "Talk to Mary" / "I need the business analyst" | Persona — Mary | `1-analysis/bmad-agent-analyst/SKILL.md` |
| "Talk to Paige" / "I need the tech writer" | Persona — Paige | `1-analysis/bmad-agent-tech-writer/SKILL.md` |
| "Create a product brief" / "Update my product brief" | Workflow | `1-analysis/bmad-product-brief/SKILL.md` |
| "Create a PRFAQ" / "Work backwards" / "Run the PRFAQ challenge" | Workflow | `1-analysis/bmad-prfaq/SKILL.md` |
| "Document this project" / "Generate project docs" (brownfield) | Workflow | `1-analysis/bmad-document-project/SKILL.md` |
| "Run market research" / "Research my competition" | Workflow | `1-analysis/research/bmad-market-research/SKILL.md` |
| "Run domain research" / "Research this industry" | Workflow | `1-analysis/research/bmad-domain-research/SKILL.md` |
| "Run technical research" / "Research this technology" | Workflow | `1-analysis/research/bmad-technical-research/SKILL.md` |

**Typical entry points:** new green-field idea → `bmad-product-brief` or `bmad-prfaq`; existing codebase the team needs to onboard → `bmad-document-project`.

---

## Phase 2 — Planning (`2-plan-workflows/`)

Turn the analysis into a Product Requirements Document and UX specs. Owned by John (PM) and Sally (UX).

| Trigger | Sub-skill | Read |
|---|---|---|
| "Talk to John" / "I need the product manager" | Persona — John | `2-plan-workflows/bmad-agent-pm/SKILL.md` |
| "Talk to Sally" / "I need the UX designer" | Persona — Sally | `2-plan-workflows/bmad-agent-ux-designer/SKILL.md` |
| "Create a PRD" / "I want a new product requirements doc" | Workflow | `2-plan-workflows/bmad-create-prd/SKILL.md` |
| "Edit this PRD" | Workflow | `2-plan-workflows/bmad-edit-prd/SKILL.md` |
| "Validate this PRD" / "Run PRD validation" | Workflow | `2-plan-workflows/bmad-validate-prd/SKILL.md` |
| "Create UX design" / "Plan the UX" / "Create UX specifications" | Workflow | `2-plan-workflows/bmad-create-ux-design/SKILL.md` |

**Pre-requisites:** a product brief or PRFAQ from phase 1 (not strictly required, but the PRD workflow asks for one).

---

## Phase 3 — Solutioning (`3-solutioning/`)

Translate the PRD + UX into technical architecture, epics and stories, and AI-agent context. Owned by Winston (architect).

| Trigger | Sub-skill | Read |
|---|---|---|
| "Talk to Winston" / "I need the architect" | Persona — Winston | `3-solutioning/bmad-agent-architect/SKILL.md` |
| "Create architecture" / "Create technical architecture" / "Create a solution design" | Workflow | `3-solutioning/bmad-create-architecture/SKILL.md` |
| "Create the epics and stories list" | Workflow | `3-solutioning/bmad-create-epics-and-stories/SKILL.md` |
| "Generate project context" / "Create project context" | Workflow | `3-solutioning/bmad-generate-project-context/SKILL.md` |
| "Check implementation readiness" / "Are we ready to ship?" | Workflow | `3-solutioning/bmad-check-implementation-readiness/SKILL.md` |

**Gate to phase 4:** `bmad-check-implementation-readiness` is the last stop before development. If it surfaces gaps, loop back to phase 2 or 3 to close them.

---

## Phase 4 — Implementation (`4-implementation/`)

Execute approved stories, review, track sprints, retrospect. Owned by Amelia (dev).

| Trigger | Sub-skill | Read |
|---|---|---|
| "Talk to Amelia" / "I need the developer" | Persona — Amelia | `4-implementation/bmad-agent-dev/SKILL.md` |
| "Build / fix / tweak / refactor / add / modify [anything]" — any code intent | Workflow | `4-implementation/bmad-quick-dev/SKILL.md` |
| "Create the next story" / "Create story [id]" | Workflow | `4-implementation/bmad-create-story/SKILL.md` |
| "Implement story [file]" / "Dev this story" / "Implement next story in sprint plan" | Workflow | `4-implementation/bmad-dev-story/SKILL.md` |
| "Run code review" / "Review this code" | Workflow | `4-implementation/bmad-code-review/SKILL.md` |
| "Generate QA tests for [feature]" / "Create automated E2E tests" | Workflow | `4-implementation/bmad-qa-generate-e2e-tests/SKILL.md` |
| "Run sprint planning" / "Generate sprint plan" | Workflow | `4-implementation/bmad-sprint-planning/SKILL.md` |
| "Check sprint status" / "Show sprint status" | Workflow | `4-implementation/bmad-sprint-status/SKILL.md` |
| "Correct course" / "Propose sprint change" | Workflow | `4-implementation/bmad-correct-course/SKILL.md` |
| "Checkpoint" / "Human review" / "Walk me through this change" | Workflow | `4-implementation/bmad-checkpoint-preview/SKILL.md` |
| "Run a retrospective" / "Retro the epic" | Workflow | `4-implementation/bmad-retrospective/SKILL.md` |

**Quick-dev vs. full pipeline:** `bmad-quick-dev` is the catch-all for *any* code change request; it's a hardened single-pass workflow that produces a reviewable artifact. Use it when there is no formal story file. Use `bmad-create-story` → `bmad-dev-story` when the user wants the full BMad pipeline (story spec then implementation).

---

## Agent quick map

The framework defines six named personas. Each lives in a `bmad-agent-*` sub-skill that establishes identity + activation. When the user names an agent, route to the persona skill first; the persona then takes over and may invoke phase workflows.

| Agent | Phase | Role | Persona skill |
|---|---|---|---|
| **Mary** 📊 | 1 | Business Analyst — strategic rigor, evidence-grounded | `1-analysis/bmad-agent-analyst/SKILL.md` |
| **Paige** 📚 | 1 | Technical Writer — CommonMark/DITA/OpenAPI master | `1-analysis/bmad-agent-tech-writer/SKILL.md` |
| **John** 📋 | 2 | Product Manager — Jobs-to-be-Done, user value first | `2-plan-workflows/bmad-agent-pm/SKILL.md` |
| **Sally** 🎨 | 2 | UX Designer — empathy + edge-case rigor | `2-plan-workflows/bmad-agent-ux-designer/SKILL.md` |
| **Winston** 🏗️ | 3 | System Architect — boring tech, trade-offs over verdicts | `3-solutioning/bmad-agent-architect/SKILL.md` |
| **Amelia** 💻 | 4 | Senior Software Engineer — TDD, file paths and AC IDs | `4-implementation/bmad-agent-dev/SKILL.md` |

Full persona descriptions and module configuration (output folders, language settings, user skill level prompts) are in `module.yaml`.

---

## Conventions used by every sub-skill

All BMad sub-skills follow the same path conventions. Note these once and they apply everywhere:

- **Bare paths** (e.g. `references/guide.md`) resolve from the *sub-skill's* root.
- **`{skill-root}`** resolves to the sub-skill's installed directory (where `customize.toml` lives).
- **`{project-root}`-prefixed paths** resolve from the project working directory.
- **`{skill-name}`** resolves to the sub-skill directory's basename.

On activation, every sub-skill resolves its `customize.toml` (with optional team and user overrides under `{project-root}/_bmad/custom/`). If the resolver script is unavailable, the sub-skill's SKILL.md explains how to merge the layers manually (base → team → user, scalars override, tables deep-merge, arrays of tables key-merge, other arrays append).

---

## Routing rules (when in doubt)

1. **Agent name in the prompt?** → load that agent's persona skill, full stop. The persona handles the rest.
2. **Action verb without an agent?** → match the verb to the trigger tables above.
3. **"BMad" / "BMM" / "the framework" without specifics?** → ask one clarifying question: which phase or which artifact (brief, PRD, architecture, story, sprint)?
4. **Code change without ceremony?** → `4-implementation/bmad-quick-dev/SKILL.md` — it's the framework's catch-all.
5. **Multiple matches?** → prefer the deepest, most specific phase. If user says "create a PRD and validate it", read `bmad-create-prd` first; the user can chain `bmad-validate-prd` after.

Don't preload more than one sub-skill at a time. The framework's progressive disclosure depends on it.
