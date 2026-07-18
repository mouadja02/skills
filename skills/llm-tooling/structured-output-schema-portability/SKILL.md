---
name: structured-output-schema-portability
description: Use when an LLM JSON Schema works with one structured-output provider but is rejected, weakened, or ignored by another — inventory constraints, preflight provider subsets, preserve semantics, and verify with fixtures before live calls.
version: "1.0.0"
license: MIT
---

# Structured Output Schema Portability

## When to Use

- A JSON Schema is accepted by one LLM provider but returns a schema-validation error on another.
- Generated JSON is syntactically valid but violates constraints such as `maxLength`, `pattern`, or nested object closure.
- A Pydantic, Zod, or other generated schema must target OpenAI strict output, Amazon Bedrock, Gemini, or vLLM.
- A team needs an offline preflight and fixture gate before spending credentials or provider calls.

Do **not** use this skill for ordinary API response validation, OpenAPI design, database schemas, prompt-only formatting, or choosing a model. If only one provider is involved, its current official documentation remains authoritative.

## Prerequisites

- The exact emitted JSON Schema, after framework conversion—not only the source Pydantic/Zod model.
- Python 3.10+ for the bundled, standard-library-only helper.
- At least one valid and one invalid JSON fixture representing the application contract.
- Exact provider API surface, model, SDK, and (for vLLM) server version/backend before a live probe.

## Quick Reference

```bash
SKILL_DIR=skills/llm-tooling/structured-output-schema-portability

# Inventory and structural checks only
python3 "$SKILL_DIR/scripts/schema_preflight.py" schema.json

# Conservative provider snapshot; nonzero means errors or fixture failures
python3 "$SKILL_DIR/scripts/schema_preflight.py" schema.json \
  --profile openai \
  --fixture fixtures/valid.json \
  --invalid-fixture fixtures/too-many-items.json \
  --report json > preflight.json

# Produce a reviewable candidate that only closes objects; never overwrite input
python3 "$SKILL_DIR/scripts/schema_preflight.py" schema.json \
  --profile bedrock \
  --write-tightened schema.bedrock.candidate.json
```

Profiles are dated conservative snapshots, not claims that a schema will compile for every model. Unknown or backend-dependent behavior must go to a bounded live probe.

## Procedure

### 1. Freeze the contract and deployment tuple

Record:

```text
schema SHA-256:
provider / API surface:
model ID and version:
SDK or framework version:
vLLM version + guided-decoding backend (if applicable):
positive fixtures:
negative fixtures:
```

Keep the original schema immutable. Export the schema actually sent over the wire and redact prompts, customer data, credentials, and headers. A source model and its emitted schema can differ.

**Completion:** the schema file is parseable JSON, its hash is recorded, and each target has an exact deployment tuple.

### 2. Inventory before transforming

Run the helper once with `--profile generic`. Review keyword inventory, reference style, object count, and nesting depth. Then run once per target profile.

Classify each finding:

- **Unsupported:** the profile documents rejection or cannot express the keyword.
- **Required shape:** provider rules such as closed objects or all fields required.
- **Uncertain:** model, API, version, or backend dependent; do not silently treat it as supported.
- **Application-only:** semantic rules that must remain in the original validator even if removed from a provider schema.

See [provider profile notes](references/provider-profiles.md) before acting on a finding.

**Completion:** every original keyword is mapped to provider-enforced, application-enforced, or unresolved.

### 3. Choose a response per constraint

Use this order; stop at the first acceptable option:

1. **Preserve:** keep the keyword when the exact target documents support.
2. **Reshape without weakening:** for example, move a root union under a required object property.
3. **Tighten with review:** `--write-tightened` adds missing `additionalProperties: false`. It never overwrites the source and reports each changed pointer. Confirm that rejecting unknown keys is intended.
4. **Move enforcement to the application:** omit a provider-unsupported keyword only from the provider schema, while retaining it in the immutable original validator.
5. **Use a documented fallback:** tool calling, JSON mode plus validation/retry, or a target-specific schema.
6. **Reject portability:** if a business invariant cannot be preserved, do not claim the schema is portable.

Never delete constraints merely to make a 400 response disappear. Never add missing properties to `required` automatically. OpenAI's documented nullable-union pattern changes the output contract and requires an explicit application decision.

**Completion:** each change has a reason, semantic impact, owner, and rollback.

### 4. Build a schema family, not one lossy common denominator

Store separate artifacts:

```text
schema.original.json            # application truth
schema.openai.json              # provider projection
schema.bedrock.json             # provider projection
schema.gemini.json              # provider projection
fixtures/valid/*.json
fixtures/invalid/*.json
```

Generate projections deterministically from the original when practical. Review diffs. Do not replace the original validator with a provider subset.

For optional fields under OpenAI strict output, decide explicitly between:

- required + nullable output, followed by application normalization;
- a redesigned envelope;
- another output mode/provider fallback.

**Completion:** no provider projection silently weakens the application contract.

### 5. Run differential fixtures offline

The helper's fixture validator covers common types, properties, required fields, closed objects, enums, constants, bounds, arrays, `anyOf`, `allOf`, and internal `$ref`. It is a smoke test, not a complete Draft 2020-12 implementation. Use the project's full JSON Schema validator for production gating.

For every projection:

1. positive fixtures pass the **original** validator;
2. positive fixtures pass the projection validator;
3. each negative fixture fails the original validator for the intended reason;
4. if a negative fixture passes a provider projection, application post-validation must reject it;
5. transformed-schema diffs contain only approved changes.

Use `--fixture` for expected-valid instances and `--invalid-fixture` for expected-invalid instances. The JSON report records expected versus observed validity and makes a mismatched expectation return nonzero. Review each invalid fixture's error list to confirm it failed for the intended reason.

**Completion:** a machine-readable matrix identifies which layer rejects every negative fixture.

### 6. Run one bounded live compile/request probe

Only after offline checks, submit the smallest schema and benign fixture to the exact deployment tuple. Capture status, provider request ID, and redacted error class—not tokens or full payloads. Cap retries; a deterministic 400 is not transient.

For vLLM, this step is mandatory because supported behavior depends on server version, model, and guided-decoding backend. Test both a positive output and a constraint-targeting negative case; successful JSON parsing alone does not prove enforcement.

**Completion:** the exact target either accepts and enforces the projection, or the fallback is selected.

### 7. Gate and monitor

Promote only when:

- schema hashes and profile snapshot dates are recorded;
- offline original/projection tests pass;
- live probe behavior matches the matrix;
- unsupported constraints retain application validation;
- provider errors and post-validation failures are observable;
- rollback restores the previous schema or output mode.

Re-run after provider/model/SDK/vLLM-backend changes. Time-sensitive claims belong in [provider profile notes](references/provider-profiles.md), not in assumptions embedded across application code.

## Failure Recovery

| Failure | Safe response |
| --- | --- |
| Immediate provider 400 | Stop retries; compare the exact emitted schema and provider profile. |
| Valid JSON violates a constraint | Treat constrained decoding as unproven; keep original post-validation and test the exact backend. |
| Framework schema differs from source model | Export after all framework transformers; diff before provider submission. |
| Tightening rejects historical payloads | Keep the candidate separate, restore the original, and obtain contract-owner approval. |
| Provider docs do not specify a keyword | Mark unresolved and use a bounded probe or application-only enforcement. |
| Recursive or external references | Bundle intentionally or redesign; do not let the helper's smoke validator stand in for full resolution. |

## Safety and Pitfalls

- Never put bearer tokens, API keys, prompts, customer payloads, or authorization headers in fixtures or reports.
- Never infer constraint enforcement from one successful response.
- Do not use a universal intersection schema when separate projections preserve more intent.
- `additionalProperties: false` is semantic tightening, not formatting cleanup.
- Provider profiles drift. Verify dated notes against official documentation before a production migration.
- Generated schemas can hide nested `$defs` errors; inspect the emitted artifact recursively.
- Do not execute code or installers from benchmark or issue repositories. They are evidence, not dependencies.

## Objective Verification

A complete run produces:

- immutable original schema hash;
- per-target preflight JSON with zero unexplained errors;
- reviewed projection diffs;
- positive and negative original-validator results;
- one redacted live probe result per exact deployment tuple;
- explicit ownership for application-only constraints;
- rollback command or configuration.

Run bundled offline tests after modifying the helper:

```bash
python3 -m unittest discover \
  -s "$SKILL_DIR/tests" -p 'test_*.py' -v
```

## Evaluations

Three activation and behavior checks are documented in [references/evaluations.md](references/evaluations.md): normal portability failure, difficult semantic-preservation edge case, and a should-not-activate OpenAPI task.

## Sources and Scope

The procedure is original synthesis. Provider facts and snapshot dates are cited in [provider profile notes](references/provider-profiles.md). Demand evidence comes from independent Vercel AI SDK, vLLM, LangChain, and Pydantic AI issue reports. JSONSchemaBench motivates differential enforcement testing but no prose or code is copied; its repository had no declared SPDX license when checked, so it is evidence only.
