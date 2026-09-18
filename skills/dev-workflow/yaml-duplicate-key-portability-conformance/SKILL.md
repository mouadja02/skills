---
name: yaml-duplicate-key-portability-conformance
description: Use when YAML configuration may silently discard repeated mapping keys across PyYAML, Helm, Ansible, CI, or deployment tools—detect duplicates before construction, distinguish merge keys, and fail closed with source coordinates.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# YAML Duplicate-Key Portability Conformance

Inspect the representation graph before a constructor turns a mapping into a dictionary. Keep explicit duplicate keys, merge-key policy, parser behavior, and application merge semantics separate.

## When to Use

- A YAML parser, linter, Helm chart, or Ansible task silently keeps the last repeated key.
- The same YAML bytes warn in one runtime and fail in another.
- Quoted/plain or schema-resolved keys may compare equal after resolution.
- A CI gate must reject duplicates before deployment.

Do **not** activate for JSON/TOML, general formatting, intentional merges between separate configuration files, or YAML 1.1-versus-1.2 boolean-value migration. Use `yaml-boolean-coercion-conformance` for the latter.

## Prerequisites

- Python 3.9+ and PyYAML (`python3 -m pip install PyYAML` in an isolated environment).
- The exact YAML bytes and the parser/version/schema options used by each producer and consumer.
- Synthetic or redacted input. The helper is offline, reads data only, and composes nodes without constructing application objects.

## Quick Reference

```bash
python3 scripts/check_yaml_duplicate_keys.py values.yaml
python3 scripts/check_yaml_duplicate_keys.py values.yaml --merge-policy allow --output report.json
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_check_yaml_duplicate_keys.py
```

Exit codes: `0` clean, `1` duplicate or forbidden merge key found, `2` unreadable/oversized/malformed/unsupported input, `3` report write failure.

## Procedure

### 1. Freeze the consumer contract

Record the input digest, producer, every parser and version, resolver/schema, duplicate policy, merge-key support, and downstream precedence rules. A warning or successful load is not proof of valid input: construction may already have erased earlier entries.

### 2. Scan before construction

Run the helper on the original `.yaml` or `.yml` bytes. It walks every mapping in every document, including nested and flow mappings, and reports both the first and repeated key coordinates.

```bash
python3 scripts/check_yaml_duplicate_keys.py config.yaml --merge-policy forbid
```

The default `forbid` policy reports YAML merge keys (`<<`) separately because merge keys are an optional extension, not ordinary repeated keys. Select `--merge-policy allow` only when every declared consumer supports the same merge behavior. An explicit key overriding a key supplied through an allowed merge is not reported as an explicit duplicate.

The helper uses PyYAML SafeLoader resolution for scalar-key identity. Record that profile: plain `true` and `TRUE` resolve to the same boolean key, while quoted `"true"` remains a string. Unsupported explicit tags fail closed rather than invoking constructors.

### 3. Compare deployed consumers

Parse the same immutable fixtures with each real consumer. Capture success/failure, severity, retained key/value, schema, and merge behavior. Include:

1. block, flow, and nested duplicate mappings;
2. quoted versus plain string controls;
3. keys that resolve equal under the selected schema;
4. anchors and merge keys under the declared policy;
5. multi-document streams;
6. malformed YAML and unsupported tags.

Never infer behavior from a library family name. Pin the exact runtime and options.

### 4. Repair at the producer boundary

Remove an accidental duplicate and express the intended precedence explicitly. If layered override behavior is required, use the application's documented multi-file merge mechanism or an approved merge-key profile instead of repeated mapping entries. Re-run the scanner and every consumer fixture against the repaired bytes. Rollback restores the original bytes and previous parser tuple; do not rewrite production files automatically.

## Objective Verification

Completion requires:

- the helper reports every expected duplicate with document, path, key, and both coordinates;
- nested, flow, multi-document, and schema-resolved duplicate fixtures are rejected for the intended reason;
- allowed merge overrides are not mislabeled as explicit duplicates, while `forbid` reports merge use;
- quoted distinct controls and ordinary unique mappings pass;
- malformed YAML, unsupported tags, unreadable input, oversized input, and report-write failure fail closed;
- repaired fixtures pass the helper and all pinned consumers without silent key loss.

## Pitfalls and Safety

- Scan original bytes before `safe_load`, JSON conversion, templating, or re-serialization.
- Do not conflate repeated explicit keys with merge-source overrides.
- Resolver choice changes key identity; PyYAML SafeLoader follows YAML 1.1-style scalar resolution in several cases.
- A clean duplicate scan does not prove the YAML is semantically valid for the application.
- Never load researched or production YAML with unsafe constructors. Do not execute tags or templates.

## Evaluation Prompts

1. **Normal:** Check block and flow mappings containing repeated `port` and `tier` keys; return an ordered JSON report with both source locations.
2. **Difficult:** Under an allowed merge-key profile, verify that an explicit override of a merged default is not an explicit duplicate, but `true` and `TRUE` keys in a second document are a resolved-key collision.
3. **Should not activate:** Inspect a JSON object with unique members; explain that this YAML-specific workflow should not run.

## Sources and Fact/Policy Boundary

**Sourced facts:** YAML 1.2.2 requires mapping keys to be unique. Helm, Ansible, and PyYAML records demonstrate silent last-key retention or inconsistent duplicate handling. Yamllint provides a configurable duplicate-key rule.

**Recommendations:** pre-construction scanning, explicit merge policy, input cap, unsupported-tag rejection, fixture matrix, and producer-boundary repair are original conservative operating policy.

- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [Helm issue 31102](https://github.com/helm/helm/issues/31102)
- [Helm issue 12381](https://github.com/helm/helm/issues/12381)
- [Ansible issue 84576](https://github.com/ansible/ansible/issues/84576)
- [PyYAML issue 165](https://github.com/yaml/pyyaml/issues/165)
- [Ansible duplicate dictionary key setting](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#duplicate-yaml-dict-key)
- [Yamllint key-duplicates rule](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.key_duplicates)
