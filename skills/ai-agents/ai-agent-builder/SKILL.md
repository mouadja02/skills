---
name: ai-agent-builder
description: Use when designing an agent architecture, building a system where an LLM autonomously executes multi-step tasks, implementing tool calling or function calling, orchestrating multiple specialized subagents, or creating evaluation pipelines for AI outputs. Also use for agentic data engineering pipelines, code generation agents, agent-powered CLI tools, MCP server development, or any system where an AI model calls tools, makes decisions, or loops.
---

# AI Agent Builder

Build agents that are robust, observable, and actually finish the job. The difference between a demo and a production agent is: structured outputs, error recovery, observability, and a loop that terminates cleanly.

---

## Agent Architecture Patterns

### Single-Agent with Tools (simplest)
One LLM loop that calls tools until done. Best for well-scoped tasks.

```
User Request
    → Agent (LLM)
        → Tool calls (file read, API call, code exec, etc.)
        → More tool calls as needed
    → Final structured output
```

### Orchestrator + Specialized Subagents
One orchestrator plans and delegates; subagents execute specialized tasks in parallel.

```
User Request
    → Orchestrator (plans, decomposes, synthesizes)
        → Subagent A: parse mapping files
        → Subagent B: generate SQL models
        → Subagent C: generate YAML metadata
    → Orchestrator aggregates + validates
    → Final output
```

Use this when tasks are genuinely parallelizable and have clear boundaries. Don't add subagents just to look architectural — coordination overhead is real.

### Plan-then-Execute
Agent produces a structured plan first, then executes each step. Reduces hallucination on complex tasks because it commits to a strategy before acting.

```
User Request
    → Planning pass (output: list of steps)
    → Human review (optional)
    → Execution pass (follow the plan, step by step)
    → Validation
```

---

## Tool Design (Function Calling)

Tools should be narrow, deterministic, and easy to verify. An agent that has 3 sharp tools beats one with 15 blurry ones.

**Anthropic tool schema:**
```python
tools = [
    {
        "name": "read_mapping_file",
        "description": "Read an Informatica mapping JSON file and return its contents. Use this before any analysis or generation step.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the mapping JSON or XML file"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_dbt_model",
        "description": "Write a dbt model SQL file and its schema YAML. Call once per model.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {"type": "string"},
                "sql_content": {"type": "string"},
                "schema_yaml": {"type": "string"},
                "output_dir": {"type": "string"}
            },
            "required": ["model_name", "sql_content", "output_dir"]
        }
    }
]
```

**Tool implementation:**
```python
import json

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "read_mapping_file":
        with open(tool_input["file_path"]) as f:
            return f.read()
    elif tool_name == "write_dbt_model":
        path = f"{tool_input['output_dir']}/{tool_input['model_name']}.sql"
        with open(path, "w") as f:
            f.write(tool_input["sql_content"])
        return json.dumps({"written": path, "status": "ok"})
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
```

---

## The Core Agent Loop

```python
import anthropic
import json
from typing import Any

client = anthropic.AsyncAnthropic()

async def run_agent(
    system: str,
    user_message: str,
    tools: list[dict],
    max_iterations: int = 10,
) -> tuple[str, list[dict]]:
    messages = [{"role": "user", "content": user_message}]
    tool_calls_log = []

    for iteration in range(max_iterations):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            tools=tools,
            messages=messages,
        )

        # Append assistant response to message history
        messages.append({"role": "assistant", "content": response.content})

        # Done — no tool calls
        if response.stop_reason == "end_turn":
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")), ""
            )
            return final_text, tool_calls_log

        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input)
                    tool_calls_log.append({
                        "tool": block.name,
                        "input": block.input,
                        "result": result[:500],  # truncate for logging
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent hit max iterations ({max_iterations}) without completing")
```

---

## Structured Outputs from Agents

For agents that must return structured data (not just text), use either:

**Option A: Force JSON in the prompt + parse**
```python
SYSTEM = """
You are a dbt generator. When done, you MUST output a single JSON object
(no markdown, no explanation) matching this schema:

{
  "models": [{"name": str, "sql": str, "materialization": str}],
  "sources_yaml": str,
  "issues": [str]
}
"""

# Parse the final response
import json
result = json.loads(final_text)
```

**Option B: Pydantic + instructor or LiteLLM**
```python
from pydantic import BaseModel
import litellm

class GeneratedProject(BaseModel):
    models: list[DbtModel]
    sources_yaml: str
    issues: list[str]

response = await litellm.acompletion(
    model="claude-sonnet-4-6",
    messages=messages,
    response_format=GeneratedProject,
)
project = GeneratedProject.model_validate_json(response.choices[0].message.content)
```

**Option C: Final structured tool call** — give the agent a `submit_result` tool with your schema. When the agent calls it, you have your structured output without parsing text.

```python
{
    "name": "submit_result",
    "description": "Call this when you have finished generating all models. Submit the complete result.",
    "input_schema": GeneratedProject.model_json_schema()
}
```

---

## Multi-Agent Orchestration

```python
import asyncio

async def orchestrate_migration(mapping_files: list[str]) -> list[GeneratedProject]:
    # Parse all mappings in parallel
    parse_tasks = [
        run_agent(PARSER_SYSTEM, f"Parse this mapping: {path}", parse_tools)
        for path in mapping_files
    ]
    parsed_results = await asyncio.gather(*parse_tasks)

    # Generate dbt models in parallel
    generate_tasks = [
        run_agent(GENERATOR_SYSTEM, f"Generate dbt models for:\n{result}", generate_tools)
        for result, _ in parsed_results
    ]
    generated_results = await asyncio.gather(*generate_tasks)

    # Validate all in a single pass
    validation_input = "\n\n".join(r for r, _ in generated_results)
    validated, _ = await run_agent(VALIDATOR_SYSTEM, validation_input, validate_tools)

    return generated_results
```

**Key principle:** subagents should be stateless and receive all context they need in their initial message. Don't rely on shared state — pass data explicitly.

---

## Error Recovery Patterns

**Retry with feedback:**
```python
async def run_agent_with_retry(
    system: str,
    user_message: str,
    validate_fn: callable,
    max_attempts: int = 3,
) -> Any:
    last_error = None
    for attempt in range(max_attempts):
        result, _ = await run_agent(system, user_message, tools)
        try:
            validated = validate_fn(result)
            return validated
        except Exception as e:
            last_error = e
            # Feed the error back — agent learns from its mistake
            user_message = (
                f"{user_message}\n\n"
                f"Previous attempt failed validation:\n{e}\n\n"
                f"Previous output:\n{result}\n\n"
                f"Please fix the issues and try again."
            )
    raise RuntimeError(f"Agent failed after {max_attempts} attempts: {last_error}")
```

**Checkpoint / resume for long pipelines:**
```python
import json, os

def save_checkpoint(job_id: str, step: str, data: Any):
    path = f".checkpoints/{job_id}/{step}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)

def load_checkpoint(job_id: str, step: str) -> Any | None:
    path = f".checkpoints/{job_id}/{step}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

# In the pipeline:
async def run_pipeline(job_id: str, mapping: dict):
    parsed = load_checkpoint(job_id, "parsed")
    if not parsed:
        parsed, _ = await run_agent(PARSER_SYSTEM, str(mapping), parse_tools)
        save_checkpoint(job_id, "parsed", parsed)

    generated = load_checkpoint(job_id, "generated")
    if not generated:
        generated, _ = await run_agent(GENERATOR_SYSTEM, str(parsed), gen_tools)
        save_checkpoint(job_id, "generated", generated)
```

---

## Observability: Structured Agent Logging

```python
import time, uuid
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    steps: list[dict] = field(default_factory=list)
    status: str = "running"
    error: str | None = None
    duration_ms: float = 0

    def log_step(self, step_type: str, data: dict):
        self.steps.append({
            "type": step_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        })

    def finish(self, status: str = "done", error: str | None = None):
        self.status = status
        self.error = error
```

---

## Evaluation — Automated Grading

Treat your agent like a function with inputs and expected outputs. Regression-test every change.

```python
# evals/evals.json format
evals = [
    {
        "id": 1,
        "prompt": "Convert the customer_orders mapping to dbt",
        "expected": {
            "model_count": 2,
            "has_staging_model": True,
            "incremental_strategy": "merge"
        }
    }
]

async def grade_run(prompt: str, expected: dict, agent_output: str) -> dict:
    results = {}

    # Programmatic checks
    if "model_count" in expected:
        import json
        out = json.loads(agent_output)
        results["model_count"] = len(out["models"]) == expected["model_count"]

    if "has_staging_model" in expected:
        results["has_staging_model"] = any(
            m["name"].startswith("stg_") for m in json.loads(agent_output)["models"]
        )

    # LLM-as-judge for qualitative checks
    judge_prompt = f"""
    Expected behavior: {expected}
    Agent output: {agent_output[:2000]}

    Score each criterion 0-3 (0=missing, 1=poor, 2=ok, 3=excellent).
    Return JSON: {{"scores": {{}}, "overall": 0-3, "reasoning": ""}}
    """
    judge_response, _ = await run_agent(JUDGE_SYSTEM, judge_prompt, [])
    results["llm_judge"] = json.loads(judge_response)

    pass_rate = sum(1 for v in results.values() if v is True) / len(results)
    return {"pass_rate": pass_rate, "details": results}
```

---

## MCP Server Development

Build tools you can expose to Claude via MCP:

```python
# mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("my-agent-tools")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="parse_mapping",
            description="Parse an Informatica mapping file and return structured metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "parse_mapping":
        result = await parse_mapping_file(arguments["file_path"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Prompt Engineering for Agents

**System prompt structure that works:**
```
You are a [role]. Your job is to [goal].

## What you have access to
[tool list with when to use each]

## How to approach the task
1. First, [step] 
2. Then, [step]

## Output format
[exact schema or template]

## Rules
[only the non-obvious ones — don't list obvious things like "be accurate"]
```

**Don't over-constrain.** A smart model given the right goal and tools will often find a better path than rigid step-by-step instructions. Explain the *why* — let the model reason.

**Few-shot examples in the user message** (not system) improve consistency on structured output without bloating the system prompt.
