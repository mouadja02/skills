---
name: w3c-baggage-propagation-conformance
description: Use when W3C Baggage members disappear across hops, repeated baggage fields are only partly read, percent encoding changes values, metadata is rewritten, or propagation limits disagree.
version: "1.0.0"
license: MIT
---

# W3C Baggage Propagation Conformance

## When to Use

- Repeated `baggage` HTTP field lines lose members during extraction or injection.
- `%` escapes, UTF-8 values, `=` inside values, or property metadata differ across runtimes.
- A gateway, SDK, or service applies the 64-member and 8192-byte boundaries incorrectly.
- Duplicate keys or member dropping produce cross-runtime drift.

Do **not** use for `traceparent`/`tracestate` sampling, generic request headers, or deciding what sensitive application data should be placed in baggage.

## Prerequisites

- Exact SDK/runtime versions and a synthetic or redacted capture from each hop.
- Python 3.10+ for the offline standard-library analyzer.
- Current W3C Baggage and OpenTelemetry propagator specifications reopened before production decisions.

## Quick Reference

```bash
SKILL_DIR=skills/api-backend/w3c-baggage-propagation-conformance
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/analyze_baggage.py" trace.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$SKILL_DIR/tests" -p 'test_*.py' -v
```

Exit `0` means `ready` or `not_applicable`; exit `1` means parsed baggage is `blocked`; exit `2` means input/schema/output failure, not a conformance result.

## Procedure

### 1. Capture field values without secrets

Record every received and forwarded `baggage` field value in arrival order. Omit the field name. Use synthetic opaque identifiers; baggage can expose user or tenant data across service boundaries.

**Completion:** the trace identifies each hop/runtime and contains no credentials or production values.

### 2. Combine repeated fields before parsing

Treat all repeated field values as one comma-separated baggage-string. Never use an API that returns only the first value. Split list-members before percent-decoding because encoded delimiters belong to a value.

**Completion:** member count includes every field line and preserves duplicate-key order.

### 3. Validate grammar and percent encoding

Keys use HTTP `token`. Values use the ASCII `baggage-octet` set; characters outside it must be UTF-8 percent-encoded. A literal percent must itself be encoded, so `%ZZ` is invalid. Decode valid percent octets as UTF-8 and replace invalid UTF-8 sequences with U+FFFD. Split key/value only at the first raw `=`; decoded values may contain any number of equals signs.

**Completion:** malformed percent syntax is a finding, `version%3Dv2` decodes to `version=v2`, and malformed input is never guessed.

### 4. Keep properties opaque

Validate `;key` and `;key=value` property grammar, trim surrounding OWS, and preserve property value bytes. W3C gives properties no universal meaning. Do not apply value decoding/re-encoding to the entire metadata string merely because an SDK calls it metadata.

**Completion:** extract/inject does not silently percent-rewrite property delimiters or opaque property values.

### 5. Apply both combined limits independently

At 64 members or fewer **and** 8192 UTF-8 bytes or fewer, the platform must be capable of propagating all members, including added members. The limits apply to the combination of all field lines. Above either boundary, a platform may drop members until its supported limits are met; it must not truncate a member. Which members are dropped and their order are implementation policy, not a universal invariant. Implementations may support higher limits.

**Completion:** tests cover 64/65 members and 8192/8193 bytes separately without treating either minimum capacity as a universal maximum.

### 6. Compare the propagation transition

Compare logical `(key, decoded value, opaque properties)` tuples in order. Under both minimum boundaries, unexplained loss is blocked. If the application intentionally adds, updates, deletes, or deduplicates baggage, record that mutation explicitly; do not mislabel declared application policy as transport loss.

**Completion:** a safe control preserves all undeclared members, while a one-field-only extraction fixture fails.

### 7. Repair and rerun

Fix the earliest boundary: multi-value carrier, grammar parser, value encoder, metadata handling, or explicit limit/drop policy. Rerun repeated-field, percent, UTF-8, property, duplicate, exact-boundary, loss, and not-applicable fixtures.

**Completion:** helper classification is `ready`, packaged tests pass, and any later staging probe is bounded and redacted.

## Findings and Observations

| Code | Meaning |
| --- | --- |
| `invalid_list_member` | A parsed member violates key, value, percent, or property grammar. |
| `undeclared_member_loss_under_limits` | A source member disappeared while both minimum-capacity conditions held. |
| `combined_limits` | Observation reporting member/byte counts and each boundary independently. |
| `forwarded_member_count` | Observation only; count alone does not identify which member changed. |

## Failure Recovery and Pitfalls

- **Exit 2:** repair I/O, JSON, or schema first; this is not expected-invalid protocol evidence.
- **First-value APIs:** use a multi-value accessor or explicitly join all field values.
- **Decode before split:** unsafe; `%3D` and other escapes must remain inside their member during structural parsing.
- **Properties:** preserve them as opaque validated metadata; do not assume all language APIs model each property separately.
- **Limits:** 64 and 8192 are minimum propagation capabilities, not mandatory rejection maxima.
- **Duplicates:** uniqueness is not guaranteed; preserve order unless a declared mutation policy deduplicates.
- **Privacy:** stop and recapture if baggage includes personal data, authorization material, or tenant secrets.
- **Production mutation:** the helper is offline and never sends or rewrites headers.

## Objective Verification

A complete run proves repeated-field discovery, strict percent grammar, UTF-8 replacement, first-equals parsing, opaque properties, duplicate order, independent combined limits, whole-member handling, declared versus unexplained mutation, malformed-input fail-closure, and a trace-context-only negative activation case.

See the [trace schema](references/trace-schema.md) and [evaluation prompts](references/evaluations.md).

## Sources and Scope

Header grammar, encoding, mutation, and minimum propagation limits are sourced facts. Redaction, explicit mutation ledgers, and fail-closed rollout are safety recommendations. This is original synthesis; no source code or issue prose was copied. OpenTelemetry repositories and specifications are Apache-2.0.

- [W3C Baggage Recommendation](https://www.w3.org/TR/baggage/)
- [OpenTelemetry propagators specification](https://opentelemetry.io/docs/specs/otel/context/api-propagators/)
- [Java property metadata encoding issue](https://github.com/open-telemetry/opentelemetry-java/issues/6771)
- [Go repeated-header issue](https://github.com/open-telemetry/opentelemetry-go/issues/6154)
- [Go equals-sign value issue](https://github.com/open-telemetry/opentelemetry-go/issues/5840)
- [.NET space-encoding issue](https://github.com/open-telemetry/opentelemetry-dotnet/issues/5260)
- [Swift percent-encoding issue](https://github.com/open-telemetry/opentelemetry-swift/issues/761)