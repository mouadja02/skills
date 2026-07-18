# Evaluation Prompts

Use a fresh agent context for baseline (without this skill) and treatment (with this skill). Do not make provider calls. Grade only observable artifacts and commands.

## 1. Normal: Bedrock rejection during provider migration

**Prompt**

> Our Zod-generated schema works with Gemini but Amazon Bedrock returns `maxItems is not supported`. It has nested objects and optional fields. Give me a safe migration plan and an offline preflight command. Do not use credentials or make network calls.

**Deterministic assertions**

- Activates this skill.
- Requests the exact emitted schema and deployment tuple.
- Identifies provider projections plus immutable original validation, rather than deleting `maxItems` globally.
- Uses `schema_preflight.py --profile bedrock` and records a nonzero preflight as a finding, not a transient failure.
- Requires positive and negative fixtures and a bounded later live probe.
- Does not print or request credentials.

## 2. Difficult edge: accepted schema but weakened enforcement

**Prompt**

> vLLM accepts this Draft 2020-12 schema, but values sometimes exceed `maxLength` when `pattern` is present under array items. We also target OpenAI strict output, where the root is a discriminated union and several properties are optional. Make one portable schema automatically and tell us it is guaranteed.

**Deterministic assertions**

- Refuses the guarantee and does not create a silently weakened universal schema.
- Calls out vLLM version/model/backend dependence and requires a negative enforcement probe.
- Detects OpenAI's top-level union, closed-object, and all-fields-required constraints.
- Treats required-plus-nullable as an explicit semantic decision, not an automatic rewrite.
- Keeps original and target projections, with application post-validation for unsupported constraints.
- Provides rollback criteria.

## 3. Should not activate: ordinary OpenAPI authoring

**Prompt**

> Design an OpenAPI 3.1 schema for our invoice REST endpoint. No LLM or structured-output provider is involved.

**Deterministic assertions**

- Does not activate this skill.
- Does not introduce provider profiles, LLM live probes, or constrained-decoding advice.
- Routes to ordinary OpenAPI/API-schema guidance.

## Scoring

Each assertion is pass/fail. A treatment response passes an evaluation only if every assertion passes. Compare the baseline and treatment by listing newly satisfied assertions; do not invent percentages, latency, or model-quality metrics.
