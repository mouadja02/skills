# ai-agents

Skills for **designing, scaffolding, and orchestrating AI agents** — single-agent and multi-agent, headless and TUI, hosted and local. Includes Microsoft Copilot agent tooling, structured autonomy frameworks, MCP integration, and prompt engineering.

Use these when the task is *building an agent system*, not *using* one.

## Skills in this category

### Architecture & patterns

| Skill | What it does |
| --- | --- |
| [`ai-agent-builder`](./ai-agent-builder/SKILL.md) | Design agent architectures — tool calling, multi-step autonomous loops, subagent orchestration, evaluation pipelines. The general-purpose agent design skill. |
| [`multi-agent-patterns`](./multi-agent-patterns/SKILL.md) | Supervisor pattern, swarm architecture, agent handoffs, context isolation, parallel execution. |
| [`tool-design`](./tool-design/SKILL.md) | Design and name agent tools — reduce complexity, write good descriptions, MCP tool patterns, consolidation strategies. |
| [`bdi-mental-states`](./bdi-mental-states/SKILL.md) | Belief-Desire-Intention architecture — model agent mental states, RDF-to-beliefs transforms, neuro-symbolic integration. |
| [`latent-briefing`](./latent-briefing/SKILL.md) | Cross-agent memory without summarization — KV cache compaction, attention matching, recursive language models with workers. |
| [`agentic-rag-architect`](./agentic-rag-architect/SKILL.md) | An expert guide for building, optimizing, and designing advanced Retrieval-Augmented Generation (RAG) systems with agentic capabilities. |
| [`agentic-browser-automation`](./agentic-browser-automation/SKILL.md) | Build AI-powered browser agents that autonomously navigate, scrape, fill forms, and extract data using LLM reasoning + Playwright. Self-healing selectors, API discovery, stealth mode. |

### Prompt engineering & evaluation

| Skill | What it does |
| --- | --- |
| [`senior-prompt-engineer`](./senior-prompt-engineer/SKILL.md) | Prompt optimization, A/B prompt testing with regression workflows, prompt versioning and governance, RAG evaluation, agent orchestrator validation, structured-output design, few-shot example design. The canonical prompt-engineering skill. |

### MCP & tooling

| Skill | What it does |
| --- | --- |
| [`mcp-server-builder`](./mcp-server-builder/SKILL.md) | Build production-grade MCP (Model Context Protocol) servers from API contracts. Scaffold Python or TypeScript MCP servers, expose REST APIs to LLM agents as MCP tools. |

### Scaffolding (project starters)

| Skill | What it does |
| --- | --- |
| [`create-agent-tui`](./create-agent-tui/SKILL.md) | Scaffold a TypeScript TUI agent (like create-react-app for terminal agents). Three input styles, four tool display modes, ASCII banners, streaming, sessions. |
| [`create-headless-agent`](./create-headless-agent/SKILL.md) | Scaffold a headless TypeScript agent with Bun — for CLI tools, API servers, queue workers, pipelines. No UI. |
| [`hosted-agents`](./hosted-agents/SKILL.md) | Build background/hosted coding agents — sandboxed VMs, Modal sandboxes, multiplayer agents, self-spawning agents. |

### Infrastructure & reliability

| Skill | What it does |
| --- | --- |
| [`durable-agent-workflows`](./durable-agent-workflows/SKILL.md) | Build fault-tolerant agent pipelines with Temporal, Inngest, or DIY checkpointing — automatic retry, crash recovery, human-in-the-loop gates, observability. |
| [`local-ai-stack`](./local-ai-stack/SKILL.md) | Set up a complete private AI stack — Ollama, Open WebUI, local RAG pipelines, GPU acceleration, model selection, team deployment. Zero cloud dependencies. |

### Domain-specific agents

| Skill | What it does |
| --- | --- |
| [`trading-agent-builder`](./trading-agent-builder/SKILL.md) | Build multi-agent AI trading systems — fundamental/technical/sentiment analysts, risk manager, portfolio manager, backtesting framework. |

### Self-improving agents

| Skill | What it does |
| --- | --- |
| [`auto-memory-pro`](./auto-memory-pro/SKILL.md) | Curate Claude Code's auto-memory into durable project knowledge — analyze MEMORY.md, promote learnings to CLAUDE.md and `.claude/rules/`, extract recurring solutions into reusable skills. |
| [`autoresearch-agent`](./autoresearch-agent/SKILL.md) | Autonomous experiment loop that optimizes any file by a measurable metric (Karpathy-inspired). The agent edits, evaluates, and only keeps improvements (git commit), runs unattended. |

### Methodology

| Skill | What it does |
| --- | --- |
| [`bmm-skills/`](./bmm-skills/SKILL.md) | **BMad Method (BMM)** — full agile AI-development framework with 30 sub-skills across 4 phases (Analysis → Planning → Solutioning → Implementation) and 6 named agent personas (Mary the analyst, Paige the tech writer, John the PM, Sally the UX designer, Winston the architect, Amelia the developer). Routes to the right sub-skill folder. |

### Microsoft Copilot & agent platforms

| Skill | What it does |
| --- | --- |
| [`agent-governance`](./agent-governance/SKILL.md) | Governance policies and guardrails for AI agent deployments. |
| [`agent-owasp-compliance`](./agent-owasp-compliance/SKILL.md) | OWASP Top-10 for LLMs compliance review for agent systems. |
| [`agent-supply-chain`](./agent-supply-chain/SKILL.md) | Supply chain security and integrity checks for AI agent pipelines. |
| [`ai-ready`](./ai-ready/SKILL.md) | Assess and prepare a codebase to be AI agent-ready. |
| [`ai-team-orchestration`](./ai-team-orchestration/SKILL.md) | Orchestrate teams of AI agents for complex collaborative tasks. |
| [`create-agentsmd`](./create-agentsmd/SKILL.md) | Generate and maintain `AGENTS.md` files for codebases. |
| [`declarative-agents`](./declarative-agents/SKILL.md) | Build Microsoft 365 Copilot declarative agents with skills and actions. |
| [`entra-agent-user`](./entra-agent-user/SKILL.md) | Configure Microsoft Entra for AI agent user identities and permissions. |
| [`foundry-agent-sync`](./foundry-agent-sync/SKILL.md) | Sync and manage agents using Azure AI Foundry. |
| [`mcp-cli`](./mcp-cli/SKILL.md) | Use the MCP CLI to manage and interact with MCP servers. |
| [`mcp-copilot-studio-server-generator`](./mcp-copilot-studio-server-generator/SKILL.md) | Generate MCP servers for Microsoft Copilot Studio integrations. |
| [`mcp-create-adaptive-cards`](./mcp-create-adaptive-cards/SKILL.md) | Create Adaptive Cards for use in MCP-powered agent responses. |
| [`mcp-create-declarative-agent`](./mcp-create-declarative-agent/SKILL.md) | Create declarative Copilot agents via MCP tooling. |
| [`mcp-deploy-manage-agents`](./mcp-deploy-manage-agents/SKILL.md) | Deploy and manage agents using MCP server infrastructure. |
| [`mcp-security-audit`](./mcp-security-audit/SKILL.md) | Audit MCP server configurations for security vulnerabilities. |
| [`microsoft-agent-framework`](./microsoft-agent-framework/SKILL.md) | Build agents using the Microsoft Agent Framework and SDK. |
| [`semantic-kernel`](./semantic-kernel/SKILL.md) | Build AI applications and agents with Microsoft Semantic Kernel. |
| [`workiq-copilot`](./workiq-copilot/SKILL.md) | Query Microsoft 365 data (emails, meetings, Teams) via WorkIQ for live organizational context. |

### Prompt engineering & evaluation

| Skill | What it does |
| --- | --- |
| [`agentic-eval`](./agentic-eval/SKILL.md) | Systematic evaluation of agentic AI systems — metrics, harnesses, failure analysis. |
| [`ai-prompt-engineering-safety-review`](./ai-prompt-engineering-safety-review/SKILL.md) | Review prompts and agent instructions for safety, injection risks, and jailbreak vectors. |
| [`autoresearch`](./autoresearch/SKILL.md) | Run autonomous research tasks using a multi-step agent loop. |
| [`boost-prompt`](./boost-prompt/SKILL.md) | Interactively refine prompts by interrogating scope, deliverables, and constraints. |
| [`eval-driven-dev`](./eval-driven-dev/SKILL.md) | Evaluation-driven development — write evals before building agent features. |
| [`finalize-agent-prompt`](./finalize-agent-prompt/SKILL.md) | Review and finalize system prompts for production agent deployments. |
| [`prompt-builder`](./prompt-builder/SKILL.md) | Guided prompt construction workflow with structured templates. |
| [`tldr-prompt`](./tldr-prompt/SKILL.md) | Compress verbose prompts into concise, high-signal instructions. |

### Structured autonomy

| Skill | What it does |
| --- | --- |
| [`structured-autonomy-generate`](./structured-autonomy-generate/SKILL.md) | Generate structured autonomy plans for agent task execution. |
| [`structured-autonomy-implement`](./structured-autonomy-implement/SKILL.md) | Implement structured autonomy workflows in agent systems. |
| [`structured-autonomy-plan`](./structured-autonomy-plan/SKILL.md) | Plan agent tasks using structured autonomy frameworks. |

### Memory & cognition

| Skill | What it does |
| --- | --- |
| [`memory-merger`](./memory-merger/SKILL.md) | Merge and deduplicate agent memory stores across sessions. |
| [`nano-banana-pro-openrouter`](./nano-banana-pro-openrouter/SKILL.md) | Lightweight agent patterns using OpenRouter's nano/small models. |
| [`from-the-other-side-vega`](./from-the-other-side-vega/SKILL.md) | AI partner patterns and lived experience for long-term human-AI collaboration. |

## When to use this folder

- "Build an agent that does X"
- "Design a multi-agent system"
- "Scaffold a CLI agent / a TUI agent / a hosted agent"
- "Optimize this prompt" / "A/B test prompts" / "version a prompt"
- "Build an MCP server"
- "Talk to Mary / Paige / John / Sally / Winston / Amelia" (BMM personas)
- "Build a browser agent" / "scrape a website with AI" / "self-healing selectors"
- "Make my agent survive crashes" / "add retry logic" / "durable workflows"
- "Run LLMs locally" / "set up Ollama" / "private AI stack"
- "Build a trading bot" / "financial analysis agent" / "market sentiment agent"
- "Run code review / sprint planning / retrospective" (BMM workflows)

## Related categories

- [`context-engineering/`](../context-engineering/) — managing the context window of the agents you build.
- [`llm-integrations/`](../llm-integrations/) — wiring the model layer (OpenRouter SDK, OAuth, image gen).
- [`engineering-craft/`](../engineering-craft/) — the development discipline applied *to* agent code.
