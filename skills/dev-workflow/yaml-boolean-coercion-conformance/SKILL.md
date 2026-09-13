---
name: yaml-boolean-coercion-conformance
description: Use when YAML values such as yes/no/on/off change type across PyYAML, Go, SnakeYAML, OmegaConf, Helm, or generated schemas and need a byte-preserving YAML 1.1-versus-1.2 audit.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# YAML Boolean Coercion Conformance

Audit the presentation bytes before a parser erases whether a scalar was plain or quoted. Keep lexical evidence, schema resolution, and application type validation separate.

## When to Use

- A string enum such as `no`, `on`, or `off` becomes a native boolean.
- Identical YAML bytes produce different values across parsers, generators, or runtimes.
- A migration from YAML 1.1-compatible resolution to YAML 1.2 needs a fixture-backed gate.
- Boolean-like mapping keys may collide after construction.

Do **not** activate for JSON/TOML, ordinary explicit `true`/`false` configuration, general YAML formatting, or duplicate-key analysis.

## Prerequisites

- Python 3.9+; the offline scanner uses only the standard library.
- The exact YAML bytes and the parser/version/schema options used by every producer and consumer.
- Synthetic fixtures or a redacted copy. The helper reads data only and never constructs YAML objects or executes tags.

## Quick Reference

```bash
python3 scripts/audit_yaml_booleans.py config.yaml
python3 scripts/audit_yaml_booleans.py config.yaml --output report.json
python3 tests/test_audit_yaml_booleans.py
```

Exit codes: `0` no legacy-only spellings, `1` audit completed with YAML 1.1-only boolean spellings, `2` unreadable/unsupported/malformed input, `3` report write failure.

## Procedure

### 1. Freeze the parser contract

Record exact bytes, digest, producer, parser library/version, declared YAML version, resolver/schema, and target application type. Do not infer schema behavior from a `.yaml` suffix. Preserve quotes and scalar style.

### 2. Inventory plain boolean spellings

Run the helper before parsing. It reports standalone unquoted plain scalars in mapping keys/values and block/flow sequences, while ignoring comments, quoted values, block-scalar content, and substrings such as `/on/off`.

- `legacy_only_boolean`: `y`, `yes`, `n`, `no`, `on`, `off`, case-insensitively. YAML 1.1's boolean type resolves these; YAML 1.2 core resolves them as strings.
- `stable_boolean`: `true` or `false`, case-insensitively. Both compared schemas resolve these as booleans.

The scanner is a bounded lexical gate, not a complete YAML parser. A clean report does not prove the document is valid YAML.

### 3. Prove the differential with real parsers

Parse the same immutable fixture with every deployed parser and record native type and value by path. Include at least:

1. each legacy-only spelling in lower, title, and upper case;
2. mapping keys and values;
3. block and flow collections;
4. quoted controls that must remain strings;
5. explicit `true`/`false` controls;
6. application enums whose legal string value is `no`, `on`, or `off`.

Never label a parser “YAML 1.1” or “YAML 1.2” from product reputation alone; record the selected resolver/schema options.

### 4. Recover at the ownership boundary

If the application requires a string, quote the source scalar at the producer boundary and retest every consumer. If it requires a boolean, emit canonical `true`/`false`. For command-line overlays that parse values as YAML, document a byte-preserving string escape or use a typed interface. Do not patch already-constructed booleans back into strings by spelling guesswork: quotation evidence is gone.

Rollback is the original bytes plus the previous parser/schema tuple. Do not rewrite production configuration automatically.

## Objective Verification

Completion requires:

- the helper parses successfully and reports exact line, column, spelling, role, and resolution class;
- every expected legacy-only fixture is found and quoted/comment/block-scalar controls are absent;
- real parser outputs record both native type and value for identical bytes;
- repaired string fields remain strings across all target consumers;
- explicit boolean fields remain booleans;
- malformed, unreadable, NUL-bearing, and unbalanced-flow inputs fail closed.

## Pitfalls and Safety

- Quoting is semantic evidence. Audit before construction or re-serialization.
- `yes please`, `/on/off`, and quoted `"no"` are strings, not standalone implicit booleans.
- A mapping key coerced to `True` can collide with another key after construction; inspect keys too.
- YAML 1.2 permits application-specific schemas. “1.2 document” alone does not prove core-schema resolution.
- Keep adjacent coercion classes—nulls, timestamps, octal/sexagesimal numbers, and duplicate keys—out of this audit unless separately scoped.

## Evaluation Prompts

1. **Normal:** Audit block and flow YAML containing plain `yes`, `no`, `ON`, an ambiguous key `off`, and quoted controls; return ordered machine-readable findings.
2. **Difficult:** Audit comments, literal block content, flow keys/values, `true`/`false`, URL substrings, and a second document; report only standalone plain scalars with exact coordinates.
3. **Should not activate:** Inspect a JSON object whose quoted key is `on`; decide whether this YAML-specific audit applies.

## Sources and Fact/Policy Boundary

**Sourced facts:** YAML 1.1's boolean type lists `y/yes/n/no/true/false/on/off` spellings case-insensitively. YAML 1.2.2 core tag resolution recognizes only `true/false` as booleans. Kubeflow, urfave, MELT, and Cozystack records demonstrate cross-version coercion failures in independent systems.

**Recommendations:** the offline pre-construction gate, input cap, fail-closed policy, canonical-emission rule, and recovery workflow are original conservative operating policy.

- [YAML 1.1 boolean type working draft](https://yaml.org/type/bool.html)
- [YAML 1.2.2 core tag resolution](https://yaml.org/spec/1.2.2/#1032-tag-resolution)
- [Kubeflow Pipelines PR 13757](https://github.com/kubeflow/pipelines/pull/13757)
- [urfave cli-altsrc issue 51](https://github.com/urfave/cli-altsrc/issues/51)
- [MELT training issue 37](https://github.com/MELT-proj/training/issues/37)
- [Cozystack cozyvalues-gen issue 30](https://github.com/cozystack/cozyvalues-gen/issues/30)
