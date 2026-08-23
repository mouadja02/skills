---
name: json-duplicate-member-boundary-conformance
description: Use when JSON authorization, signing, canonicalization, APIs, or distributed runtimes may disagree on repeated object names—inspect original bytes before lossy parsing and fail closed with scoped duplicate paths and offsets.
version: "1.0.0"
license: MIT
---

# JSON Duplicate-Member Boundary Conformance

## When to Use

- Two JSON consumers can apply first-wins, last-wins, preserve-all, or reject policies.
- JSON crosses an authorization, policy, coordinator/worker, signing, hashing, or canonicalization boundary.
- A parser already collapsed input into a map and uniqueness can no longer be proven.
- A migration needs deterministic positive and negative fixtures.

Do **not** activate for repeated array values, the same name in separate object scopes, ordinary schema validation, or non-JSON formats. This skill detects ambiguity; it is not a general JSON parser, canonicalizer, signature verifier, or vulnerability scanner.

## Prerequisites

- Python 3.10+ for the bundled offline analyzer.
- Original JSON bytes or text before any object-to-map conversion.
- Synthetic or redacted fixtures; never place credentials, tokens, signatures, or production payloads in reports.
- An explicit project policy for byte/depth/member limits.

## Quick Reference

```bash
python3 scripts/analyze_json_duplicates.py fixture.json > report.json
# exit 0 + control=ready: valid JSON and uniqueness proved
# exit 2 + control=blocked: duplicate, malformed, non-finite, or limit failure
# exit 3: input/output failure; treat as blocked
```

The analyzer emits decoded JSON Pointer paths, character and UTF-8 byte offsets, and first/last/preserve-all **observations** without exposing member values. Its violation predicate is only a repeated decoded name in the same object. Malformed or unprovable input is blocked separately.

## Procedure

### 1. Freeze the trust boundary

Capture the original bytes at the earliest owned boundary. Do not inspect a host-language dictionary: a normal parser may already have discarded occurrences. Record which components authorize, log, canonicalize, sign, verify, transform, or execute the value.

**Completion:** every security-relevant consumer and every parse transition is named, and the pre-collapse bytes are available.

### 2. Define policy and limits

Adopt fail-closed uniqueness for security-sensitive objects. JSON names compare as decoded strings: `"a"` and `"\u0061"` collide. Names are case-sensitive and are not Unicode-normalized unless another protocol explicitly says otherwise. Repeated array values and names in distinct object scopes are valid.

Set bounded `max_bytes`, `max_depth`, and `max_members`. A timeout, I/O error, malformed UTF-8/JSON, BOM, unpaired surrogate, `NaN`, `Infinity`, or non-finite number is **blocked**, not an expected-invalid duplicate pass.

### 3. Run the raw-input gate

```bash
python3 scripts/analyze_json_duplicates.py \
  --max-bytes 1048576 --max-depth 128 --max-members 100000 \
  request.json > duplicate-report.json
status=$?
python3 -c 'import json; r=json.load(open("duplicate-report.json")); print(r["control"], r["violation"], r["duplicate_count"])'
```

Do not use shell truthiness on serialized arrays. Parse `duplicate_count` numerically. Treat exit 2 or 3 as blocked. The report intentionally omits values; preserve raw fixtures only in access-controlled, short-lived storage.

**Completion:** `control=ready`, `valid_json=true`, and `duplicate_count=0`, or processing stops with a retained reason.

### 4. Compare consumer projections without blessing them

For every duplicate fixture, record each runtime's observed policy: reject, first-wins, last-wins, or preserve-all. These are evidence indicators, not acceptable alternatives. The safety invariant remains: no repeated decoded name may cross the trust boundary.

Use this matrix:

| Stage | Input representation | Duplicate behavior | Security action |
|---|---|---|---|
| Edge | raw bytes | reject/first/last/all | reject before authorization |
| Policy | parsed value | observed behavior | consume only gated data |
| Logger | parsed value | observed behavior | never substitute for gate |
| Canonicalizer/signer | bytes/value | must reject | stop before hashing/signing |

### 5. Test both failure and recovery

Use synthetic fixtures for:

- direct, nested, and array-contained duplicates;
- escaped-equivalent names and JSON Pointer escaping (`~`, `/`);
- three or more occurrences;
- repeated names in separate objects as a safe positive control;
- repeated array values as a should-not-activate control;
- malformed UTF-8/JSON, BOM, surrogate, `NaN`/`Infinity`, trailing data, and exact resource limits;
- output and input I/O failure.

Prove the failure boundary: ambiguous input is blocked before authorization, canonicalization, hashing, signing, verification, or execution. Prove recovery by removing the repeated member at the producer, rerunning the same fixture, and obtaining `ready`; never “repair” ambiguity by selecting first or last.

### 6. Gate rollout

Run the analyzer at every boundary where bytes can be reparsed independently. Compare reports and consumer observations in staging. Deploy only when all paths reject duplicates and valid safe controls remain accepted. Monitor counts, not payload contents.

## Failure Recovery

- **Only a collapsed map remains:** uniqueness is unprovable; reacquire original bytes or block.
- **Parser outcomes disagree:** keep the boundary blocked; align on pre-parse rejection rather than choosing a winner.
- **Limit exceeded:** raise limits only from measured synthetic sizes and rerun; never silently bypass.
- **Interrupted rollout:** preserve the old path, stop new signing/canonicalization, and replay only synthetic fixtures after rollback.
- **Analyzer I/O failure:** exit 3 is blocked. Fix storage/pipe permissions and rerun from original bytes.

## Verification

From the installed skill directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
printf '%s' '{"a":1,"\u0061":2}' | python3 scripts/analyze_json_duplicates.py -
printf '%s' '[{"a":1},{"a":2},1,1]' | python3 scripts/analyze_json_duplicates.py -
```

The tests must pass. The first probe must exit 2 with one duplicate at `/a`; the safe control must exit 0 with `ready`.

## Evaluation Prompts

1. **Normal:** An API gateway and service parse `{"role":"user","role":"admin"}` differently. Produce a pre-deployment procedure.
2. **Difficult edge:** Design a fail-closed check for nested objects, arrays, escaped-equivalent names, malformed JSON, and signing/canonicalization.
3. **Should not activate:** Decide whether repeated array values and the same name in separate objects should trigger the gate.

## Sources and Recommendations

**Sourced facts:** RFC 8259 says object names should be unique and describes implementation differences for duplicates. RFC 8785 requires duplicate-free objects as a canonicalization prerequisite. Public GJSON, yyjson, and Velox reports demonstrate first/all, requested reject, and preserve/last divergence across independent projects.

**Recommendations:** pre-parse rejection, the bundled limits, value-redacted reports, staging matrices, and rollout controls are conservative operational guidance synthesized for this skill.

- RFC 8259, JSON Data Interchange Format: https://www.rfc-editor.org/rfc/rfc8259.html
- RFC 8785, JSON Canonicalization Scheme: https://www.rfc-editor.org/rfc/rfc8785.html
- GJSON issue 393: https://github.com/tidwall/gjson/issues/393
- yyjson issue 254: https://github.com/ibireme/yyjson/issues/254
- Velox issue 18066: https://github.com/facebookincubator/velox/issues/18066

No source code or prose was copied. The helper, tests, fixtures, and workflow are original and use only the Python standard library.
