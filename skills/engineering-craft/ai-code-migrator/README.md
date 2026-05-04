# AI Code Migrator

Systematic, AI-assisted codebase migration at scale. Handles framework upgrades, language conversions, API replacements, and dependency swaps across hundreds of files using a structured 6-phase workflow: analyze → plan → transform → validate → review → ship.

## Quick Start

```typescript
// 1. Analyze scope
const analysis = await analyzeMigration('./src', 'React class components', 'React hooks', llm);
// → { affectedFiles: 147, complexity: 'moderate', estimatedTime: '2h' }

// 2. Generate migration rules
const rules = await generateMigrationPlan(analysis, llm);

// 3. Apply file-by-file in batches
await migrateBatch(analysis.affectedFiles, rules, llm);
```

## Supported Migrations

| From | To | Complexity |
|---|---|---|
| React class components | React hooks | Moderate |
| Vue 2 | Vue 3 Composition API | Complex |
| JavaScript | TypeScript | Moderate |
| CommonJS (`require`) | ESM (`import`) | Trivial |
| Webpack | Vite | Moderate |
| Next.js 13 | Next.js 15 | Complex |
| Moment.js | date-fns | Trivial |
| REST APIs | GraphQL | Complex |

## Workflow Phases

1. **Analyze** — scan codebase for patterns, estimate scope and risks
2. **Plan** — generate consistent migration rules with before/after examples
3. **Transform** — apply changes file-by-file with LLM, preserving formatting
4. **Validate** — run lint, typecheck, tests, build after each batch
5. **Review** — human review of edge cases and TODO comments
6. **Ship** — atomic commits, max 20 files per PR

## Installation

### Claude Code

```bash
cp -R engineering-craft/ai-code-migrator ~/.claude/skills/ai-code-migrator
```

### Cursor

```bash
cp -R engineering-craft/ai-code-migrator ~/.cursor/skills/ai-code-migrator
```
