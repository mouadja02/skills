# Durable Agent Workflows

Design and build fault-tolerant AI agent workflows that survive crashes, resume from checkpoints, and include human-in-the-loop approval gates. Covers Temporal, Inngest, and lightweight DIY checkpoint patterns.

## Quick Start

```typescript
// Temporal: each step is automatically retried and checkpointed
const plan = await callLLM({ prompt: `Research plan for: ${topic}` });
const sources = await Promise.all(plan.queries.map(q => searchWeb(q)));
const approved = await notifyHuman({ message: 'Proceed?', timeout: '24h' });
const report = await callLLM({ prompt: `Synthesize: ${JSON.stringify(sources)}` });
```

## Core Patterns

- **Temporal workflows** — deterministic orchestration with automatic retry, checkpointing, and a built-in observability UI
- **Inngest (serverless)** — event-driven steps with `waitForEvent` for human-in-the-loop gates
- **DIY checkpoint** — lightweight SQLite/Redis-backed step-level persistence with exponential backoff retry
- **Structured logging** — per-step token usage, cost tracking, and workflow-level observability
- **Error classification** — retryable vs non-retryable errors, cost circuit breakers, timeout management

## Decision Matrix

| Requirement | Temporal | Inngest | DIY Checkpoint |
|---|---|---|---|
| Self-hosted | ✅ | ❌ (cloud) | ✅ |
| Serverless | ❌ | ✅ | ⚠️ |
| Human-in-loop | ✅ (signals) | ✅ (waitForEvent) | Manual |
| Best for | Enterprise | Startups | MVPs |

## Installation

### Claude Code

```bash
cp -R ai-agents/durable-agent-workflows ~/.claude/skills/durable-agent-workflows
```

### Cursor

```bash
cp -R ai-agents/durable-agent-workflows ~/.cursor/skills/durable-agent-workflows
```
