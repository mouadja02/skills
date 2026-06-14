---
name: deepagents-harness
description: Use when designing long-horizon agents that need subagents, isolated context windows, filesystem-backed work, persistence, human approval, MCP tools, or production tracing.
source: "https://github.com/langchain-ai/deepagents"
---

# Deep Agents Harness

Design long-running agents as a harness with explicit state, bounded delegation, durable artifacts, and reviewable tool calls. Use a higher-level harness when the work needs more than one ReAct loop.

## Use When

- The agent must plan, delegate, write files, run tools, and resume after interruption.
- Tool output is too large for the context window and needs filesystem offload.
- Subagents need separate context windows or specialist instructions.
- Humans must approve, edit, or reject high-risk actions.
- You need production traces, checkpoints, evals, or deployment hooks.

## Harness Design

1. Define the persistent state object: task, plan, artifacts, decisions, approvals, and final output.
2. Split capabilities into tools, subagents, filesystem, memory, shell, and human review.
3. Give each subagent a narrow contract: inputs, allowed tools, expected artifacts, and stop condition.
4. Store bulky observations as files and pass summaries plus paths through the state.
5. Add approval gates for network calls, shell commands, writes outside workspace, credential access, deletes, and external side effects.
6. Trace every step with state diffs, tool inputs, tool outputs, and handoff reasons.
7. Evaluate the trajectory, not just the final answer.

## Decision Table

| Need | Pattern |
| --- | --- |
| Short single-step assistant | Plain tool-calling agent |
| Stateful workflow with branches | LangGraph-style graph |
| Long-horizon work with files and subagents | Deep agent harness |
| Tool execution can affect users or infrastructure | Human-in-the-loop gate |
| Agent needs learned project practices | Durable memory plus context evolution |

## Handoff Contract

Every subagent handoff should include:

- Goal and non-goals.
- Allowed files and tools.
- Evidence to collect.
- Output artifact path.
- Review criteria.
- Failure status vocabulary: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.

See [harness-contracts.md](references/harness-contracts.md) for reusable templates.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Letting subagents explore the whole repo | Give exact files, commands, and output contracts |
| Passing huge tool outputs through chat | Store them as artifacts and pass summaries |
| Treating checkpoints as logs only | Resume from checkpoints and test recovery |
| Adding memory without invalidation | Version memory and attach evidence |
| Evaluating only pass/fail | Inspect trajectory quality, retries, dead ends, and repair behavior |

## References

- GitHub: langchain-ai/deepagents - https://github.com/langchain-ai/deepagents
- GitHub: langchain-ai/langgraph - https://github.com/langchain-ai/langgraph
- LangGraph documentation - https://docs.langchain.com/oss/python/langgraph/
- LangSmith documentation - https://docs.smith.langchain.com/
