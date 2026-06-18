# MCP Tool Routing Patterns

## Pattern 1: Synchronized Flat Index

Use when tools are independent and server count is modest.

1. Poll MCP servers or registries.
2. Normalize each tool into a retrieval document.
3. Hash schema and description fields.
4. Upsert changed tools and delete stale tools.
5. Retrieve top-k tools per request.

This matches the ScaleMCP lesson that MCP servers should be the single source of truth, with local indexes synchronized from them.

## Pattern 2: Agent-as-a-Graph

Use when tools belong to parent agents or servers and selection should return the owner, not only the tool.

Graph nodes:

- `agent`
- `server`
- `tool`
- `capability`
- `domain`
- `permission`

Graph edges:

- `agent owns tool`
- `server exposes tool`
- `tool requires permission`
- `tool supports capability`
- `tool complements tool`

Retrieve candidate tools and agents, rerank, then traverse to the parent agent/server set.

## Pattern 3: Safety-Aware Router

Use when retrieved tools can write data, spend money, expose secrets, or call external services.

Add routing penalties or hard gates for:

- Destructive operations
- Broad OAuth scopes
- Tools with untrusted natural-language descriptions
- Tools that return executable instructions
- Tools whose schema hash changed after task planning

## Failure Modes

| Failure | Mitigation |
| --- | --- |
| Tool stuffing | Retrieve a small candidate set instead of loading all schemas. |
| Lexical false positive | Include synthetic user questions and argument semantics in embeddings. |
| Stale schema | Hash tool definitions and resync before invocation. |
| Unsafe exposure | Classify side effects and gate write-capable tools. |
| Parent-agent miss | Use graph traversal from tool nodes to server or agent nodes. |

## References

- ScaleMCP: https://arxiv.org/abs/2505.06416
- Agent-as-a-Graph: https://arxiv.org/abs/2511.18194
- AgentRouter: https://huggingface.co/papers/2510.05445
- MCP-Bench: https://github.com/Accenture/mcp-bench

