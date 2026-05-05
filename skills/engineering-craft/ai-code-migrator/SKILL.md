---
name: "ai-code-migrator"
description: "Automate large-scale codebase migrations using AI — framework upgrades, language conversions, API modernization, and dependency swaps. Use when the user wants to migrate from one framework to another (React class→hooks, Vue 2→3, Angular→React, Express→Fastify, Python 2→3), upgrade major library versions (Next.js 13→15, Webpack→Vite), convert between languages (JavaScript→TypeScript, Python→Rust), modernize legacy codebases, replace deprecated APIs, or perform any systematic code transformation across hundreds of files."
---

# AI Code Migrator

**Tier:** POWERFUL
**Category:** Engineering Craft
**Domain:** Code Modernization / Migration / Refactoring

## Overview

Systematic, AI-assisted codebase migration at scale. Instead of manual find-and-replace or brittle codemods, this skill uses a structured workflow: analyze → plan → transform → validate → commit. It handles framework upgrades, language conversions, API replacements, and dependency swaps across hundreds or thousands of files.

## When to Use

- Framework upgrades: React class→hooks, Vue 2→3, Next.js 13→15, Angular→React
- Build tool migration: Webpack→Vite, CRA→Vite, Gulp→modern tooling
- Language conversion: JavaScript→TypeScript, Python 2→3, CommonJS→ESM
- Library swaps: Moment.js→date-fns, Redux→Zustand, REST→GraphQL
- API modernization: callback→async/await, XMLHttpRequest→fetch
- Deprecation cleanup: removing deprecated APIs across entire codebase
- Any systematic transformation that touches 10+ files

## Migration Workflow

```
Phase 1: ANALYZE        Phase 2: PLAN           Phase 3: TRANSFORM
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ Scan codebase│ ──────→ │ Generate     │ ──────→ │ Apply changes│
│ for patterns │         │ migration    │         │ file by file │
│ to migrate   │         │ plan + rules │         │ with LLM     │
└─────────────┘         └─────────────┘         └─────────────┘
                                                       │
Phase 6: SHIP           Phase 5: REVIEW         Phase 4: VALIDATE
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ Commit in    │ ←────── │ Human review │ ←────── │ Run tests,   │
│ atomic PRs   │         │ edge cases   │         │ lint, build   │
└─────────────┘         └─────────────┘         └─────────────┘
```

## Phase 1: Analyze

Scan the codebase to understand migration scope:

```typescript
interface MigrationAnalysis {
  totalFiles: number;
  affectedFiles: string[];
  patterns: PatternMatch[];
  complexity: 'trivial' | 'moderate' | 'complex' | 'requires-manual';
  estimatedTime: string;
  risks: string[];
  breakingChanges: string[];
}

async function analyzeMigration(
  rootDir: string,
  from: string,
  to: string,
  llm: LLMClient
): Promise<MigrationAnalysis> {
  // 1. Find all affected files
  const files = await glob(`${rootDir}/**/*.{ts,tsx,js,jsx}`, { ignore: 'node_modules' });
  
  // 2. Detect patterns that need migration
  const patterns: PatternMatch[] = [];
  for (const file of files) {
    const content = await readFile(file, 'utf-8');
    const matches = await llm.complete(`
      Identify all ${from} patterns in this file that need migration to ${to}.
      File: ${file}
      Content: ${content.slice(0, 8000)}
      Return JSON: [{ line, pattern, complexity, migrationStrategy }]
    `);
    patterns.push(...JSON.parse(matches).map(m => ({ ...m, file })));
  }
  
  return {
    totalFiles: files.length,
    affectedFiles: [...new Set(patterns.map(p => p.file))],
    patterns,
    complexity: calculateComplexity(patterns),
    estimatedTime: estimateTime(patterns),
    risks: identifyRisks(patterns),
    breakingChanges: findBreakingChanges(from, to),
  };
}
```

## Phase 2: Plan

Generate migration rules that ensure consistency:

```typescript
interface MigrationRule {
  name: string;
  description: string;
  before: string;   // pattern/example
  after: string;    // replacement/example
  scope: 'auto' | 'manual-review';
  testCommand?: string;
}

async function generateMigrationPlan(
  analysis: MigrationAnalysis,
  llm: LLMClient
): Promise<MigrationRule[]> {
  const rules = await llm.complete(`
    Generate migration rules for: ${analysis.patterns.length} patterns.
    Migration: ${JSON.stringify(analysis.patterns.slice(0, 20))}
    
    For each unique pattern type, create a rule with:
    - name: kebab-case identifier
    - description: what it transforms
    - before: example of old code
    - after: example of new code  
    - scope: "auto" if safe, "manual-review" if risky
    
    Return JSON array of rules.
  `);
  return JSON.parse(rules);
}
```

## Phase 3: Transform

Apply changes file-by-file with the LLM:

```typescript
async function migrateFile(
  filePath: string,
  rules: MigrationRule[],
  llm: LLMClient
): Promise<{ original: string; migrated: string; changes: string[] }> {
  const original = await readFile(filePath, 'utf-8');
  
  const migrated = await llm.complete(`
    Apply these migration rules to the file:
    Rules: ${JSON.stringify(rules)}
    
    Original file (${filePath}):
    ${original}
    
    Requirements:
    - Apply ALL matching rules
    - Preserve comments, formatting, whitespace style
    - Do NOT change logic unrelated to migration
    - Add TODO comments for ambiguous cases
    - Return ONLY the migrated file content
  `);
  
  return {
    original,
    migrated,
    changes: diffLines(original, migrated),
  };
}

// Process in batches to manage LLM costs
async function migrateBatch(files: string[], rules: MigrationRule[], llm: LLMClient) {
  const BATCH_SIZE = 5;
  const results = [];
  
  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const batch = files.slice(i, i + BATCH_SIZE);
    const batchResults = await Promise.all(
      batch.map(f => migrateFile(f, rules, llm))
    );
    results.push(...batchResults);
    
    // Checkpoint progress
    await saveCheckpoint({ completed: i + BATCH_SIZE, total: files.length });
    console.log(`Migrated ${Math.min(i + BATCH_SIZE, files.length)}/${files.length}`);
  }
  return results;
}
```

## Phase 4: Validate

```bash
# Automated validation pipeline
npm run lint          # Ensure no syntax errors introduced
npm run typecheck     # TypeScript compilation passes
npm run test          # All existing tests still pass
npm run build         # Production build succeeds
```

## Common Migration Recipes

### React Class → Hooks
```
Rules: class→function, this.state→useState, componentDidMount→useEffect,
       this.props→destructured params, this.setState→setter functions
```

### CommonJS → ESM
```
Rules: require()→import, module.exports→export default,
       exports.x→export const x, __dirname→import.meta.dirname
```

### JavaScript → TypeScript
```
Rules: .js→.ts/.tsx, add type annotations, add interfaces for props,
       add return types, replace any with proper types
```

### Webpack → Vite
```
Rules: webpack.config.js→vite.config.ts, remove loaders→use plugins,
       process.env→import.meta.env, require.context→import.meta.glob
```

## Best Practices

1. **Migrate in atomic commits** — One logical change per commit, not one file per commit
2. **Keep tests passing at every step** — Never batch-commit untested changes
3. **Start with low-risk files** — Migrate utility files first, complex components last
4. **Preserve git blame** — Use `git mv` for renames, separate refactors from renames
5. **Feature-flag the migration** — Run old and new code paths in parallel when possible
6. **Track migration progress** — Maintain a checklist of files/patterns remaining
7. **Set an LLM cost budget** — Large migrations can consume significant tokens

## Pitfalls

1. **Migrating without tests** — Add tests BEFORE migrating if none exist
2. **One giant PR** — Break into reviewable chunks (max 20 files per PR)
3. **Not handling edge cases** — LLMs miss ~5% of patterns; always validate
4. **Changing behavior during migration** — Migration should be behavior-preserving
5. **No rollback plan** — Use feature branches; don't migrate on main
