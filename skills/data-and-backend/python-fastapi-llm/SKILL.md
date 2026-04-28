---
name: python-fastapi-llm
description: Use when building a Python API that integrates LLMs, creating an agent backend with FastAPI, implementing streaming responses, handling file uploads for AI processing, or designing a backend for an AI-powered tool. Also use for async Python patterns, Pydantic schemas for LLM structured outputs, retry strategies for LLM calls, background AI jobs, or any service combining FastAPI and LLMs. If Python + AI backend is in scope — use this skill.
---

# Python FastAPI + LLM Backend

Building AI-powered Python backends — the patterns that make them reliable, fast, and maintainable.

---

## Project Structure

```
backend/
├── main.py                  # FastAPI app factory
├── routers/
│   ├── generate.py          # AI generation endpoints
│   ├── jobs.py              # Background job management
│   └── health.py            # Health + readiness checks
├── services/
│   ├── llm.py               # LLM client abstraction
│   ├── generator.py         # Business logic for generation
│   └── storage.py           # File / DB persistence
├── models/
│   ├── requests.py          # Pydantic input models
│   └── responses.py         # Pydantic output models
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── logging.py           # Structured logging
│   └── exceptions.py        # Custom exceptions + handlers
├── tests/
└── requirements.txt
```

---

## FastAPI App Factory

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from routers import generate, jobs, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: initialize clients, warm caches
    yield
    # shutdown: close connections

app = FastAPI(title="AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/v1/generate", tags=["generate"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(health.router, tags=["health"])
```

---

## Settings (pydantic-settings)

```python
# core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_model: str = "claude-sonnet-4-6"
    max_tokens: int = 8096

    # App
    allowed_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## LLM Client — LiteLLM (recommended for multi-provider)

LiteLLM gives one unified API across Anthropic, OpenAI, Azure, Bedrock, etc.

```python
# services/llm.py
import litellm
from litellm import acompletion, completion
from core.config import settings

litellm.drop_params = True  # ignore unsupported params per provider

async def call_llm(
    messages: list[dict],
    model: str | None = None,
    response_format: type | None = None,  # Pydantic model for structured output
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str:
    response = await acompletion(
        model=model or settings.default_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens or settings.max_tokens,
        response_format=response_format,
    )
    return response.choices[0].message.content
```

---

## Structured Outputs with Pydantic

```python
from pydantic import BaseModel, Field
from typing import Literal

class DbtModel(BaseModel):
    model_name: str = Field(description="snake_case dbt model name")
    materialization: Literal["view", "table", "incremental"] = "view"
    sql: str = Field(description="The full SQL content of the model")
    description: str

class GeneratedProject(BaseModel):
    models: list[DbtModel]
    sources_yaml: str
    schema_yaml: str
    issues: list[str] = Field(default_factory=list)

async def generate_dbt_project(mapping_json: dict) -> GeneratedProject:
    response = await call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Convert this mapping:\n{mapping_json}"}
        ],
        response_format=GeneratedProject,  # LiteLLM handles JSON schema injection
    )
    return GeneratedProject.model_validate_json(response)
```

---

## Anthropic SDK Directly (for advanced features)

```python
import anthropic
from core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

async def call_claude(
    system: str,
    user_message: str,
    model: str = "claude-sonnet-4-6",
) -> str:
    message = await client.messages.create(
        model=model,
        max_tokens=8096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text

# Tool use (function calling)
async def call_claude_with_tools(
    messages: list[dict],
    tools: list[dict],  # Anthropic tool schema format
) -> anthropic.types.Message:
    return await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        tools=tools,
        messages=messages,
    )
```

---

## Streaming Responses (SSE)

```python
# routers/generate.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import anthropic
import json

router = APIRouter()
client = anthropic.AsyncAnthropic()

@router.post("/stream")
async def generate_stream(request: GenerateRequest):
    async def event_generator():
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            messages=[{"role": "user", "content": request.prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## File Upload for AI Processing

```python
# routers/generate.py
from fastapi import UploadFile, File, HTTPException
import json

@router.post("/from-mapping")
async def generate_from_mapping(file: UploadFile = File(...)):
    if not file.filename.endswith((".json", ".xml")):
        raise HTTPException(400, "Only .json or .xml mapping files supported")

    content = await file.read()
    try:
        mapping = json.loads(content)
    except json.JSONDecodeError:
        mapping = content.decode("utf-8")  # XML — parse downstream

    result = await generator_service.process(mapping)
    return result
```

---

## Background Jobs (long-running AI tasks)

```python
# For generation tasks that take > 30s, use background jobs
from fastapi import BackgroundTasks
import uuid
from services.storage import job_store

@router.post("/async-generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    await job_store.create(job_id, status="pending")
    background_tasks.add_task(run_generation, job_id, request)
    return {"job_id": job_id, "status": "pending"}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job

async def run_generation(job_id: str, request: GenerateRequest):
    try:
        await job_store.update(job_id, status="running")
        result = await generator_service.process(request)
        await job_store.update(job_id, status="done", result=result)
    except Exception as e:
        await job_store.update(job_id, status="error", error=str(e))
```

---

## Retry + Error Handling

```python
# services/llm.py
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import litellm

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((litellm.RateLimitError, litellm.APIConnectionError)),
    reraise=True,
)
async def call_llm_with_retry(messages: list[dict], **kwargs) -> str:
    return await call_llm(messages, **kwargs)
```

```python
# core/exceptions.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import litellm

async def llm_exception_handler(request: Request, exc: litellm.APIError):
    return JSONResponse(
        status_code=502,
        content={"error": "LLM provider error", "detail": str(exc)},
    )

# In main.py:
app.add_exception_handler(litellm.APIError, llm_exception_handler)
```

---

## LLM Monitoring / Structured Logging

```python
# services/llm_monitor.py
import time
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class LLMCall:
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0
    success: bool = True
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class LLMMonitor:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.calls: list[LLMCall] = []

    async def track(self, coro, model: str) -> str:
        start = time.monotonic()
        try:
            result = await coro
            elapsed = (time.monotonic() - start) * 1000
            # extract token counts if available
            self.calls.append(LLMCall(model=model, latency_ms=elapsed))
            return result
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self.calls.append(LLMCall(model=model, latency_ms=elapsed, success=False, error=str(e)))
            raise

    def summary(self) -> dict:
        return {
            "job_id": self.job_id,
            "total_calls": len(self.calls),
            "total_latency_ms": sum(c.latency_ms for c in self.calls),
            "success_rate": sum(c.success for c in self.calls) / len(self.calls) if self.calls else 0,
        }
```

---

## Prompt Engineering Patterns

**System prompt structure** — be explicit about output format:
```python
SYSTEM_PROMPT = """
You are a dbt model generator. Given an Informatica mapping, produce a valid dbt project.

ALWAYS respond with valid JSON matching this schema:
{schema_json}

Rules:
- Use snake_case for all model names
- Always use ref() and source() — never hardcode schema/table
- Cast all columns to their final types in staging models
"""
```

**Few-shot examples** — include in the user message, not the system prompt:
```python
def build_user_message(mapping: dict, examples: list[dict]) -> str:
    parts = []
    for ex in examples[:2]:  # 2 examples is usually enough
        parts.append(f"Input:\n{json.dumps(ex['input'])}\n\nOutput:\n{json.dumps(ex['output'])}")
    parts.append(f"Input:\n{json.dumps(mapping)}\n\nOutput:")
    return "\n\n---\n\n".join(parts)
```

**Chain of thought** for complex transformations:
```python
# Add a "thinking" step before the final JSON output
messages = [
    {"role": "user", "content": "Analyze this mapping and convert it..."},
    # Let Claude reason freely first, then constrain the output
]
# Use extended thinking (Anthropic) or separate reasoning step
```

---

## Testing AI Endpoints

```python
# tests/test_generate.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_generate_from_mapping():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/generate/from-mapping",
            files={"file": ("mapping.json", b'{"sources": [...]}', "application/json")},
        )
    assert response.status_code == 200
    result = response.json()
    assert "models" in result
    assert len(result["models"]) > 0

# Mock LLM calls in tests to avoid costs:
@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    async def fake_call_llm(messages, **kwargs):
        return '{"models": [], "sources_yaml": "", "schema_yaml": ""}'
    monkeypatch.setattr("services.llm.call_llm", fake_call_llm)
```

---

## Docker Setup

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml (dev)
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - .:/app       # hot-reload in dev
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Requirements

```
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.0
pydantic-settings>=2.0
litellm>=1.40      # multi-provider LLM unified API
anthropic>=0.40    # direct Anthropic SDK
tenacity>=8.0      # retry logic
httpx>=0.27        # async HTTP client
python-multipart   # file uploads
```
