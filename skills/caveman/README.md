# caveman

**Token-efficiency mode** — terse responses that cut output tokens ~75% while preserving full technical accuracy. The caveman family is meant for power users who want fewer pleasantries and more signal, plus a small set of skill-discovery tools that sit naturally alongside it.

## Skills in this category

### Caveman mode

| Skill | What it does |
| --- | --- |
| [`caveman`](./caveman/SKILL.md) | The main mode. Activates terse responses with intensity levels: `lite`, `full` (default), `ultra`, `wenyan-lite`, `wenyan-full`, `wenyan-ultra`. Triggers: "caveman mode", "talk like caveman", "use caveman", `/caveman`. Auto-triggers when token efficiency is requested. |
| [`caveman-help`](./caveman-help/SKILL.md) | Quick-reference card for all caveman modes, skills, and commands. One-shot display, not a persistent mode. |

### Specialized caveman applications

| Skill | What it does |
| --- | --- |
| [`caveman-compress`](./caveman-compress/SKILL.md) | Compress natural-language memory files (`CLAUDE.md`, todos, preferences) into caveman format to reduce input tokens. Preserves all technical substance, code, URLs, and structure. Saves a `.original.md` backup. Triggers on `/caveman:compress` or "compress memory file". |
| [`caveman-commit`](./caveman-commit/SKILL.md) | Generate ultra-compressed commit messages — Conventional Commits format, subject ≤ 50 chars, body only when "why" isn't obvious. Triggers on "write a commit", "commit message", `/commit`. |
| [`caveman-review`](./caveman-review/SKILL.md) | Ultra-compressed PR/code-review comments — one line per finding (`location, problem, fix`), no throat-clearing. Triggers on "review this PR", "code review", `/review`. |

### Companion utilities

| Skill | What it does |
| --- | --- |
| [`find-skills`](./find-skills/SKILL.md) | Discover and install agent skills from the open ecosystem when the user asks "how do I do X", "is there a skill that can…", or expresses interest in extending capabilities. |

## Cursor rule

The `rules/caveman.mdc` file is a Cursor rule (not a skill) that pins caveman mode on globally when `alwaysApply: true`. Move it into your `.cursor/rules/` directory to activate.

## When to use this folder

- "Be brief / use less tokens"
- "Caveman mode" / "talk like caveman" / `/caveman`
- "Compress my memory file" — `caveman-compress`
- "Write a commit message" — `caveman-commit`
- "Review this PR" — `caveman-review`
- "Find a skill that does X" — `find-skills`

## Related categories

- [`context-engineering/`](../context-engineering/) — broader context-window strategies (compression, persistence, memory). Caveman is a *style*; `context-engineering` is the *architecture*.
- [`engineering-craft/requesting-code-review`](../engineering-craft/requesting-code-review/) and [`receiving-code-review`](../engineering-craft/receiving-code-review/) — code-review craft (Caveman just trims the output).
- [`skill-authoring/`](../skill-authoring/) — `find-skills` complements the skill-creation skills there.
