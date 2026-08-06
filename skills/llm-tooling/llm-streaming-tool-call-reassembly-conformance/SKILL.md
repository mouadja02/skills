---
name: llm-streaming-tool-call-reassembly-conformance
description: Use when streamed LLM tool calls merge, truncate, collide, or execute early across OpenAI-compatible, Anthropic, or Mistral events — reassemble by stable slot, validate terminal state and schema, and gate execution offline.
version: "1.0.0"
license: MIT
---

# LLM Streaming Tool-Call Reassembly Conformance

## When to Use

- Parallel streamed tool calls merge into malformed arguments or inconsistent IDs.
- A tool executes when its arguments merely become parseable, before the provider ends the call.
- An OpenAI-compatible, Anthropic, or Mistral adapter needs adversarial fixture coverage.
- A delayed ID/name, repeated slot, or truncated stream must fail closed before side effects.

Do **not** use this for ordinary text streaming, MCP JSON-RPC/SSE framing, provider authentication, tool selection quality, or non-streaming calls. Use the MCP Streamable HTTP conformance skill for transport framing. This workflow never executes a tool.

## Prerequisites

- Python 3.10+; the bundled runner uses only the standard library.
- A redacted JSON capture or synthetic fixture. Remove prompts, credentials, outputs, and user data.
- The exact tool input schemas used by the application.
- A pinned adapter/provider version and a rollback path.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_tool_stream.py fixture.json --report json
```

| Exit | Meaning | Execution decision |
| ---: | --- | --- |
| 0 | Complete, unambiguous, schema-valid calls | Eligible for a separate policy gate |
| 1 | Conformance failure | Block every call in the turn |
| 2 | Invalid input or no streamed tool calls | Fix fixture or do not activate |

A JSON report has `status`, `applicable`, `executable`, `calls`, and stable finding codes. Only `status=pass`, `applicable=true`, and `executable=true` permits handoff. Eligibility is not authorization: normal authorization, idempotency, and security policy still apply.

## Fixture Envelope

Use one profile and preserve event order:

```json
{
  "profile": "openai",
  "tool_schemas": {
    "weather": {
      "type": "object",
      "properties": {"city": {"type": "string"}},
      "required": ["city"],
      "additionalProperties": false
    }
  },
  "chunks": [
    {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "type": "function", "function": {"name": "weather", "arguments": "{\"ci"}}]}}]},
    {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "ty\":\"Paris\"}"}}]}, "finish_reason": "tool_calls"}]}
  ]
}
```

- `openai` and `mistral` consume `chunks[].choices[].delta.tool_calls[]` and require a `finish_reason: "tool_calls"` terminal signal.
- `anthropic` consumes `events[]`: `content_block_start` with a `tool_use` block, `content_block_delta` with `input_json_delta.partial_json`, then `content_block_stop` for that index.
- Schemas use the runner's documented conservative subset. Unsupported schema keywords fail closed instead of being ignored.

## Procedure

### 1. Freeze identity and safety boundaries

Record provider, model, SDK/adapter version, capture point, expected tools, and whether parallel calls are enabled. Disable downstream execution in the test harness. Redact before saving fixtures; do not replay production streams.

**Complete when:** the fixture is data-only, version-pinned, and cannot invoke a tool.

### 2. Preserve raw order; do not repair by intuition

Keep every delta, including empty strings and delayed names/IDs. Never concatenate globally. The reassembly key is the provider's stable content-block index or tool-call index **within one assistant turn**. An index reused with a different non-empty ID or name is an identity collision, not a second call to guess apart.

**Complete when:** each fragment retains its turn, choice/block, slot, and order.

### 3. Reassemble as a state machine

For every slot, transition through:

```text
unseen -> accumulating -> terminal -> validated
                    \-> blocked
```

Append only argument deltas belonging to that slot. Repeated terminal events, deltas after terminal, conflicting IDs/names, missing slots, and wrong terminal reasons block the whole turn. A JSON prefix becoming parseable is **not** terminal evidence.

**Complete when:** every slot has one identity, one ordered buffer, and exactly one provider terminal transition.

### 4. Validate only after terminal state

After terminal state, parse arguments as strict JSON: reject trailing documents, `NaN`, `Infinity`, and non-object arguments. Resolve the final tool name to the supplied schema and validate the conservative subset. Unknown tools, unsupported schema keywords, and schema-invalid arguments fail closed.

**Complete when:** parsing and schema validation happen once, after terminal state, for every call.

### 5. Gate the turn atomically

Run the helper. If any call fails, set `executable=false` for the entire turn. Do not execute the calls that happened to validate; partial side effects make retries ambiguous. Preserve the report with the redacted fixture and adapter version.

**Complete when:** downstream code checks the turn-level decision, not only per-call parse success.

### 6. Differential-test before rollout

Run fixtures through both the provider adapter and this runner. Cover fragmented JSON, interleaved calls, delayed IDs/names, empty deltas, Unicode text, reused indices, malformed JSON, schema-invalid final objects, duplicate terminal events, and truncation. Pin expected finding codes in CI.

**Complete when:** bad fixtures are blocked for the intended reason and a valid fragmented stream yields the expected calls byte-for-byte.

## Failure Recovery

- **Identity collision:** quarantine the full turn; capture raw redacted events earlier in the adapter; do not invent new indices.
- **Truncated or missing terminal event:** mark outcome unknown and do not replay automatically. Retry only under an application idempotency policy with fresh call/turn identity.
- **Arguments parse early then grow:** remove parseability-based emission; wait for provider terminal evidence.
- **Schema drift:** pin the deployed schema and adapter version, update fixtures intentionally, and rerun both positive and negative cases.
- **Provider-specific event is unsupported:** retain the fixture, add a reviewed normalizer, and classify it as blocked; never silently drop a tool delta.

## Pitfalls and Unsafe Operations

- Do not key calls globally by `index`; indices are scoped to a turn and sometimes a choice/content block.
- Do not merge two calls because a gateway emitted the same index.
- Do not trust balanced braces, parseable JSON, stream closure, or a text stop as tool completion.
- Do not loosen schemas or discard unknown fields to make a fixture pass.
- Do not log credentials, prompts, tool outputs, or proxy/provider headers.
- Do not auto-replay side-effecting tools after disconnects or ambiguous completion.

## Objective Verification

A release is ready only when:

1. a valid fragmented call exits 0 and reports its exact ID, name, arguments, and `executable=true`;
2. an interleaved/reused-slot fixture exits 1 with `identity_collision` and executes nothing;
3. a text-only stream exits 2 with `status=not_applicable`;
4. malformed, truncated, duplicate-terminal, non-finite, unknown-tool, unsupported-schema, and schema-invalid fixtures fail closed;
5. no helper test requires network access.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

## Evaluation Prompts

1. **Normal:** “Verify this fragmented OpenAI tool-call stream and return the exact executable call.”
2. **Difficult edge:** “Two parallel calls reuse index 0 with different IDs; reconstruct them and decide whether either may execute.”
3. **Should not activate:** “Render this ordinary streamed text response in a chat UI.”

## Sources and Recommendation Boundary

Sourced facts: OpenAI and Mistral document streamed/parallel tool calls; Anthropic documents `input_json_delta` carrying partial JSON; the cited LangChain, LiteLLM, and Vercel AI issues report identity collision, merged parallel arguments, and premature emission failures.

Repository recommendations: the provider-neutral envelope, strict slot state machine, conservative schema subset, atomic turn-level gate, and recovery policy are original operational guidance. They are not provider specifications.

- OpenAI function calling: https://platform.openai.com/docs/guides/function-calling
- Anthropic streaming: https://docs.anthropic.com/en/docs/build-with-claude/streaming
- Mistral function calling: https://docs.mistral.ai/capabilities/function_calling/
- LangChain issue 38677: https://github.com/langchain-ai/langchain/issues/38677
- LiteLLM issue 33678: https://github.com/BerriAI/litellm/issues/33678
- Vercel AI issue 12052: https://github.com/vercel/ai/issues/12052

No source prose or code is copied. The helper and fixtures are original MIT-licensed work.
