---
name: "durable-agent-workflows"
description: "Design and build durable, fault-tolerant AI agent workflows using Temporal, Inngest, or event-driven patterns. Use when the user wants to build long-running agent pipelines, implement retry logic for LLM calls, create resumable agent workflows, orchestrate multi-step AI tasks that survive crashes, handle agent state persistence across sessions, build production-grade agent infrastructure with observability, or implement human-in-the-loop approval nodes in agent graphs."
---

# Durable Agent Workflows

**Tier:** POWERFUL
**Category:** AI Agents
**Domain:** Workflow Orchestration / Agent Infrastructure / Reliability Engineering

## Overview

Production AI agents fail constantly — LLM rate limits, timeouts, network errors, context overflows. This skill covers building agent workflows that are **durable** (survive crashes), **observable** (you can see what's happening), and **recoverable** (resume from any checkpoint). It bridges the gap between prototype agents and production infrastructure.

## When to Use

- Agent pipelines that run for minutes/hours and must not lose state
- Multi-step LLM workflows that need automatic retry with backoff
- Human-in-the-loop approval gates in autonomous agent pipelines
- Agent orchestration that must survive process restarts/deployments
- Long-running research or analysis agents that checkpoint progress
- Multi-agent systems that need coordination and state isolation
- Any agent system going from prototype to production reliability

## Core Concepts

### The Durability Problem

```
❌ Naive Agent (dies on failure):
  Step 1 ✓ → Step 2 ✓ → Step 3 ✓ → Step 4 💥 → ALL LOST

✅ Durable Agent (resumes from checkpoint):
  Step 1 ✓ → Step 2 ✓ → Step 3 ✓ → Step 4 💥
  [restart] → Step 4 ✓ → Step 5 ✓ → Done ✓
```

### Architecture Patterns

#### Pattern 1: Temporal Workflow (Recommended for Production)

```typescript
// workflow.ts — deterministic orchestration
import { proxyActivities, sleep } from '@temporalio/workflow';
import type * as activities from './activities';

const { callLLM, searchWeb, writeDocument, notifyHuman } = proxyActivities<typeof activities>({
  startToCloseTimeout: '5 minutes',
  retry: {
    maximumAttempts: 3,
    initialInterval: '2 seconds',
    backoffCoefficient: 2,
    maximumInterval: '30 seconds',
    nonRetryableErrorTypes: ['InvalidPromptError', 'ContentPolicyError'],
  },
});

export async function researchAgent(topic: string): Promise<ResearchReport> {
  // Step 1: Plan research (auto-retried on failure)
  const plan = await callLLM({
    prompt: `Create research plan for: ${topic}`,
    model: 'claude-sonnet-4-20250514',
  });

  // Step 2: Execute research in parallel
  const sources = await Promise.all(
    plan.queries.map(q => searchWeb(q))
  );

  // Step 3: Human approval gate
  const approved = await notifyHuman({
    message: `Found ${sources.length} sources. Proceed?`,
    timeout: '24 hours',
  });
  if (!approved) throw new Error('Research rejected by human');

  // Step 4: Generate report
  const report = await callLLM({
    prompt: `Synthesize report from: ${JSON.stringify(sources)}`,
    model: 'claude-sonnet-4-20250514',
  });

  return report;
}
```

```typescript
// activities.ts — side-effectful operations (non-deterministic)
export async function callLLM(params: LLMParams): Promise<any> {
  const response = await openai.chat.completions.create({
    model: params.model,
    messages: [{ role: 'user', content: params.prompt }],
  });
  return JSON.parse(response.choices[0].message.content);
}

export async function searchWeb(query: string): Promise<SearchResult[]> {
  // Actual HTTP call — Temporal handles retries
  return await tavilyClient.search(query);
}
```

#### Pattern 2: Event-Driven with Inngest (Serverless-Friendly)

```typescript
import { Inngest } from 'inngest';
const inngest = new Inngest({ id: 'agent-pipeline' });

export const agentWorkflow = inngest.createFunction(
  { id: 'research-agent', retries: 3 },
  { event: 'agent/research.start' },
  async ({ event, step }) => {
    // Each step is automatically checkpointed
    const plan = await step.run('create-plan', async () => {
      return await callLLM(`Plan research for: ${event.data.topic}`);
    });

    const sources = await step.run('gather-sources', async () => {
      return await Promise.all(plan.queries.map(searchWeb));
    });

    // Wait for human approval (up to 7 days)
    const approval = await step.waitForEvent('wait-for-approval', {
      event: 'agent/research.approved',
      timeout: '7d',
      match: 'data.workflowId',
    });

    if (!approval) throw new Error('Timed out waiting for approval');

    const report = await step.run('generate-report', async () => {
      return await callLLM(`Synthesize: ${JSON.stringify(sources)}`);
    });

    return report;
  }
);
```

#### Pattern 3: DIY Checkpoint System (Lightweight)

```typescript
interface Checkpoint {
  workflowId: string;
  step: number;
  state: any;
  createdAt: Date;
}

class DurableWorkflow {
  constructor(
    private db: Database, // SQLite, Redis, etc.
    private workflowId: string
  ) {}

  async runStep<T>(name: string, fn: () => Promise<T>): Promise<T> {
    // Check if step already completed
    const existing = await this.db.get(
      `SELECT result FROM checkpoints WHERE workflow_id = ? AND step_name = ?`,
      [this.workflowId, name]
    );
    if (existing) return JSON.parse(existing.result);

    // Execute and checkpoint
    const result = await this.retryWithBackoff(fn, 3);
    await this.db.run(
      `INSERT INTO checkpoints (workflow_id, step_name, result) VALUES (?, ?, ?)`,
      [this.workflowId, name, JSON.stringify(result)]
    );
    return result;
  }

  private async retryWithBackoff<T>(fn: () => Promise<T>, maxRetries: number): Promise<T> {
    for (let i = 0; i < maxRetries; i++) {
      try { return await fn(); }
      catch (e) {
        if (i === maxRetries - 1) throw e;
        await sleep(Math.pow(2, i) * 1000);
      }
    }
    throw new Error('Unreachable');
  }
}
```

## Observability

### Structured Logging for Agent Steps

```typescript
function agentLogger(workflowId: string) {
  return {
    step(name: string, data: any) {
      console.log(JSON.stringify({
        ts: new Date().toISOString(),
        workflow: workflowId,
        event: 'step.start',
        step: name,
        ...data,
      }));
    },
    llmCall(model: string, tokens: { input: number; output: number }, cost: number) {
      console.log(JSON.stringify({
        ts: new Date().toISOString(),
        workflow: workflowId,
        event: 'llm.call',
        model, tokens, cost,
      }));
    },
  };
}
```

## Decision Matrix

| Requirement | Temporal | Inngest | DIY Checkpoint |
|---|---|---|---|
| Self-hosted | ✅ | ❌ (cloud) | ✅ |
| Serverless | ❌ | ✅ | ⚠️ |
| Human-in-loop | ✅ (signals) | ✅ (waitForEvent) | Manual |
| Observability | ✅ (UI built-in) | ✅ (dashboard) | Manual |
| Complexity | High | Medium | Low |
| Best for | Enterprise | Startups/Serverless | MVPs |

## Common Pitfalls

1. **Non-deterministic workflow code** — Keep LLM calls in activities, not workflow body
2. **No idempotency** — Activities must be safe to retry (use idempotency keys)
3. **Unbounded retries** — Always set max attempts and non-retryable error types
4. **Missing cost tracking** — Log token usage per step; set cost circuit breakers
5. **No timeout on human gates** — Always set timeouts on approval steps
6. **State too large** — Don't checkpoint entire LLM responses; store summaries
