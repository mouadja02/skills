---
name: smolagents-code-agents
description: Use when building Hugging Face smolagents, code-executing agents, Python-action agents, Hub-shared tools, or lightweight agent prototypes that need sandboxing and provider flexibility.
source: "https://github.com/huggingface/smolagents"
---

# Smolagents Code Agents

Use code actions when an agent benefits from loops, variables, data transforms, and multi-call tool composition. Treat generated code as untrusted unless it runs in a real sandbox.

## Use When

- The user wants a lightweight agent prototype in Python.
- Tool calls need loops, branching, or batching.
- The agent should use Hugging Face Inference Providers, LiteLLM, OpenAI-compatible servers, local `transformers`, or Ollama.
- The agent needs MCP tools, Hub tools, or a shared Space.
- You must decide between `CodeAgent` and `ToolCallingAgent`.

## Build Pattern

1. Choose `CodeAgent` when actions need Python control flow; choose `ToolCallingAgent` for simple structured tool calls.
2. Keep tools small, typed, and side-effect explicit.
3. Configure the model through environment variables or a provider object, never hard-code secrets.
4. Run code execution in Docker, E2B, Modal, Blaxel, or another isolation boundary.
5. Allow imports by explicit whitelist only.
6. Stream logs and capture intermediate observations for debugging.
7. Add a task-level timeout and max-step budget.

## Safety Baseline

Never treat `LocalPythonExecutor` as a security boundary for untrusted code. Use it only for trusted local experiments.

Generate a starter safety scaffold:

```bash
python skills/agent-design/smolagents-code-agents/scripts/smolagent_safety_scaffold.py --name research_agent
```

Review [sandboxing-checklist.md](references/sandboxing-checklist.md) before running any agent that executes model-written code.

## Quick Selection

| Requirement | Choose |
| --- | --- |
| Agent writes Python actions | `CodeAgent` |
| Strict JSON-like tool calls | `ToolCallingAgent` |
| Untrusted tasks or web data | Sandboxed executor |
| Local model experiments | `TransformersModel` or Ollama-compatible provider |
| Hosted provider flexibility | `InferenceClientModel`, `LiteLLMModel`, or OpenAI-compatible model |

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Running untrusted code locally | Use Docker or managed sandbox |
| Exposing broad filesystem access | Mount a temporary workspace only |
| Giving tools vague docstrings | Make inputs, outputs, and side effects explicit |
| Letting agents import anything | Whitelist imports per task |
| Shipping without trace logs | Persist steps, code snippets, tool outputs, and final answer |

## References

- GitHub: huggingface/smolagents - https://github.com/huggingface/smolagents
- Hugging Face docs: smolagents - https://huggingface.co/docs/smolagents/index
- Hugging Face docs: CodeAgent - https://huggingface.co/docs/smolagents/reference/agents
- Hugging Face docs: MCP tools - https://huggingface.co/docs/smolagents/tutorials/mcp
