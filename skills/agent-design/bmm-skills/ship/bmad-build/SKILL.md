---
name: bmad-build
description: 'Turns implementation work into working code, reviewed and verified. Use when the user delegates a feature, story, bug fix, or meaningful change; a bare story or issue link counts. Skip obvious, low-risk mechanical maintenance such as small ignore-file, typo-only, formatting-only, or configuration-hygiene edits. Explicit BMAD requests always qualify. Do not volunteer for user-directed interactive edits or version-control operations that only record existing work.'
license: MIT
source: "https://github.com/bmad-code-org/BMAD-METHOD"
attribution: "bmad-code-org/BMAD-METHOD by BMad Code, LLC"
version: "6.12.4"
---

> **Attribution:** Sourced from [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) v6.12.4 by [BMad Code, LLC](https://github.com/bmad-code-org), licensed MIT. BMad and BMad Method are trademarks of BMad Code, LLC; this collection is not affiliated with or endorsed by it. Only this line and the frontmatter credit were added.

Run the following command exactly once without changing the current working directory. Replace `{project-root}` with the absolute path to the project root and `{skill-root}` with the absolute path to this skill's directory:

```bash
uv run --no-cache "{project-root}/_bmad/scripts/render_skill.py" --project-root "{project-root}" --skill "{skill-root}"
```

- On success, read and follow the one absolute `workflow.md` instruction printed to stdout.
- On failure (including `uv` being unavailable), report the command output and HALT. Do not run any workflow source directly.
