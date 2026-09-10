---
name: http-content-encoding-chain-conformance
description: Use when HTTP clients, proxies, or tests mishandle repeated or comma-listed Content-Encoding values, stacked gzip/deflate bodies, unknown codings, or decompression limits; validates the complete chain before bounded inverse decoding.
version: "1.0.0"
license: MIT
---

# HTTP Content-Encoding Chain Conformance

## When to Use

- A client returns compressed bytes or decode errors for stacked `Content-Encoding` values.
- A proxy combines repeated field lines and only decodes one layer.
- You need a bounded, offline fixture proving coding order and inverse decoding.
- You are comparing runtime behavior for unknown, malformed, or repeated codings.

Do **not** use this for `Transfer-Encoding`, HTTP message framing, media-type-inherent compression, archive extraction, or tuning `Accept-Encoding` preferences.

## Prerequisites

- Python 3.9+ for the bundled standard-library analyzer.
- A redacted fixture containing raw `Content-Encoding` field values and synthetic body bytes.
- Explicit local resource limits. The RFC defines coding semantics, not universal byte, ratio, or chain-depth budgets.

## Quick Reference

```bash
python3 scripts/check_content_encoding.py fixture.json
python3 -m unittest discover -s tests -p 'test_*.py'
```

Input:

```json
{
  "field_lines": ["gzip", "deflate"],
  "body_base64": "...",
  "policy": {
    "max_chain": 4,
    "max_encoded_bytes": 1048576,
    "max_output_bytes": 8388608,
    "max_expansion_ratio": 100.0
  }
}
```

`body_base64` may be omitted for preflight-only analysis. Add `transfer_encoding` only to prove that a fixture is out of scope when `field_lines` is empty.

## Procedure

### 1. Capture without normalizing away evidence

Record each received `Content-Encoding` field line in arrival order. Do not sort, deduplicate, or infer a chain from the body magic bytes. Use synthetic payloads; never put credentials or production bodies in fixtures.

**Complete when:** the ordered field-line array is preserved.

### 2. Parse the complete list before decoding

Combine field lines in arrival order, split each list at commas, trim optional whitespace, and validate each member as an HTTP token. Reject empty members, non-string values, unknown codings, and chains over the declared cap before decoding any layer. Coding names are case-insensitive.

RFC 9110 section 8.4 says the sender lists codings in application order. Therefore decode from the final member back to the first. Repeated codings are distinct transformations. `identity` is reserved for `Accept-Encoding` and SHOULD NOT appear in `Content-Encoding`; this analyzer rejects it rather than silently treating it as a layer.

**Complete when:** the report shows both application and inverse order and preflight failures have zero transitions.

### 3. Decode with explicit policy

The helper supports `gzip`, `x-gzip`, and RFC zlib-wrapped `deflate`. It bounds encoded bytes, every decoded intermediate, final expansion ratio, and chain depth. It rejects truncated streams and trailing or concatenated members rather than selecting an implementation-specific interpretation.

Unknown coding is a whole-chain failure. Do not decode an outer supported layer and expose the partial result as representation data: it is still encoded by the unknown transformation.

**Complete when:** every transition records only coding, input/output sizes, and SHA-256; no decoded content is logged.

### 4. Compare the real runtime separately

Run the same synthetic fixture through the application client with automatic decoding both enabled and disabled. Compare:

- parsed chain and field-line combination;
- final digest and length;
- handling of unknown codings and malformed lists;
- resource-limit behavior.

Label runtime behavior as **observed**. A pass by this helper does not prove the production client applies the same policy.

### 5. Recover safely

On failure, preserve the encoded synthetic fixture and report. Prefer rejecting or negotiating `Accept-Encoding: identity` where appropriate over guessing, skipping a coding, or repeatedly decompressing until bytes “look right.” Raise limits only after reviewing trusted payload sizes; do not disable bounds globally.

## Verification

A valid result has `status: "decoded"`, the expected final digest, and one transition per coding in inverse order. A preflight rejection has `status: "rejected"`, a stable `reason`, and `transitions: []`. Exit codes are 0 for decoded/not-applicable/preflight-only results, 2 for invalid input or conformance rejection, and 3 for output-write failure.

Minimum fixture matrix:

1. repeated field lines and one comma-list produce the same ordered chain;
2. `gzip, deflate` decodes `deflate` then `gzip` to the expected digest;
3. chain count exactly at the cap passes and cap + 1 fails;
4. unknown and empty members fail before transitions;
5. truncated, trailing-member, output-cap, and ratio-cap cases fail closed;
6. absent `Content-Encoding` plus `Transfer-Encoding: chunked` is `not_applicable`.

## Pitfalls and Safety

- Do not confuse application order with decode order.
- Do not treat repeated field names as one opaque coding token.
- Do not skip unknown codings or trust partially decoded bytes.
- Do not call `deflate` a raw DEFLATE stream; RFC 9110 defines the zlib format.
- Do not claim chain/output/ratio caps are RFC mandates; they are local policy.
- Do not use unbounded convenience decompression on untrusted bytes.

## Evaluation Prompts

- **Normal:** Verify a doubly gzipped synthetic JSON body supplied through two `Content-Encoding: gzip` field lines; return transitions and final digest.
- **Difficult edge:** Preflight `gzip, x-unknown` plus `deflate` at an exact chain cap of three; prove no partial output is trusted and distinguish RFC semantics from policy.
- **Should not activate:** Diagnose a response with only `Transfer-Encoding: chunked`; explain why content-chain validation is out of scope.

## Sources

Sourced facts:

- [RFC 9110 §8.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.4) defines `Content-Encoding` as a list in application order and distinguishes it from `Transfer-Encoding`.
- [aiohttp issue #13364](https://github.com/aio-libs/aiohttp/issues/13364), [workerd issue #7051](https://github.com/cloudflare/workerd/issues/7051), and [urllib3 issue #1441](https://github.com/urllib3/urllib3/issues/1441) document independent stacked-coding interoperability failures.

Recommendations such as fail-closed unknown-coding handling, no concatenated members, and the numeric resource limits are explicit local safety policy, not claims that RFC 9110 mandates those choices.
