---
name: openapi-nullability-migration-conformance
description: Use when OpenAPI 3.0 nullable schemas are ignored, rewritten, or generate unusable types after an OpenAPI 3.1 migration. Inventory requiredness, null acceptance, references, composition, and fixtures offline before changing a contract.
version: "1.0.0"
license: MIT
---

# OpenAPI Nullability Migration Conformance

## When to Use

- An OpenAPI 3.0 `nullable: true` contract is being migrated to OpenAPI 3.1.
- A validator, client generator, or schema exporter disagrees about missing values versus explicit JSON `null`.
- A nullable `$ref`, composition, enum, or generated type changes across tools.
- A team needs a read-only inventory and fixture gate before accepting a contract rewrite.

Do **not** use for database-language nullability, ordinary application optionals, LLM structured-output provider subsets, or a contract with no OpenAPI dialect boundary.

## Prerequisites

- The exact OpenAPI JSON artifact sent to the affected tool. Convert YAML with a trusted project parser first; the helper intentionally parses JSON only.
- OpenAPI version, validator/generator name, and exact versions.
- Python 3.10+ for the standard-library-only offline helper.
- Synthetic positive and negative instances. Keep credentials and production payloads out of fixtures.

## Quick Reference

```bash
python3 scripts/audit_nullability.py openapi.json > nullability-report.json
# 0: no error findings; 1: report contains errors; 2: input failure; 3: output failure
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The helper never rewrites input. It emits stable JSON Pointers, finding codes, and independent `missing_allowed`/`null_allowed` property states.

## Standards Boundary

**Sourced facts:** OpenAPI 3.0.3 defines `nullable` as adding `null` to the allowed type only when `type` is explicitly defined in the same Schema Object. Its Reference Object cannot be extended with sibling fields. OpenAPI 3.1 aligns Schema Objects with JSON Schema 2020-12, where null is represented by a `null` type or a union containing it; `nullable` is not that vocabulary's keyword.

**Recommendations in this skill:** treat ambiguous 3.0 composition as non-portable, preserve the original, emit a migration plan rather than an automatic rewrite, and verify semantics with instances plus generated-type diffs.

## Procedure

### 1. Freeze dialect and intended instance states

Hash the original artifact and record the exact `openapi` value. For every affected property, fill this matrix before editing:

| State | Expected |
| --- | --- |
| property missing | accept/reject |
| property present as `null` | accept/reject |
| property present as ordinary valid value | accept |
| property present as wrong non-null type | reject |

Requiredness controls presence; nullability controls a present value. Never infer one from the other.

**Completion:** the original hash and all four outcomes are recorded independently.

### 2. Run the offline inventory

Run the helper on the emitted JSON contract and account for every finding:

- `NULLABLE_REF_SIBLING_IGNORED`: a 3.0 Reference Object sibling does not make the target nullable.
- `NULLABLE_WITHOUT_LOCAL_TYPE`: a 3.0 composition wrapper has no same-object type; do not assume portable null semantics.
- `NULLABLE_KEYWORD_OAS31`: a 3.1 schema retained the old keyword.
- `ENUM_NULL_WITHOUT_NULL_TYPE`: `enum` lists null while the type system excludes it.
- structural codes: malformed `type`, `required`, `properties`, schema maps, or composition.

A warning is unresolved portability evidence, not permission to rewrite. The helper does not resolve external references or claim full JSON Schema validation.

**Completion:** each pointer is mapped to intended missing/null/non-null behavior and an owner.

### 3. Choose a reviewable 3.1 representation

Use the smallest representation that preserves the frozen instance states:

```yaml
# required and nullable string
required: [nickname]
properties:
  nickname:
    type: [string, "null"]

# nullable reference when the target itself must remain unchanged
properties:
  pet:
    anyOf:
      - $ref: '#/components/schemas/Pet'
      - type: "null"
```

A `type` array is concise for simple types. A union branch is useful around references or structurally distinct alternatives. Preserve annotations, constraints, discriminator behavior, defaults, examples, `readOnly`/`writeOnly`, and request/response direction. Do not mechanically wrap every schema or translate `nullable: false` into a new constraint.

**Completion:** a separate candidate artifact has a pointer-level rationale and the original remains byte-identical.

### 4. Validate semantics, not syntax alone

Use a complete Draft 2020-12/OpenAPI 3.1 validator from the project for the candidate. For every property, test missing, null, valid non-null, and invalid non-null instances. An expected-invalid fixture counts only when it parses and fails for the intended assertion.

Then run every downstream validator and generator against both artifacts. Compare:

```text
pointer | original accepted states | candidate accepted states | generated source type | direction | verdict
```

A generated optional type can conflate “missing” and “present null.” Confirm encoder and decoder behavior, not only a type alias.

**Completion:** application validation and generated-client behavior preserve the frozen matrix, or the migration is blocked.

### 5. Gate rollout and recover safely

Publish only after semantic fixtures, generated diffs, and contract-owner review pass. Version the contract when consumers cannot accept the new dialect or union shape. Retain the old artifact and generator lockfile/configuration for rollback.

If a tool ignores 3.1 unions, do not put `nullable` back into a 3.1 schema and call it portable. Pin or replace the tool, maintain an explicitly labeled projection, or delay migration while preserving application validation.

## Failure Recovery

| Failure | Safe response |
| --- | --- |
| `$ref` sibling worked in one 3.0 tool | Treat it as implementation-specific; model null with a wrapper/union and add a cross-tool fixture. |
| 3.1 type array becomes `unknown` | Try an equivalent reviewed union only if semantics stay equal; otherwise block that generator. |
| Required nullable field becomes optional | Restore `required`, add missing-versus-null fixtures, and regenerate all clients. |
| Validator accepts `enum: [null]` unexpectedly | Check the type vocabulary and validator mode; require the null type explicitly. |
| Candidate weakens another constraint | Restore the original, isolate the nullability change, and rerun all negative fixtures. |
| Input or output error | Exit codes 2/3 are infrastructure failures, never evidence of conformance. |

## Pitfalls and Unsafe Operations

- Never rewrite a production contract in place or infer intent from generator output.
- Do not treat OpenAPI 3.0 `nullable` as a general JSON Schema keyword.
- Do not assume a composition wrapper inherits a local `type` for 3.0 nullability.
- Do not equate absent, omitted-on-encode, defaulted, and explicit null.
- Do not copy customer examples, tokens, or sensitive defaults into fixtures or reports.
- Do not claim the helper is a complete OpenAPI or JSON Schema validator.

## Objective Verification

A complete migration produces: an immutable original hash; a helper report with explained findings; a four-state fixture matrix per affected property; full-validator results; generated source and encoder/decoder diffs; explicit approvals; and a rollback artifact. Run the bundled tests and require zero failures after helper changes.

## Evaluation Prompts

1. **Normal:** Migrate a required nullable string and an optional non-null string from OpenAPI 3.0.3 to 3.1 without conflating missing and null.
2. **Difficult edge:** Diagnose a nullable 3.0 `$ref` sibling, an `allOf` wrapper without local type, and an enum containing null; produce intended-reason fixtures before proposing 3.1 forms.
3. **Should not activate:** Explain whether a nullable PostgreSQL column permits an omitted value and explicit SQL `NULL`.

## Sources

- [OpenAPI Specification 3.0.3](https://spec.openapis.org/oas/v3.0.3.html)
- [OpenAPI Specification 3.1.2](https://spec.openapis.org/oas/v3.1.2.html)
- [Safe Settings issue 1024 — 3.0 nullable ignored under Draft 2020-12](https://github.com/github-community-projects/safe-settings/issues/1024)
- [Orval issue 3714 — invalid nullable reference forms](https://github.com/orval-labs/orval/issues/3714)
- [Swift OpenAPI Generator issue 906 — nullable referenced schema generation](https://github.com/apple/swift-openapi-generator/issues/906)
- [Massimo issue 170 — 3.1 type arrays generated as unknown](https://github.com/platformatic/massimo/issues/170)

All instructions, code, and fixtures are original synthesis. Sources provide specification facts and demand evidence only; no third-party code or prose is copied.
