# llm-integrations

Skills for **connecting to LLMs through OpenRouter, monitoring with Arize/Phoenix, and vector search with Qdrant** — the SDK, model discovery, observability, and evaluation layer.

If your code calls an LLM or needs LLM observability, this is the layer.

## Skills in this category

| Skill | What it does |
| --- | --- |
| [`openrouter-typescript-sdk`](./openrouter-typescript-sdk/SKILL.md) | The complete reference for `@openrouter/sdk` and `@openrouter/agent` — the `callModel` pattern, tool definitions, stop conditions, streaming, and 300+ supported models. |
| [`openrouter-models`](./openrouter-models/SKILL.md) | Query available OpenRouter models — pricing, context lengths, capabilities, provider latency, throughput. Search/filter/compare models, find the fastest provider. |
| [`openrouter-images`](./openrouter-images/SKILL.md) | Generate images from text prompts and edit existing images using OpenRouter's image-generation models. |
| [`openrouter-oauth`](./openrouter-oauth/SKILL.md) | "Sign In with OpenRouter" via OAuth PKCE — framework-agnostic, no SDK, no client registration, no backend, no secrets. |
| [`openrouter-agent-migration`](./openrouter-agent-migration/SKILL.md) | Migration guide from `@openrouter/sdk` to `@openrouter/agent` for `callModel`, `tool()`, and stop conditions. |

### Arize AI (LLM observability)

| Skill | What it does |
| --- | --- |
| [`arize-ai-provider-integration`](./arize-ai-provider-integration/SKILL.md) | Integrate Arize AI with LLM providers for tracing and monitoring. |
| [`arize-annotation`](./arize-annotation/SKILL.md) | Annotate LLM traces in Arize for human feedback and evaluation. |
| [`arize-dataset`](./arize-dataset/SKILL.md) | Create and manage Arize datasets for LLM evaluation. |
| [`arize-evaluator`](./arize-evaluator/SKILL.md) | Build custom evaluators in Arize for LLM quality metrics. |
| [`arize-experiment`](./arize-experiment/SKILL.md) | Run A/B experiments on LLM prompts and models in Arize. |
| [`arize-instrumentation`](./arize-instrumentation/SKILL.md) | Instrument LLM applications with Arize OpenTelemetry tracing. |
| [`arize-link`](./arize-link/SKILL.md) | Generate and share Arize links for trace inspection and collaboration. |
| [`arize-prompt-optimization`](./arize-prompt-optimization/SKILL.md) | Optimize prompts using Arize data-driven evaluation workflows. |
| [`arize-trace`](./arize-trace/SKILL.md) | Trace and debug LLM application flows using Arize tracing. |

### Phoenix (open-source LLM observability)

| Skill | What it does |
| --- | --- |
| [`phoenix-cli`](./phoenix-cli/SKILL.md) | Use the Arize Phoenix CLI for local LLM tracing and evaluation. |
| [`phoenix-evals`](./phoenix-evals/SKILL.md) | Run LLM evaluations using Phoenix's evaluation framework. |
| [`phoenix-tracing`](./phoenix-tracing/SKILL.md) | Instrument LLM applications with Phoenix OpenTelemetry tracing. |

### Qdrant (vector database)

| Skill | What it does |
| --- | --- |
| [`qdrant-clients-sdk`](./qdrant-clients-sdk/SKILL.md) | Use the Qdrant client SDKs for vector search in Python, TypeScript, Go. |
| [`qdrant-deployment-options`](./qdrant-deployment-options/SKILL.md) | Deploy Qdrant — Docker, Kubernetes, Qdrant Cloud, self-hosted. |
| [`qdrant-model-migration`](./qdrant-model-migration/SKILL.md) | Migrate embedding models in Qdrant with zero-downtime strategies. |
| [`qdrant-monitoring`](./qdrant-monitoring/SKILL.md) | Monitor Qdrant cluster health, performance, and capacity. |
| [`qdrant-performance-optimization`](./qdrant-performance-optimization/SKILL.md) | Optimize Qdrant for search speed, indexing, and memory efficiency. |
| [`qdrant-scaling`](./qdrant-scaling/SKILL.md) | Scale Qdrant horizontally with sharding and replication strategies. |
| [`qdrant-search-quality`](./qdrant-search-quality/SKILL.md) | Improve vector search quality — reranking, hybrid search, quantization. |
| [`qdrant-version-upgrade`](./qdrant-version-upgrade/SKILL.md) | Upgrade Qdrant to new versions with migration guides and compatibility checks. |

### Model selection

| Skill | What it does |
| --- | --- |
| [`model-recommendation`](./model-recommendation/SKILL.md) | Recommend the best LLM for a use case — cost, speed, quality, context length trade-offs. |

## When to use this folder

- "Call an LLM from my TypeScript code"
- "Add a 'Sign in with OpenRouter' button"
- "Compare GPT-4 vs Claude pricing for my use case"
- "Generate / edit an image from a prompt"
- "Migrate my SDK code to the new agent package"
- "Instrument my LLM app with Arize / Phoenix tracing"
- "Set up Qdrant for vector search" / "optimize vector search quality"

## Related categories

- [`ai-agents/`](../ai-agents/) — agent scaffolds and patterns that *use* this integration layer.
- [`data-and-backend/python-fastapi-llm/`](../data-and-backend/python-fastapi-llm/) — Python equivalent for FastAPI backends.
