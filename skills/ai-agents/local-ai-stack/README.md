# Local AI Stack

Set up a complete, private AI stack on your own hardware — from local model serving (Ollama) to chat interface (Open WebUI) to local RAG pipelines with local embeddings. Zero cloud dependencies, zero per-token costs.

## Quick Start

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull a model
ollama pull qwen2.5:14b

# 3. Deploy Open WebUI
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

# 4. Open http://localhost:3000
```

## What's Covered

- **Ollama setup** — installation, model pulling, custom Modelfiles, GPU acceleration
- **Open WebUI** — self-hosted ChatGPT alternative with user management
- **GPU configuration** — NVIDIA CUDA, Apple Metal, AMD ROCm
- **Model selection** — comparison table by use case, size, speed, and quality
- **Local RAG** — LangChain + nomic-embed-text + ChromaDB, fully offline
- **API integration** — OpenAI-compatible endpoint at `localhost:11434`
- **Performance tuning** — flash attention, context length, concurrent requests
- **Team deployment** — reverse proxy, HTTPS, CORS, role-based access

## Model Selection Guide

| Use Case | Model | VRAM Required |
|---|---|---|
| Chat / General | Llama 3.1 8B | 6GB |
| Best balance | Qwen 2.5 14B | 10GB |
| Coding | DeepSeek Coder V2 | 10GB |
| Max quality | Llama 3.1 70B | 48GB |
| Embeddings (RAG) | nomic-embed-text | 1GB |

## Installation

### Claude Code

```bash
cp -R ai-agents/local-ai-stack ~/.claude/skills/local-ai-stack
```

### Cursor

```bash
cp -R ai-agents/local-ai-stack ~/.cursor/skills/local-ai-stack
```
