# Provider Profile Notes

Checked 2026-07-18 unless a source gives a more specific update date. These are sourced facts, followed by curator recommendations. Reopen official documentation before a production migration.

## OpenAI strict structured outputs

**Sourced facts:** The official guide says the root must be an object and not a top-level `anyOf`; all fields must be required; every object must set `additionalProperties: false`; schemas may contain at most 5,000 object properties and 10 nesting levels. It lists `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, and `else` as unsupported. Fine-tuned models have additional keyword restrictions.

**Profile behavior:** `openai` checks those stable shape rules, limits, and generally unsupported composition keywords. It does not assume the additional fine-tuned-model restrictions apply to every model.

**Recommendation:** Treat model eligibility, enum/string-size limits, and fine-tuned-model rules as deployment-tuple checks. Do not auto-require formerly optional fields.

Source: [OpenAI — Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Amazon Bedrock

**Sourced facts:** The official guide describes a JSON Schema Draft 2020-12 subset. It lists basic types, `enum`, `const`, `anyOf`, limited `allOf`, internal references, named string formats, and `minItems` values 0 or 1. It lists recursive schemas, external references, numerical constraints, `minLength`, `maxLength`, and `additionalProperties` values other than `false` as unsupported. Unsupported schemas return an immediate 400. API surface and model support matter.

**Profile behavior:** `bedrock` rejects the listed unsupported numeric/string constraints, external references, non-0/1 `minItems`, and objects not explicitly closed. It warns that the helper does not prove absence of recursive reference cycles.

**Recommendation:** Use the exact Bedrock API surface and model table; stop retrying deterministic schema-validation 400s.

Source: [Amazon Bedrock — Get validated JSON results from models](https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html)

## Gemini API

**Sourced facts:** The official page documents a subset with primitive types; `title` and `description`; object `properties`, `required`, and `additionalProperties`; string `enum` and `format`; numeric `enum`, `minimum`, and `maximum`; and array `items`, `prefixItems`, `minItems`, and `maxItems`. It warns that not all JSON Schema features are supported and that very large or deeply nested schemas may be rejected. The page showed “Last updated 2026-07-07 UTC” when checked.

**Profile behavior:** `gemini` uses the documented list as a conservative allowlist. Unlisted annotation keywords warn; unlisted behavioral keywords error. It always warns about unspecified complexity limits.

**Recommendation:** An allowlist error means “not documented by this snapshot,” not proof that every model rejects it. Preserve the constraint in the original validator and confirm with a bounded probe.

Source: [Google AI for Developers — Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)

## vLLM

**Sourced facts:** vLLM documents structured-output options, but actual enforcement has varied by guided-decoding backend, version, model, and schema keyword. A 2026 issue reports a case where a string `pattern` caused an array-item `maxLength` constraint not to be enforced.

**Profile behavior:** `vllm` intentionally emits a backend-dependency warning rather than a brittle static allowlist.

**Recommendation:** Record version/model/backend and run a negative enforcement probe. Valid JSON alone is insufficient.

Sources:

- [vLLM — Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [vLLM issue #45592 — pattern on string items causes maxLength to be ignored](https://github.com/vllm-project/vllm/issues/45592)

## Cross-project demand evidence

These issue reports are factual evidence only; do not copy their code or prose:

- [Vercel AI issue #17197 — Bedrock rejects forwarded `maxItems`](https://github.com/vercel/ai/issues/17197)
- [LangChain issue #38223 — nested strict schema missing required closure metadata](https://github.com/langchain-ai/langchain/issues/38223)
- [Pydantic AI issue #6471 — transformation skipped for profile-default native output](https://github.com/pydantic/pydantic-ai/issues/6471)
- [vLLM issue #45592 — accepted schema does not enforce all constraints](https://github.com/vllm-project/vllm/issues/45592)

## Technical basis and licensing

[JSONSchemaBench (arXiv:2501.10868)](https://arxiv.org/abs/2501.10868) evaluates structured-output frameworks on coverage, quality, and efficiency, supporting differential tests rather than “valid JSON” checks alone. Its [official repository](https://github.com/guidance-ai/jsonschemabench) declared no SPDX license through GitHub when checked; this skill copies neither its prose nor its code. The Hugging Face paper page was used only as a discovery cross-check: [paper 2501.10868](https://huggingface.co/papers/2501.10868).

The provider documentation linked above is cited for factual claims. This skill and helper are original MIT-licensed work and bundle no third-party code.
