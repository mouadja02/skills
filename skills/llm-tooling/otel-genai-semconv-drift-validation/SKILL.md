---
name: otel-genai-semconv-drift-validation
description: "Use when OpenTelemetry GenAI spans or events drift across semantic-convention versions, duplicate token usage, use obsolete names, or capture model content without explicit safeguards."
version: "1.0.0"
license: MIT
---

# OpenTelemetry GenAI Semantic-Convention Drift Validation

Pin the convention evidence, normalize exported records, and reject ambiguous migrations before changing dashboards or collectors. The bundled helper is offline and data-only: it never contacts a telemetry backend and never rewrites input.

## When to Use

- A GenAI instrumentation or collector upgrade renames or moves `gen_ai.*` fields.
- Different SDKs emit incompatible span names, events, token totals, or content representations.
- Dashboards must migrate from legacy GenAI attributes without silently losing data.
- Prompt, response, or system-instruction capture needs an explicit privacy gate.

## When Not to Use

- The telemetry has no GenAI records; use the relevant database, HTTP, or infrastructure tracing workflow.
- The task is initial OpenTelemetry SDK installation rather than semantic compatibility.
- The user wants provider-specific OpenInference setup or Phoenix querying; use `phoenix-tracing`.
- A production collector should be modified automatically. This skill produces evidence and a migration plan, not mutation authorization.

## Prerequisites

- A redacted OTLP JSON export or a normalized fixture containing only the records under review.
- Exact instrumentation, SDK, collector, and semantic-convention versions or commit identifiers.
- Owners for telemetry schema, dashboards, privacy, and rollback.
- Python 3.10+ for the optional offline helper.

## Quick Reference

1. Pin the emitting and target semantic-convention commits.
2. Capture the same bounded request through old and new paths.
3. Normalize only span/event name and attributes into the schema below.
4. Run:

```bash
python3 scripts/validate_genai.py --input observations/genai.json
```

Exit `0` means `pass`, `review`, or `not_applicable`; exit `1` means semantic errors; exit `2` means malformed/unreadable input or an unknown profile. The helper always reports `mutation_permitted: false`.

## Normalized Input

```json
{
  "schema_version": 1,
  "profile": "otel-genai-main-434c91d",
  "content_capture": {
    "opt_in": false,
    "redaction_verified": false,
    "truncation_limit": null
  },
  "records": [{
    "kind": "span",
    "name": "chat model-a",
    "attributes": {
      "gen_ai.operation.name": "chat",
      "gen_ai.request.model": "model-a",
      "gen_ai.usage.input_tokens": 15,
      "gen_ai.usage.cache_read.input_tokens": 5
    }
  }]
}
```

Do not include trace payloads, credentials, API keys, user identifiers, production prompt text, or complete tool arguments. Preserve an encrypted, access-controlled raw export separately only when policy permits.

## Procedure

### 1. Freeze versions and data ownership

Record emitter library, language SDK, collector/exporter, backend, dashboard version, and the exact semantic-convention commit. Treat `Development` attributes as version-sensitive. Identify who owns schema changes and who can approve content capture.

**Completion:** every compared path has a version tuple and a named decision owner.

### 2. Capture a bounded old/new fixture pair

Use synthetic prompts and responses. Exercise one chat/inference operation, one tool or agent operation when relevant, cache/reasoning token subtotals, success and error, and content capture both disabled and explicitly enabled. Preserve initial span attributes and events separately; do not flatten them before comparison.

**Completion:** old and new paths processed the same synthetic inputs, with redacted raw artifacts and timestamps.

### 3. Normalize without inventing semantics

Convert OTLP envelopes to the bundled `records` shape. Preserve attribute keys, JSON value types, event names, and span names exactly. Do not rename fields during extraction. If an exporter serialized structured messages as JSON strings, record that fact rather than parsing and re-emitting them silently.

**Completion:** a reviewer can trace every normalized value to one source span or event.

### 4. Validate the pinned profile

Run the helper. It checks:

- legacy field and event names against a commit-pinned profile;
- required `gen_ai.operation.name` and operation-specific span naming;
- `execute_tool` tool identity;
- non-negative integer token counts and inclusive cache/reasoning totals;
- content attributes against explicit opt-in, redaction, and truncation controls;
- malformed shapes, non-standard JSON numbers, unknown profiles, and unrelated telemetry.

An unknown profile is a hard input error. Update the profile from a reviewed canonical commit; never assume `main` retained prior semantics.

**Completion:** each finding has a record index and is accepted, corrected at the emitter, or documented as an intentional compatibility exception.

### 5. Build a migration diff

Produce a table with `old field/event`, `new field/event`, `source commit`, `affected emitters`, `affected queries`, `backfill decision`, and `removal date`. During a bounded dual-read window, dashboards may query both reviewed names, but emitters should not duplicate values indefinitely.

For token usage, confirm aggregate semantics before summing. Current pinned guidance says input totals include cache-read and cache-creation subtotals and output totals include reasoning subtotals. Adding both total and subtotal again double-counts usage.

**Completion:** the migration explicitly separates renamed fields, changed value semantics, and representation changes.

### 6. Gate content capture separately

OpenTelemetry's pinned guidance says model instructions, inputs, and outputs should not be captured by default. Require explicit opt-in, redaction tests, a positive truncation limit, access controls, retention, and deletion behavior. Prefer content references with separate authorization for production when available.

Never enable capture merely to make an observability test pass. A semantic-convention migration and a privacy-policy change are separate approvals.

**Completion:** disabled mode contains no content; enabled mode passes synthetic canary redaction and size-limit assertions.

### 7. Canary and rollback

Deploy to a bounded canary. Compare record counts by operation, error status, token totals, event/span representation, dropped-attribute metrics, envelope sizes, backend query results, and cost. Retain the old parser/dashboard until the canary proves parity. Roll back the emitter or collector version—not stored telemetry—if unknown fields, content leakage, or count divergence appears.

**Completion:** old and new paths agree on synthetic operation counts and inclusive token totals, and privacy probes show no unauthorized content.

## Objective Verification

Pass only when:

- every target profile is pinned to a canonical commit and access date;
- malformed, unknown-profile, and non-finite inputs fail closed;
- legacy names are surfaced rather than silently rewritten;
- operation/span-name fixtures cover inference and relevant agent/tool operations;
- token totals are not smaller than included subtotals and dashboards do not sum them twice;
- content-disabled fixtures contain no content attributes;
- content-enabled fixtures prove opt-in, redaction, truncation, access, and retention controls;
- a canary demonstrates query parity and rollback.

## Unsafe Operations and Recovery

- Never send raw prompts, responses, tool arguments, tokens, or credentials to an evaluation fixture.
- Never auto-rewrite stored telemetry or delete legacy dashboard fields.
- Never treat a profile on a moving branch as stable; pin a commit and refresh deliberately.
- If content leaked, stop capture/export, preserve only authorized audit evidence, invoke incident/privacy handling, rotate exposed secrets, and follow approved deletion procedures.
- If token counts jumped, freeze billing or SLO changes, compare raw provider usage with total/subtotal semantics, and restore the last verified dashboard query.
- If a canary emits unknown semantics, stop promotion and keep dual-read compatibility until a new profile and fixtures pass.

## Pitfalls

- Attribute stability can differ within the same GenAI convention document.
- Parser acceptance does not prove operation-to-attribute correctness.
- Events and span attributes may carry equivalent content in different SDKs; flattening them too early hides precedence and duplication.
- `gen_ai.usage.input_tokens` is a total, not a value to add to cache subtotals again.
- A JSON string containing structured messages is not equivalent to native structured attributes for every backend.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with machine-checkable assertions.

## Sources and Provenance

Sourced facts about field requirements, span names, inclusive token totals, development status, and opt-in content capture come from the OpenTelemetry GenAI semantic-conventions repository at commit `434c91dcc34ed038e3048c07720ddfed2c6bddfc`, accessed 2026-07-30. Issue reports provide factual demand evidence. The normalization schema, validator, migration gates, canary sequence, and safety thresholds are original recommendations.

- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
- [Pinned GenAI convention commit](https://github.com/open-telemetry/semantic-conventions-genai/commit/434c91dcc34ed038e3048c07720ddfed2c6bddfc)
- [OpenTelemetry Rust #3575: deprecated generated GenAI API lacks a clear replacement](https://github.com/open-telemetry/opentelemetry-rust/issues/3575)
- [Dify #36710: standardize workflow telemetry](https://github.com/langgenius/dify/issues/36710)
- [LangWatch #5900: promote event-based GenAI messages](https://github.com/langwatch/langwatch/issues/5900)
- [Sentry for AI #291: validate operation-to-attribute semantics](https://github.com/getsentry/sentry-for-ai/issues/291)
- [OpenTelemetry: GenAI observability in 2026](https://opentelemetry.io/blog/2026/genai-observability/)
