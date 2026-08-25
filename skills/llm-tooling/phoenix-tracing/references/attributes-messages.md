# Chat Message Attributes

This document covers how chat messages are represented on LLM spans in OpenInference.

## Overview

Messages are lists, so they follow the array flattening rule plus the mandatory `.message.`
segment. See `fundamentals-flattening.md` for the general rule.

```
llm.input_messages.{index}.message.{field}
llm.output_messages.{index}.message.{field}
```

`{index}` is zero-based and reflects conversation order. Omitting the `.message.` segment is the
single most common instrumentation mistake — Phoenix will not render the conversation without it.

## Core Message Fields

| Attribute                                     | Type   | Description                                       |
| --------------------------------------------- | ------ | ------------------------------------------------- |
| `llm.input_messages.{i}.message.role`          | String | `"system"`, `"user"`, `"assistant"`, or `"tool"`  |
| `llm.input_messages.{i}.message.content`       | String | Plain text content of the message                 |
| `llm.input_messages.{i}.message.name`          | String | Optional author name for the message              |
| `llm.output_messages.{i}.message.role`         | String | Usually `"assistant"`                             |
| `llm.output_messages.{i}.message.content`      | String | Text content of the completion                    |

**Example:**

```json
{
  "openinference.span.kind": "LLM",
  "llm.input_messages.0.message.role": "system",
  "llm.input_messages.0.message.content": "You are a helpful assistant.",
  "llm.input_messages.1.message.role": "user",
  "llm.input_messages.1.message.content": "What is the capital of France?",
  "llm.output_messages.0.message.role": "assistant",
  "llm.output_messages.0.message.content": "The capital of France is Paris."
}
```

## Multimodal Content

When a single message carries mixed content (text plus images), use `contents` instead of
`content`. Each entry is itself flattened with a `.message_content.` segment.

| Attribute                                                            | Type   | Description                      |
| -------------------------------------------------------------------- | ------ | -------------------------------- |
| `llm.input_messages.{i}.message.contents.{j}.message_content.type`     | String | `"text"` or `"image"`            |
| `llm.input_messages.{i}.message.contents.{j}.message_content.text`     | String | Text, when type is `"text"`      |
| `llm.input_messages.{i}.message.contents.{j}.message_content.image.image.url` | String | URL or base64 data URI |

**Example:**

```json
{
  "openinference.span.kind": "LLM",
  "llm.input_messages.0.message.role": "user",
  "llm.input_messages.0.message.contents.0.message_content.type": "text",
  "llm.input_messages.0.message.contents.0.message_content.text": "What is in this image?",
  "llm.input_messages.0.message.contents.1.message_content.type": "image",
  "llm.input_messages.0.message.contents.1.message_content.image.image.url": "https://example.com/cat.png"
}
```

Set either `content` or `contents` on a given message, not both.

## Tool Calls

Tool invocations requested by the model live on the **output** message that requested them.

| Attribute                                                                    | Type   | Description                        |
| ----------------------------------------------------------------------------- | ------ | ---------------------------------- |
| `llm.output_messages.{i}.message.tool_calls.{k}.tool_call.id`                   | String | Provider-assigned call id          |
| `llm.output_messages.{i}.message.tool_calls.{k}.tool_call.function.name`        | String | Tool/function name                 |
| `llm.output_messages.{i}.message.tool_calls.{k}.tool_call.function.arguments`   | String | JSON-serialized argument object    |

The tool's **result** comes back as a subsequent input message with role `"tool"`, correlated by
`tool_call_id`.

| Attribute                                      | Type   | Description                              |
| ----------------------------------------------- | ------ | ---------------------------------------- |
| `llm.input_messages.{i}.message.tool_call_id`    | String | Matches the `tool_call.id` it answers    |

**Example — full call/response round trip:**

```json
{
  "openinference.span.kind": "LLM",
  "llm.output_messages.0.message.role": "assistant",
  "llm.output_messages.0.message.tool_calls.0.tool_call.id": "call_abc123",
  "llm.output_messages.0.message.tool_calls.0.tool_call.function.name": "get_weather",
  "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments": "{\"city\": \"Paris\"}",

  "llm.input_messages.2.message.role": "tool",
  "llm.input_messages.2.message.tool_call_id": "call_abc123",
  "llm.input_messages.2.message.content": "{\"temp_c\": 18, \"condition\": \"cloudy\"}"
}
```

Note that `function.arguments` and tool results are **JSON-serialized strings**, not nested
objects — attribute values must be primitives.

## Common Mistakes

| Mistake                                              | Consequence                                        |
| ----------------------------------------------------- | -------------------------------------------------- |
| Dropping the `.message.` segment                       | Phoenix will not render the conversation view       |
| Non-contiguous indices (`0`, `2`, `3`)                 | Messages render out of order or go missing          |
| Passing a nested object as an attribute value          | Rejected by OpenTelemetry; flatten it first         |
| Setting both `content` and `contents`                  | Ambiguous rendering; pick one                       |
| Tool result without `tool_call_id`                     | Result cannot be correlated to its call             |

## See Also

- `fundamentals-flattening.md` — the general flattening rules these follow
- `span-llm.md` — the full LLM span attribute set
- `span-tool.md` — TOOL spans for the execution of a tool call
- `instrumentation-manual-python.md` / `instrumentation-manual-typescript.md` — setting these in code
