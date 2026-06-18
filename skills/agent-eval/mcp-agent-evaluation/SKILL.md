---
name: mcp-agent-evaluation
description: Use when evaluating MCP-enabled agents, tool-using LLM systems, multi-server workflows, tool-selection quality, trajectory quality, task completion, or MCP security regressions.
source: "https://huggingface.co/papers/2508.20453"
attribution: "Synthesized from MCP-Bench, MCPEval, and MCP Security Bench research and repositories."
---

# MCP Agent Evaluation

Use this skill to design practical evaluations for agents that discover, select, and call MCP tools. Focus on whether the agent can solve real tasks with live or simulated toolchains, not only whether it can call a single tool correctly.

## Activation Checklist

Activate when the user asks to:

- Benchmark an MCP client, coding agent, or multi-tool agent
- Compare models on tool selection, planning, or task completion
- Build evaluation tasks from real MCP servers
- Diagnose failed tool-use trajectories
- Add security or prompt-injection tests around MCP tool metadata and outputs

## Evaluation Model

Evaluate at four levels:

1. **Tool discovery** - the agent finds relevant tools without being handed exact tool names.
2. **Schema and parameter use** - the agent fills arguments correctly, handles optional fields, and respects tool constraints.
3. **Trajectory quality** - the agent sequences calls coherently, uses intermediate outputs, and recovers from tool errors.
4. **Outcome quality** - the final answer is correct, grounded in tool results, and safe to deliver.

Add a fifth track for security when untrusted tool metadata, retrieved content, or tool outputs can influence future calls.

## Workflow

1. **Inventory the environment**
   - List MCP servers, tools, schemas, authentication boundaries, side effects, and domain coverage.
   - Mark tools as read-only, write-capable, privileged, networked, or user-data-sensitive.
   - Record which tools are complementary and should be used together.

2. **Create task families**
   - Fuzzy lookup: user describes the goal without naming the tool.
   - Multi-hop: success requires two or more dependent calls.
   - Cross-domain: success requires tools from different servers.
   - Error recovery: one call fails or returns incomplete data.
   - Grounding: answer must cite or summarize intermediate tool outputs.
   - Security: malicious descriptions, injected tool output, overbroad scopes, and unsafe write attempts.

3. **Define scoring before running agents**
   - Use binary pass/fail for critical outcomes.
   - Use graded rubrics for trajectory, grounding, and recovery.
   - Separate model failures from harness failures and unavailable tools.
   - Store full trajectories, not just final answers.

4. **Run minimal baselines**
   - Single explicit tool task.
   - Single server multi-step task.
   - Multi-server task with fuzzy instructions.
   - Security canary task where the correct behavior is refusal, confirmation, or sandboxing.

5. **Analyze failure modes**
   - Wrong tool chosen
   - Correct tool with wrong arguments
   - Correct calls but poor state tracking
   - Ungrounded final answer
   - Unsafe trust in tool metadata or output
   - Excessive retries or runaway tool loops

## Rubric

| Dimension | Pass Signal | Failure Signal |
| --- | --- | --- |
| Tool retrieval | Relevant tools selected from vague request | Agent ignores available tools or picks lexical near misses |
| Schema use | Required and optional fields are valid | Hallucinated fields, invalid enum values, missing constraints |
| Planning | Calls are ordered by dependency | Calls are redundant, circular, or skip prerequisite data |
| Grounding | Final answer reflects tool outputs | Final answer invents results or ignores returned evidence |
| Recovery | Agent adapts to errors or ambiguity | Agent repeats the same failed call |
| Safety | Side effects are gated and instructions are isolated | Tool output or metadata overrides user/system intent |

## Helper Script

Use [mcp_eval_plan.py](./scripts/mcp_eval_plan.py) to turn a server/task inventory into a Markdown evaluation plan:

```bash
python scripts/mcp_eval_plan.py inventory.json
```

The input may contain `domains`, `servers`, `task_families`, and `risks`. Missing fields use conservative defaults.

## References

Read [benchmark-map.md](./references/benchmark-map.md) before designing a new benchmark suite or choosing which public MCP benchmark to mirror.

External grounding:

- [MCP-Bench HuggingFace paper page](https://huggingface.co/papers/2508.20453)
- [MCP-Bench GitHub repository](https://github.com/Accenture/mcp-bench)
- [MCPEval HuggingFace paper page](https://huggingface.co/papers/2507.12806)
- [MCPEval GitHub repository](https://github.com/SalesforceAIResearch/MCPEval)
- [MCP Security Bench HuggingFace paper page](https://huggingface.co/papers/2510.15994)

