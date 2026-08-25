# Harness Modules

Optional architectural modules that extend the core harness. Each section includes purpose, complete code, and how to wire it into `agent.ts` and `cli.ts`.

## Contents

- [Session Persistence](#session-persistence) — JSONL conversation log (DEFAULT ON)
- [Context Compaction](#context-compaction) — summarize older messages
- [System Prompt Composition](#system-prompt-composition) — dynamic instructions from context files
- [Tool Approval](#tool-approval) — gate mutating tools behind user confirmation (ON by default)
- [Structured Event Logging](#structured-event-logging) — emit events for observability

---

## Session Persistence

JSONL (newline-delimited JSON) append-only log for crash-safe conversation persistence. Pattern from pi-mono's session manager.

### src/session.ts

```typescript
import { appendFileSync, readFileSync, existsSync, mkdirSync, readdirSync } from 'fs';
import { join } from 'path';

type Message = { role: string; content: string; [key: string]: unknown };

interface SessionEntry {
  timestamp: string;
  message: Message;
}

export function initSessionDir(dir: string): void {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

export function saveMessage(sessionPath: string, message: Message): void {
  const entry: SessionEntry = {
    timestamp: new Date().toISOString(),
    message,
  };
  appendFileSync(sessionPath, JSON.stringify(entry) + '\n');
}

export function loadSession(sessionPath: string): Message[] {
  if (!existsSync(sessionPath)) return [];

  return readFileSync(sessionPath, 'utf-8')
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      try {
        const entry: SessionEntry = JSON.parse(line);
        return entry.message;
      } catch {
        return null;
      }
    })
    .filter((m): m is Message => m !== null);
}

export function listSessions(dir: string): string[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith('.jsonl'))
    .sort();
}

export function newSessionPath(dir: string): string {
  const id = new Date().toISOString().replace(/[:.]/g, '-');
  return join(dir, `${id}.jsonl`);
}
```

### Integration

In `cli.ts`, wrap the message loop:

```typescript
import { initSessionDir, loadSession, saveMessage, newSessionPath } from './session.js';

// At startup:
initSessionDir(config.sessionDir);
const sessionPath = newSessionPath(config.sessionDir);
const messages = loadSession(sessionPath); // empty for new, or pass existing path

// In the REPL loop, build the input from history + new message:
messages.push({ role: 'user', content: input });
saveMessage(sessionPath, { role: 'user', content: input });

const agentInput = messages.length > 1 ? messages : input;
const result = await runAgentWithRetry(config, agentInput, {
  onEvent: (e) => {
    if (e.type === 'text') onText(e.delta);
  },
});

messages.push({ role: 'assistant', content: result.text });
saveMessage(sessionPath, { role: 'assistant', content: result.text });
```

---

## Context Compaction

When conversation history grows too long, summarize older messages to fit within the model's context window. Pattern from pi-mono's compaction with file tracking.

### src/compaction.ts

```typescript
import { OpenRouter } from '@openrouter/agent';

type Message = { role: string; content: string; [key: string]: unknown };

interface CompactionConfig {
  /** Max messages before triggering compaction */
  threshold: number;
  /** Number of recent messages to preserve verbatim */
  keepRecent: number;
  /** Model to use for summarization */
  model: string;
}

const DEFAULTS: CompactionConfig = {
  threshold: 40,
  keepRecent: 10,
  model: 'openai/gpt-4.1-mini',
};

/**
 * Walk the initial cut point forward until we land somewhere that doesn't
 * split a tool turn. A tool turn looks like:
 *
 *   assistant (with tool_calls) → tool (result) × N → assistant (text)
 *
 * If the boundary falls between the assistant-with-calls and its tool
 * results, the summarized half would end with an unresolved call and the
 * kept half would start with orphaned results — the model sees a
 * half-finished turn and gets confused. Pi, OpenClaw, and Claude Code all
 * enforce this invariant in their compaction paths.
 *
 * Safe cut points are before a user message or before a plain assistant
 * message with no pending tool_calls.
 */
function findSafeBoundary(messages: Message[], cut: number): number {
  while (cut < messages.length) {
    const msg = messages[cut];

    // Orphaned tool result at the boundary — step past it so the pair
    // stays together on the summarized side.
    if (msg.role === 'tool') { cut++; continue; }

    // Assistant with unresolved tool_calls — step past it and any
    // trailing tool results from the same turn.
    const toolCalls = (msg as { tool_calls?: unknown[] }).tool_calls;
    if (msg.role === 'assistant' && Array.isArray(toolCalls) && toolCalls.length > 0) {
      cut++;
      while (cut < messages.length && messages[cut].role === 'tool') cut++;
      continue;
    }

    break;
  }
  return cut;
}

export async function compactMessages(
  client: OpenRouter,
  messages: Message[],
  config: Partial<CompactionConfig> = {},
): Promise<Message[]> {
  const opts = { ...DEFAULTS, ...config };

  if (messages.length <= opts.threshold) return messages;

  const idealCut = messages.length - opts.keepRecent;
  const safeCut = findSafeBoundary(messages, idealCut);

  // If the boundary walked all the way to the end (rare: every remaining
  // message is part of one giant tool turn), give up on compacting rather
  // than summarize everything and leave nothing behind.
  if (safeCut >= messages.length) return messages;

  const toSummarize = messages.slice(0, safeCut);
  const toKeep = messages.slice(safeCut);

  const summaryResult = client.callModel({
    model: opts.model,
    instructions:
      'Summarize the following conversation concisely. Preserve key facts, decisions, file paths mentioned, and tool results. Output only the summary.',
    input: toSummarize.map((m) => `${m.role}: ${m.content}`).join('\n\n'),
  });

  const summary = await summaryResult.getText();

  return [
    { role: 'system', content: `[Conversation summary]\n${summary}` },
    ...toKeep,
  ];
}
```

### Integration

In `agent.ts`, call before `callModel`:

```typescript
import { compactMessages } from './compaction.js';

// Inside runAgent, when input is a message array, compact before calling callModel:
if (Array.isArray(input)) {
  const client = new OpenRouter({ apiKey: config.apiKey });
  input = await compactMessages(client, input as Message[], {
    threshold: 40,
    keepRecent: 10,
  });
}
// Then pass input to callModel as usual
```

---

## System Prompt Composition

Compose the system prompt from a static base plus dynamically loaded context files (similar to how pi-mono loads AGENTS.md/CLAUDE.md from project directories).

### src/system-prompt.ts

```typescript
import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

interface PromptConfig {
  /** Base system prompt */
  base: string;
  /** File names to look for in the project directory */
  contextFiles: string[];
  /** Directory to search for context files */
  projectDir: string;
}

export function composeSystemPrompt(config: PromptConfig): string {
  const parts = [config.base];

  for (const filename of config.contextFiles) {
    const filePath = resolve(config.projectDir, filename);
    if (existsSync(filePath)) {
      const content = readFileSync(filePath, 'utf-8');
      parts.push(`\n## ${filename}\n\n${content}`);
    }
  }

  return parts.join('\n');
}
```

### Integration

In `agent.ts`, use as the `instructions` parameter:

```typescript
import { composeSystemPrompt } from './system-prompt.js';

const instructions = composeSystemPrompt({
  base: config.systemPrompt,
  contextFiles: ['AGENTS.md', 'CLAUDE.md', '.agent-context.md'],
  projectDir: process.cwd(),
});

// Pass to callModel:
client.callModel({ instructions, ... });
```

---

## Tool Approval

Gate mutating tools behind user confirmation. Uses `requireApproval` from `@openrouter/agent/tool` plus a session-scoped approval cache. Pattern from Codex's approval flow.

**This module is ON by default**, because File Write, File Edit, and Shell/Bash are default-ON tools that write to the user's disk and run arbitrary commands. Generate an ungated harness only when the user explicitly asks for one.

### Approval policies

`approvalPolicy` lives in `AgentConfig` and defaults to `'dangerous-only'`:

| Policy | Behavior |
|--------|----------|
| `always` | Every mutating tool call prompts. Safest, noisiest. |
| `dangerous-only` | **Default.** Prompts for destructive shell commands and for writes that escape the working directory. Ordinary in-project edits run unprompted. |
| `never` | No prompts. Explicit opt-out — only when the user asks for it. |

Read-only tools (`file_read`, `glob`, `grep`, `list_dir`, `web_fetch`, `view_image`) are never gated under any policy.

### src/approval.ts

```typescript
import { createInterface } from 'readline';
import { resolve, relative, isAbsolute } from 'path';
import type { ApprovalPolicy } from './config.js';

// Session-scoped cache: once the user approves a given tool+target, the same
// target is not re-prompted for the rest of the run. Cleared on /new.
const approved = new Set<string>();

export function resetApprovals(): void {
  approved.clear();
}

/** Shell commands that warrant a prompt even under 'dangerous-only'. */
const DESTRUCTIVE = /\brm\b|\bsudo\b|\bchmod\b|\bchown\b|\bdd\b|\bmkfs\b|\bkill(all)?\b|>\s*\/dev\/|\bgit\s+(push|reset\s+--hard|clean)\b|\bcurl\b[^|]*\|\s*(ba)?sh/;

export function isDestructiveCommand(command: string): boolean {
  return DESTRUCTIVE.test(command);
}

/** True when a write target escapes the working directory. */
export function escapesCwd(path: string): boolean {
  const rel = relative(process.cwd(), resolve(path));
  return rel.startsWith('..') || isAbsolute(rel);
}

/**
 * Prompt the user to confirm one tool call. Returns false to deny — the caller
 * returns an error to the model rather than throwing, so the agent can recover
 * and try something else.
 */
export async function confirm(tool: string, target: string, detail: string): Promise<boolean> {
  const key = `${tool}:${target}`;
  if (approved.has(key)) return true;

  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const answer = await new Promise<string>((r) =>
    rl.question(`\n  \x1b[33m⚠\x1b[0m  ${tool} wants to ${detail}\n     [y] allow once  [a] allow for this session  [n] deny: `, r),
  );
  rl.close();

  const choice = answer.trim().toLowerCase();
  if (choice === 'a') {
    approved.add(key);
    return true;
  }
  return choice === 'y' || choice === '';
}

export function needsApproval(policy: ApprovalPolicy, dangerous: boolean): boolean {
  if (policy === 'never') return false;
  if (policy === 'always') return true;
  return dangerous;
}
```

`confirm()` reads from stdin, so it cannot run while another readline interface holds the terminal. Call it from inside `execute`, after the main REPL prompt has resolved — not from a concurrent stream handler.

### Gating a mutating tool

Each mutating tool exports a factory that takes the policy and checks it inside `execute`. `requireApproval` is also set so SDK-side consumers see the tool's metadata:

```typescript
import { tool } from '@openrouter/agent/tool';
import { z } from 'zod';
import { confirm, needsApproval, isDestructiveCommand } from '../approval.js';
import type { ApprovalPolicy } from '../config.js';

export function createShellTool(policy: ApprovalPolicy) {
  return tool({
    name: 'shell',
    description: 'Execute a shell command',
    inputSchema: z.object({ command: z.string(), timeout: z.number().optional() }),
    requireApproval: policy === 'never' ? false : policy === 'always' ? true : isDestructiveCommand,
    execute: async ({ command, timeout }) => {
      if (needsApproval(policy, isDestructiveCommand(command))) {
        const ok = await confirm('shell', command, `run: ${command}`);
        if (!ok) return { error: 'Denied by user. Do not retry this command.' };
      }
      /* ... run the command ... */
    },
  });
}
```

`createFileWriteTool` and `createFileEditTool` follow the same shape, swapping `isDestructiveCommand(command)` for `escapesCwd(path)` and describing the action as `write ${path}` / `edit ${path}`.

### Integration

```typescript
// In config.ts:
export type ApprovalPolicy = 'always' | 'dangerous-only' | 'never';
// AgentConfig gains:  approvalPolicy: ApprovalPolicy;
// DEFAULTS gains:     approvalPolicy: 'dangerous-only',

// In tools/index.ts, build mutating tools from the policy:
export function buildTools(config: AgentConfig) {
  return [
    fileReadTool,   // read-only, never gated
    createFileWriteTool(config.approvalPolicy),
    createFileEditTool(config.approvalPolicy),
    createShellTool(config.approvalPolicy),
  ];
}
```

If the `/new` slash command is generated, call `resetApprovals()` alongside clearing the conversation so session approvals do not leak across conversations.

---

## Structured Event Logging

Emit structured events for tool calls, API requests, and errors. Entry point decides how to render them. Pattern from Codex's tracing.

### src/logger.ts

```typescript
type EventType = 'tool_call' | 'tool_result' | 'api_request' | 'api_error' | 'turn_start' | 'turn_end';

interface AgentEvent {
  type: EventType;
  timestamp: string;
  data: Record<string, unknown>;
}

type EventHandler = (event: AgentEvent) => void;

export class AgentLogger {
  private handlers: EventHandler[] = [];

  on(handler: EventHandler): void {
    this.handlers.push(handler);
  }

  emit(type: EventType, data: Record<string, unknown>): void {
    const event: AgentEvent = {
      type,
      timestamp: new Date().toISOString(),
      data,
    };
    for (const handler of this.handlers) {
      handler(event);
    }
  }
}

/** Default handler that logs to stderr as JSON */
export function consoleLogHandler(event: AgentEvent): void {
  process.stderr.write(JSON.stringify(event) + '\n');
}
```

### Integration

In `agent.ts`, emit events in callbacks:

```typescript
import { AgentLogger } from './logger.js';

export async function runAgent(config: AgentConfig, input, options?) {
  const logger = options?.logger ?? new AgentLogger();

  const result = client.callModel({
    // ...
    onTurnStart: async (ctx) => {
      logger.emit('turn_start', { turn: ctx.numberOfTurns });
    },
    onTurnEnd: async (ctx) => {
      logger.emit('turn_end', { turn: ctx.numberOfTurns });
    },
  });
  // ...
}
```

In `cli.ts`, attach a handler:

```typescript
import { AgentLogger, consoleLogHandler } from './logger.js';

const logger = new AgentLogger();
logger.on(consoleLogHandler); // or a custom handler
```

---

## `@`-file References

Let users type `@filename` to attach file content to their message. Before sending to the agent, scan the input for `@path` tokens, read each file, and prepend the content.

### Integration

In `cli.ts`, before pushing the user message:

```typescript
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

function expandFileRefs(input: string): string {
  const parts: string[] = [];
  const pattern = /@([\w.\/\-]+)/g;
  let match;
  while ((match = pattern.exec(input)) !== null) {
    const filePath = resolve(match[1]);
    if (existsSync(filePath)) {
      try {
        const content = readFileSync(filePath, 'utf-8');
        parts.push(`<file path="${match[1]}">\n${content}\n</file>`);
      } catch { /* skip unreadable */ }
    }
  }
  if (!parts.length) return input;
  return parts.join('\n') + '\n\n' + input;
}

// Before messages.push:
const expanded = expandFileRefs(trimmed);
messages.push({ role: 'user', content: expanded });
```

Optional: add tab completion for `@` using `rl.completer` to fuzzy-match files in the working directory.

---

## `!` Shell Shortcut

`!command` runs a shell command and injects stdout into context as a user message, without going through a tool call. `!!command` runs silently (output not shown).

### Integration

In `cli.ts`, before command dispatch:

```typescript
import { execSync } from 'child_process';

if (trimmed.startsWith('!')) {
  const silent = trimmed.startsWith('!!');
  const cmd = trimmed.slice(silent ? 2 : 1).trim();
  if (!cmd) { rl.prompt(); return; }
  try {
    const output = execSync(cmd, { encoding: 'utf-8', timeout: 30000, maxBuffer: 256 * 1024 }).trim();
    if (!silent) console.log(`${GRAY}${output}${RESET}`);
    messages.push({ role: 'user', content: `Shell output of \`${cmd}\`:\n\`\`\`\n${output}\n\`\`\`` });
  } catch (err: any) {
    console.log(`${YELLOW}  ${err.message}${RESET}`);
  }
  rl.prompt();
  return;
}
```

---

## Multi-line Input

Replace readline with raw terminal mode to support Shift+Enter for newlines. Enter sends the message.

### src/multi-line-input.ts

```typescript
import { emitKeypressEvents } from 'readline';

export function readMultiLine(prompt: string): Promise<string> {
  return new Promise((resolve) => {
    process.stdout.write(prompt);
    emitKeypressEvents(process.stdin);
    process.stdin.setRawMode(true);
    process.stdin.resume();

    let buffer = '';
    const onKeypress = (_ch: string, key: { name: string; shift?: boolean; ctrl?: boolean }) => {
      if (key.ctrl && key.name === 'c') { process.exit(0); }
      if (key.name === 'return' && !key.shift) {
        process.stdin.setRawMode(false);
        process.stdin.pause();
        process.stdin.removeListener('keypress', onKeypress);
        process.stdout.write('\n');
        resolve(buffer);
        return;
      }
      if (key.name === 'return' && key.shift) {
        buffer += '\n';
        process.stdout.write('\n');
        return;
      }
      if (key.name === 'backspace') {
        if (buffer.length) { buffer = buffer.slice(0, -1); process.stdout.write('\b \b'); }
        return;
      }
      if (_ch) { buffer += _ch; process.stdout.write(_ch); }
    };
    process.stdin.on('keypress', onKeypress);
  });
}
```

### Integration

Replace the `rl.on('line')` loop with calls to `readMultiLine(prompt)` in a `while` loop.

