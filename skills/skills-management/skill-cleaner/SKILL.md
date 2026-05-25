---
name: skill-cleaner
description: "Audit skills: loaded roots, duplicate skills, unused skills, prompt-budget costs, compact descriptions."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Skill Cleaner

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this when trimming skill prompt budget, finding duplicate skills, auditing enabled/disabled skill roots, or deciding which skills/plugins to remove.

## Workflow

1. Run the analyzer script:

```bash
node --experimental-strip-types skills/skill-cleaner/scripts/skill-cleaner.ts --months 3
```

Useful variants:

```bash
node --experimental-strip-types skills/skill-cleaner/scripts/skill-cleaner.ts --no-logs
node --experimental-strip-types skills/skill-cleaner/scripts/skill-cleaner.ts --months 6 --max-log-mb 800 --deep-logs
node --experimental-strip-types skills/skill-cleaner/scripts/skill-cleaner.ts --context-tokens 272000 --budget-percent 2 --no-logs
node --experimental-strip-types skills/skill-cleaner/scripts/skill-cleaner.ts --root ~/path/to/extra-skills --no-logs
```

2. Read the report in this order:

- **Skill Budget**: context size, 2% skills budget, budgeted usage, and pre-budget full-list pressure.
- **Description candidates**: long descriptions where relaxed grammar saves prompt budget.
- **Duplicates**: same skill name or near-identical description/body across skill roots.
- **Unused candidates**: no recent skill-use trace in logs.
- **Root summary**: where skills came from and whether config marks them disabled.

3. Before deleting or editing:

- Verify the kept copy exists and is loaded.
- Prefer deleting repo-local duplicates when built-ins cover them.
- Preserve trigger nouns in descriptions: product, tool, action, object.

## Analyzer Notes

- Script follows standard frontmatter rules: YAML frontmatter only, default name from parent dir, single-line sanitized `name` and `description`.
- Skill budget: 2% of raw `context_window`, token cost `ceil(utf8_bytes / 4)`, then full descriptions -> equal description truncation -> omitted minimum lines.
- For duplicate names, reports description/body similarity and suggests deletion candidates only when bodies are near copies.
- Usage evidence is heuristic: `$skill`, `Use $skill`, and paths like `skills/<name>/SKILL.md`.

## Output Policy

- Suggest first; edit only when the user asks.
- If asked to apply cleanup, make small grouped commits: descriptions, deletes, config disables.
- Do not delete ignored/untracked skill dirs without naming the destination or confirming they are disposable.
