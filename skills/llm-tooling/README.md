# llm-tooling

Skills for **LLM observability, tracing, evaluation (Arize/Phoenix), vector search (Qdrant), and OpenRouter model routing**.

## Skills in this category

### Arize AI — observability & evaluation

| Skill | What it does |
| --- | --- |
| `arize-ai-provider-integration` | Integrate LLM providers with Arize Phoenix. |
| `arize-annotation` | Add human annotations to traces in Arize. |
| `arize-dataset` | Build and manage datasets in Arize for evaluation. |
| `arize-evaluator` | Create custom evaluators in Arize Phoenix. |
| `arize-experiment` | Run experiments and A/B tests in Arize. |
| `arize-instrumentation` | Instrument LLM applications with Arize tracing. |
| `arize-link` | Link traces, datasets, and experiments in Arize. |
| `arize-prompt-optimization` | Optimize prompts using Arize experiment data. |
| `arize-trace` | View and analyze traces in Arize Phoenix. |

### Phoenix — open-source LLM observability

| Skill | What it does |
| --- | --- |
| `phoenix-cli` | Arize Phoenix CLI — launch, manage, export. |
| `phoenix-evals` | Phoenix evaluations — hallucination, relevance, toxicity, custom. |
| `phoenix-tracing` | Instrument apps with Phoenix tracing — spans, attributes, callbacks. |

### Qdrant — vector search

| Skill | What it does |
| --- | --- |
| `qdrant-clients-sdk` | Qdrant Python/TypeScript/Go client SDK usage. |
| `qdrant-deployment-options` | Deploy Qdrant — Docker, Kubernetes, cloud. |
| `qdrant-model-migration` | Migrate embedding models in Qdrant without downtime. |
| `qdrant-monitoring` | Monitor Qdrant — metrics, health, performance dashboards. |
| `qdrant-performance-optimization` | Optimize Qdrant queries — HNSW config, quantization, filters. |
| `qdrant-scaling` | Scale Qdrant — sharding, replication, distributed mode. |
| `qdrant-search-quality` | Improve Qdrant search quality — hybrid search, reranking. |
| `qdrant-version-upgrade` | Upgrade Qdrant versions safely. |

### OpenRouter — model routing

| Skill | What it does |
| --- | --- |
| `openrouter-typescript-sdk` | OpenRouter TypeScript SDK — completions, streaming, tool use. |
| `openrouter-models` | Explore and select OpenRouter models by capability and cost. |
| `openrouter-agent-migration` | Migrate agents to use OpenRouter for model routing. |
| `openrouter-images` | Generate images via OpenRouter. |
| `openrouter-oauth` | OAuth integration for OpenRouter. |

### General

| Skill | What it does |
| --- | --- |
| `model-recommendation` | Recommend the best LLM for a given use case. |

### Image generation _(from steipete/agent-scripts)_

| Skill | What it does |
| --- | --- |
| `nano-banana-pro` | Gemini image gen/edit — text/image input, 512-4K workflows, draft→iterate→final. |
| `openai-image-gen` | OpenAI Images API — batches, prompt sampler, gallery via gpt-image-1. |

### Second-model review _(from steipete/agent-scripts)_

| Skill | What it does |
| --- | --- |
| `oracle` | Oracle — bundle prompts/files for another AI model review, debug, refactor. |

## When to use this category

- "Instrument my LLM app with tracing"
- "Evaluate hallucinations / relevance"
- "Set up Qdrant vector search" / "optimize search quality"
- "Use OpenRouter for model routing"
- "Run A/B experiments on prompts"
- "Generate images with Gemini / OpenAI"
- "Send this codebase to another model for review"
