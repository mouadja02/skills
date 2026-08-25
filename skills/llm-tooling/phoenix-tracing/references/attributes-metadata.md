# Metadata and Tags

This document covers custom metadata and tags — the two supported ways to attach your own
dimensions to any span.

## Overview

Metadata is how you make traces filterable by concerns OpenInference does not model natively:
environment, tenant, prompt version, experiment arm, cost center.

| Attribute  | Type   | Description                                      |
| ---------- | ------ | ------------------------------------------------ |
| `metadata` | String | JSON-serialized object of arbitrary key-values   |
| `tag.tags` | List   | List of short string labels                      |

Both can be set on **any span kind**.

## Metadata

`metadata` is a single attribute holding a **JSON-serialized string** — not a nested object. The
flattening convention does not apply here; serialize the whole object yourself.

```json
{
  "openinference.span.kind": "LLM",
  "metadata": "{\"environment\": \"production\", \"prompt_version\": \"v2.1\", \"tenant_id\": \"acme\"}"
}
```

Phoenix parses the JSON and exposes each key as a filterable dimension in the UI.

### Schema Conventions

Metadata is schemaless, which makes consistency your responsibility. A schema that stays stable
across releases is what makes filtering useful six months later.

| Convention                        | Rationale                                                   |
| ---------------------------------- | ----------------------------------------------------------- |
| `snake_case` keys                  | Matches the rest of the OpenInference attribute namespace    |
| Flat, one level deep               | Nested objects are awkward to filter on in the UI            |
| Primitive values only              | Strings, numbers, booleans — avoid arrays and objects        |
| Stable key names across versions   | Renaming a key silently splits your historical data          |
| Bounded cardinality                | A key with unbounded values is a poor filter dimension       |

**A workable baseline schema:**

```json
{
  "environment": "production",
  "service_version": "1.4.2",
  "prompt_version": "v2.1",
  "model_provider": "anthropic",
  "experiment_arm": "control",
  "tenant_id": "acme"
}
```

### What Not to Put in Metadata

- **PII or secrets** — metadata is stored verbatim and shown in the UI. See `production-python.md`
  for masking guidance.
- **Large blobs** — full documents or prompt bodies belong in `input.value` / `output.value`.
- **High-cardinality identifiers** — a raw request UUID makes a useless filter. Use `session.id`
  and `user.id`, which are first-class attributes (see `fundamentals-universal-attributes.md`).
- **Anything already modeled** — do not duplicate `llm.model_name` or token counts into metadata.

## Tags

`tag.tags` is a list of short labels, for coarse classification you want to filter on without
inventing a metadata key.

```json
{
  "openinference.span.kind": "CHAIN",
  "tag.tags": ["regression-suite", "high-priority", "rag"]
}
```

Use tags for a small, closed vocabulary; use metadata for key-value dimensions.

## Inheritance

Metadata is **not** inherited by child spans. Set it on each span you intend to filter by, or set
it via a context manager / attribute propagator so every span in a request carries it — see the
language-specific guides.

## See Also

- `fundamentals-universal-attributes.md` — `session.id`, `user.id`, and other cross-kind attributes
- `metadata-python.md` / `metadata-typescript.md` — setting metadata in code
- `production-python.md` / `production-typescript.md` — PII masking before export
