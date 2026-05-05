---
name: "local-ai-stack"
description: "Set up and optimize a complete local AI infrastructure — Ollama, Open WebUI, local RAG pipelines, and private model serving. Use when the user wants to run LLMs locally, set up Ollama, install Open WebUI, create a private AI assistant, avoid cloud API costs, build a self-hosted ChatGPT alternative, run models on their own hardware, set up local embeddings for RAG, configure GPU acceleration for local inference, benchmark local models, or create an air-gapped AI environment for privacy-sensitive work."
---

# Local AI Stack

**Tier:** POWERFUL
**Category:** AI Agents
**Domain:** Local AI Infrastructure / Self-Hosted LLM / Privacy-First AI

## Overview

Build a complete, private AI stack on your own hardware — from local model serving to RAG pipelines to chat interfaces. This eliminates cloud API dependencies, keeps sensitive data local, and reduces per-token costs to zero after hardware investment. Covers Ollama for model management, Open WebUI for chat interface, and local embedding/RAG pipelines.

## When to Use

- Running LLMs locally for privacy, compliance, or cost savings
- Setting up Ollama with optimized model configurations
- Deploying Open WebUI as a self-hosted ChatGPT alternative
- Building local RAG pipelines with local embeddings
- Configuring GPU acceleration (CUDA/ROCm/Metal) for inference
- Creating an air-gapped AI environment (no internet required)
- Benchmarking local models for specific use cases
- Setting up a team-shared local AI server

## Quick Start: Full Local Stack in 10 Minutes

### Step 1: Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows (PowerShell)
winget install Ollama.Ollama

# Verify
ollama --version
```

### Step 2: Pull Models

```bash
# Recommended starter models (by use case)
ollama pull llama3.1:8b          # General purpose (fast, 4.7GB)
ollama pull qwen2.5:14b          # Best quality/speed balance (8.9GB)
ollama pull codellama:13b        # Code generation
ollama pull nomic-embed-text     # Embeddings for RAG (274MB)
ollama pull llama3.1:70b         # High quality (requires 48GB+ VRAM)

# Check downloaded models
ollama list
```

### Step 3: Deploy Open WebUI

```bash
# Docker (recommended)
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main

# Access at http://localhost:3000
```

## GPU Configuration

### NVIDIA (CUDA)

```bash
# Check GPU
nvidia-smi

# Ollama auto-detects CUDA. Verify:
ollama run llama3.1:8b "Hello" --verbose
# Look for "gpu" in output

# For Docker with GPU passthrough:
docker run -d --gpus all -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### Apple Silicon (Metal)

```bash
# Ollama uses Metal automatically on macOS
# Check memory: models need ~60% of unified memory
# 8B model  → 8GB Mac minimum
# 14B model → 16GB Mac minimum
# 70B model → 64GB Mac minimum (M2 Ultra/M3 Max)
```

### AMD (ROCm)

```bash
# Install ROCm toolkit first, then:
HSA_OVERRIDE_GFX_VERSION=11.0.0 ollama serve
```

## Model Selection Guide

| Use Case | Model | Size | Speed | Quality |
|---|---|---|---|---|
| Chat/General | Llama 3.1 8B | 4.7GB | ⚡⚡⚡ | ⭐⭐⭐ |
| Best balance | Qwen 2.5 14B | 8.9GB | ⚡⚡ | ⭐⭐⭐⭐ |
| Coding | CodeLlama 13B | 7.4GB | ⚡⚡ | ⭐⭐⭐⭐ |
| Coding (best) | DeepSeek Coder V2 | 8.9GB | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| Reasoning | Qwen 2.5 32B | 19GB | ⚡ | ⭐⭐⭐⭐⭐ |
| Max quality | Llama 3.1 70B | 40GB | 🐌 | ⭐⭐⭐⭐⭐ |
| Embeddings | nomic-embed-text | 274MB | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| Vision | LLaVA 1.6 13B | 8GB | ⚡⚡ | ⭐⭐⭐⭐ |

## Local RAG Pipeline

### Architecture

```
Documents → Chunking → Local Embeddings → Vector Store → Query
              ↓              ↓                ↓           ↓
          LangChain    nomic-embed-text    ChromaDB    Ollama LLM
```

### Implementation

```python
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader

# 1. Load documents
loader = DirectoryLoader('./docs', glob='**/*.md')
docs = loader.load()

# 2. Chunk
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3. Embed locally (no API calls!)
embeddings = OllamaEmbeddings(model='nomic-embed-text')
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory='./chroma_db')

# 4. Query with local LLM
llm = ChatOllama(model='qwen2.5:14b', temperature=0)
retriever = vectorstore.as_retriever(search_kwargs={'k': 5})

def ask(question: str) -> str:
    docs = retriever.invoke(question)
    context = '\n'.join([d.page_content for d in docs])
    response = llm.invoke(f"Context:\n{context}\n\nQuestion: {question}")
    return response.content
```

## Ollama API for Custom Integrations

```typescript
// Ollama exposes an OpenAI-compatible API at localhost:11434
const response = await fetch('http://localhost:11434/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    model: 'qwen2.5:14b',
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: false,
  }),
});

// Or use OpenAI SDK with Ollama backend:
import OpenAI from 'openai';
const client = new OpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama', // required but unused
});
```

## Performance Optimization

```bash
# Ollama environment variables
OLLAMA_NUM_PARALLEL=4      # Concurrent requests
OLLAMA_MAX_LOADED_MODELS=2 # Models in VRAM simultaneously
OLLAMA_GPU_OVERHEAD=0      # Reduce if OOM
OLLAMA_FLASH_ATTENTION=1   # Enable flash attention (faster)

# Custom Modelfile for fine-tuned inference
cat > Modelfile <<EOF
FROM qwen2.5:14b
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
PARAMETER num_gpu 99
SYSTEM "You are a helpful coding assistant."
EOF
ollama create my-coder -f Modelfile
```

## Common Pitfalls

1. **Model too large for VRAM** — Use quantized versions (Q4_K_M) or smaller models
2. **Slow inference** — Ensure GPU is detected; check with `ollama run --verbose`
3. **Docker can't reach Ollama** — Use `--add-host=host.docker.internal:host-gateway`
4. **OOM on long contexts** — Reduce `num_ctx` or use a smaller model
5. **Mixing embedding models** — Always use the same embedding model for index and query
6. **No persistence** — Mount volumes for both Ollama models and vector store data

## Security for Team Deployments

- Bind Ollama to `127.0.0.1` (default) or use reverse proxy with auth
- Open WebUI has built-in user management with roles
- Use Docker networks to isolate services
- Enable HTTPS via reverse proxy (Caddy/nginx) for remote access
- Set `OLLAMA_ORIGINS` to restrict CORS origins
