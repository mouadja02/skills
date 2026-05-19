# context-engineering

Skills for **managing the context window** of AI agents — what to include, what to drop, where to persist, how to compress, and how to recover when things degrade.

The whole category is about treating context as a *budget* and the filesystem as an *extension* of that budget.

## Skills in this category

### Foundations

| Skill | What it does |
| --- | --- |
| [`context-fundamentals`](./context-fundamentals/SKILL.md) | The basics — context windows, attention mechanics, progressive disclosure, context budgeting. Read first. |

### Optimization

| Skill | What it does |
| --- | --- |
| [`context-optimization`](./context-optimization/SKILL.md) | Reduce token costs, KV-cache optimization, observation masking, context partitioning, extending effective capacity. |
| [`context-compression`](./context-compression/SKILL.md) | Compress conversation history, structured summarization, tokens-per-task optimization for long sessions. |

### Failure modes & recovery

| Skill | What it does |
| --- | --- |
| [`context-degradation`](./context-degradation/SKILL.md) | Diagnose lost-in-middle, context poisoning, context clash and confusion. Recognize and mitigate degradation patterns. |

### Persistence

| Skill | What it does |
| --- | --- |
| [`filesystem-context`](./filesystem-context/SKILL.md) | Offload context to files — dynamic context discovery, scratch pads, just-in-time loading, tool-output persistence. |
| [`memory-systems`](./memory-systems/SKILL.md) | Cross-session memory architectures. Compares Mem0, Zep/Graphiti, Letta, LangMem, Cognee. Vector vs knowledge-graph vs temporal-graph trade-offs. |

### Codebase & onboarding context

| Skill | What it does |
| --- | --- |
| [`acquire-codebase-knowledge`](./acquire-codebase-knowledge/SKILL.md) | Systematically acquire knowledge about an unfamiliar codebase for agent context loading. |
| [`context-map`](./context-map/SKILL.md) | Create visual and textual context maps of a system for agent understanding. |
| [`first-ask`](./first-ask/SKILL.md) | Ask the right clarifying questions before starting any task to establish context. |
| [`integrate-context-matic`](./integrate-context-matic/SKILL.md) | Integrate ContextMatic for automated context generation and maintenance. |
| [`mini-context-graph`](./mini-context-graph/SKILL.md) | Build a minimal context graph of key entities and relationships in a codebase. |
| [`onboard-context-matic`](./onboard-context-matic/SKILL.md) | Onboard ContextMatic to automatically generate CONTEXT.md files for a project. |
| [`what-context-needed`](./what-context-needed/SKILL.md) | Determine what context the agent needs to complete a task effectively. |
| [`napkin`](./napkin/SKILL.md) | Visual whiteboard collaboration — draw, sketch, add sticky notes, share with the agent for analysis and ideation. |

## When to use this folder

- "My agent is forgetting / drifting / losing track of X"
- "How do I reduce token cost on this multi-turn workflow?"
- "I need persistent memory across sessions"
- "Pick a memory framework"
- "Compress this conversation"
- "What do you need to know before starting this task?"
- "Map out this codebase for context"

## Related categories

- [`ai-agents/`](../ai-agents/) — the agent systems whose context you're engineering.
- [`ai-agents/latent-briefing/`](../ai-agents/latent-briefing/) — multi-agent context-sharing technique that lives there because it's a coordination pattern.
