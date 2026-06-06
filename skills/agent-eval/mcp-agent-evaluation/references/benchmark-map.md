# MCP Benchmark Map

Use this reference to choose an evaluation shape before writing tasks.

## Public Sources

| Source | Best Used For | Design Signal |
| --- | --- | --- |
| MCP-Bench | Complex real-world tasks across live MCP servers | Test fuzzy tool discovery, multi-hop planning, cross-server orchestration, and task completion separately. |
| MCPEval | Automated task generation and deep evaluation | Generate domain-specific tasks from server capability inventories, then evaluate trajectories and outcomes. |
| MCP Security Bench | Security regression testing | Include attack paths against planning, tool invocation, and response handling. |
| LiveMCPBench / LiveMCP-101 | Dynamic, tool-rich environments | Stress routing when many tools exist and task wording does not name the required server. |

## Minimum Suite

Create at least these task groups:

1. **Smoke tasks** - one read-only tool, explicit goal, deterministic answer.
2. **Routing tasks** - many plausible tools, fuzzy user wording.
3. **Trajectory tasks** - dependency chain across two or more calls.
4. **Recovery tasks** - missing parameter, failed call, rate limit, or partial output.
5. **Security tasks** - malicious tool description, malicious tool output, unsafe write, or prompt-injection content.

## Scoring Notes

Keep scoring decomposed. A final answer can be correct by luck while the trajectory is unsafe, and a trajectory can be reasonable even when an external service is unavailable.

Recommended fields per run:

```json
{
  "task_id": "billing-cross-server-001",
  "tool_retrieval": 0.0,
  "schema_use": 0.0,
  "trajectory": 0.0,
  "outcome": 0.0,
  "grounding": 0.0,
  "safety": 0.0,
  "harness_status": "ok",
  "notes": ""
}
```

## References

- MCP-Bench: https://huggingface.co/papers/2508.20453
- MCPEval: https://huggingface.co/papers/2507.12806
- MCP Security Bench: https://huggingface.co/papers/2510.15994
- Accenture MCP-Bench code: https://github.com/Accenture/mcp-bench
- Salesforce AI Research MCPEval code: https://github.com/SalesforceAIResearch/MCPEval

