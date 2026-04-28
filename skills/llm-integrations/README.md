# llm-integrations

Skills for **connecting to LLMs through OpenRouter** — the SDK, model discovery, image generation, OAuth login, and migration from older SDK versions.

If your code calls an LLM, this is the layer.

## Skills in this category

| Skill | What it does |
| --- | --- |
| [`openrouter-typescript-sdk`](./openrouter-typescript-sdk/SKILL.md) | The complete reference for `@openrouter/sdk` and `@openrouter/agent` — the `callModel` pattern, tool definitions, stop conditions, streaming, and 300+ supported models. |
| [`openrouter-models`](./openrouter-models/SKILL.md) | Query available OpenRouter models — pricing, context lengths, capabilities, provider latency, throughput. Search/filter/compare models, find the fastest provider. |
| [`openrouter-images`](./openrouter-images/SKILL.md) | Generate images from text prompts and edit existing images using OpenRouter's image-generation models. |
| [`openrouter-oauth`](./openrouter-oauth/SKILL.md) | "Sign In with OpenRouter" via OAuth PKCE — framework-agnostic, no SDK, no client registration, no backend, no secrets. |
| [`openrouter-agent-migration`](./openrouter-agent-migration/SKILL.md) | Migration guide from `@openrouter/sdk` to `@openrouter/agent` for `callModel`, `tool()`, and stop conditions. |

## When to use this folder

- "Call an LLM from my TypeScript code"
- "Add a 'Sign in with OpenRouter' button"
- "Compare GPT-4 vs Claude pricing for my use case"
- "Generate / edit an image from a prompt"
- "Migrate my SDK code to the new agent package"

## Related categories

- [`ai-agents/`](../ai-agents/) — agent scaffolds and patterns that *use* this integration layer.
- [`data-and-backend/python-fastapi-llm/`](../data-and-backend/python-fastapi-llm/) — Python equivalent for FastAPI backends.
