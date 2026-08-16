---
name: multipart-form-data-wire-conformance
description: Use when multipart/form-data uploads succeed in one emitter/parser but fail, truncate, or disagree through another runtime or proxy. Inspect redacted raw bytes offline, reject ambiguous framing and disposition parameters, compare normalized part trees, and make a bounded rollout decision.
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [http, multipart, form-data, uploads, wire-format, conformance]
    related_skills: [rest-graphql-debug]
---

# Multipart/Form-Data Wire Conformance

## When to Use

- The same upload passes with curl but fails with Fetch, a mobile SDK, reverse proxy, or backend parser.
- A file tail, final boundary, field name, or part count changes across hops.
- A parser upgrade changes acceptance of closing-boundary CRLF, extended parameters, or streamed reads.
- You need a redacted, offline emitter-versus-parser compatibility gate before rollout.

Do not use this workflow for ordinary JSON or URL-encoded forms, production fuzzing, WAF bypass, exploit payloads, parser performance testing, or live requests to systems you do not own. For a simple request-shape error with no cross-runtime disagreement, use `rest-graphql-debug` first.

## Prerequisites

- Python 3.9 or newer; the helper uses only the standard library and performs no network access.
- The exact `Content-Type` and body bytes captured at a named, owned boundary.
- Component/runtime versions and a synthetic or safely redacted reproduction.
- Explicit byte, part, header, retry, and time limits for any later runtime replay.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/inspect_multipart.py \
  --content-type 'multipart/form-data; boundary=Boundary42' capture.body

PYTHONDONTWRITEBYTECODE=1 python3 scripts/inspect_multipart.py --case case.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

A case file contains `content_type`, Base64 `body_base64`, and optional positive integer `limits`. Exit `0` means valid or not applicable, `1` means applicable but invalid, and `2` means unreadable or malformed input. Always inspect `applicable`; a non-multipart request is not a conformance pass.

## Procedure

### 1. Freeze the failing boundary

Capture the exact request `Content-Type` and body bytes immediately before and after each suspected hop: emitter, client adapter, proxy, server adapter, parser. Record versions separately. Preserve CRLF, NULs, final bytes, preamble, epilogue, and the closing delimiter. Do not reconstruct the body from a parsed object.

Replace credentials and file data with deterministic sentinels without changing lengths or framing properties relevant to the failure. If safe redaction cannot preserve those properties, create an equivalent synthetic fixture. Never retain cookies, authorization headers, personal filenames, or customer payloads.

**Complete when:** every capture names its hop and version, has a digest, and contains only reviewed synthetic/redacted bytes.

### 2. Inspect framing before invoking an application parser

Run `inspect_multipart.py` on each capture. It checks:

- exactly one valid RFC 2046 boundary parameter and exact byte agreement with delimiter lines;
- opening and closing delimiters, CRLF placement, preamble/epilogue byte counts, and forbidden delimiters after close;
- configured body, part, header-count, and header-byte limits;
- exactly one `Content-Disposition: form-data` with a non-empty `name`;
- duplicate parameters, ambiguous `name*`, forbidden `filename*`, duplicate critical headers, obs-fold, and malformed header names;
- payload byte count and SHA-256 without printing payload bytes.

A closing delimiter may end at EOF or be followed by CRLF and an epilogue. Do not add a trailing CRLF merely to satisfy one parser until the raw-wire inspector proves framing is otherwise valid and compatibility testing justifies a canonical reserialization.

**Complete when:** each hop has a machine-readable report and every invalid report blocks forwarding or rollout.

### 3. Build a bounded benign fixture matrix

Vary one property at a time:

| Axis | Required fixtures |
| --- | --- |
| Closing delimiter | at EOF; followed by CRLF; CRLF plus epilogue |
| Parts | empty field; text; binary ending in `00`/`FF`; multiple repeated names |
| Disposition | quoted name; duplicate name; `name*`; `filename*`; escaped quote |
| Framing | preamble; boundary-like payload bytes; wrong-case boundary; truncation |
| Delivery | complete buffer; legal chunk splits; concurrent requests with unique sentinels |
| Limits | exact accepted boundary; one byte/part/header over limit |

Keep bytes and case count small. The bundled helper validates complete captures; transport chunking and concurrency must be exercised only against disposable local instances of the actual components because those are runtime state properties, not MIME grammar.

**Complete when:** every fixture has an expected validity, normalized part count, byte length, digest, and expected finding code.

### 4. Compare normalized trees across actual parsers

For each selected emitter/parser tuple, run the same fixture bytes and record only:

```json
{"accepted":true,"parts":[{"index":0,"name":"note","filename":null,"body_bytes":5,"sha256":"..."}]}
```

Compare acceptance, ordered part count, names, filenames, content types, byte lengths, and hashes. A successful status code is not enough. Separate three boundaries:

1. **emitter defect:** declared boundary or emitted delimiter/body bytes are inconsistent;
2. **transport/proxy defect:** before/after capture digests or normalized trees differ;
3. **parser-policy difference:** identical bytes produce different acceptance or trees.

Treat a correlated observation as evidence, not automatically as a violation: chunk splits, preambles, epilogues, repeated field names, and a closing delimiter at EOF can be valid. Findings must come from the wire invariant or an explicitly pinned application policy.

**Complete when:** the first divergent hop is named and identical bytes have been compared across every rollout-critical parser.

### 5. Choose a compatibility action

Prefer, in order:

1. fix an emitter that violates its own declared framing;
2. upgrade or configure a parser to accept the valid required profile;
3. reject ambiguous/invalid input at the first trusted boundary;
4. at an owned gateway, parse once with the strict profile and reserialize canonically before forwarding, preserving ordered repeated fields and payload bytes;
5. narrow the supported client/parser matrix if no safe common profile exists.

Never forward the original body after making a security or routing decision from a different parser's tree. If downstream policy depends on parsed names or filenames, either forward the validated canonical representation or bind the decision to the exact bytes and same parser.

### 6. Roll out and recover

Canary one tuple at a time with synthetic uploads. Require zero inspector violations, identical normalized trees, exact binary hashes, bounded memory/time, and no cross-request sentinel mixing. Keep the old tuple available.

On a mismatch: stop expansion, preserve redacted before/after captures, route to the known-good tuple, quarantine only synthetic outputs, and classify emitter/transport/parser before changing framing. If production data may have been truncated or misassociated, reconcile from the authoritative source; do not trust the damaged multipart parse.

## Fail-Closed Conditions

Block on missing/duplicate/invalid boundary parameters; boundary/body disagreement; malformed delimiter suffix; absent opening or closing delimiter; delimiter after close; exceeded limits; malformed/folded/duplicate critical headers; missing or duplicate disposition names; `name*`/`filename*`; different normalized trees for identical bytes; byte/hash mismatch; unbounded parser work; or cross-request state mixing.

Do not treat a parse error caused by unreadable/malformed fixtures as proof that an expected-invalid fixture passed. The fixture must be read successfully and rejected for its intended finding code.

## Objective Verification

1. the normal two-part fixture passes, preserves the six-byte binary tail, and reports its exact SHA-256;
2. the difficult fixture recognizes its closing boundary and eight-byte epilogue but rejects `name*` with `disposition-extended-name`;
3. boundary case mismatch, truncation, malformed suffixes, duplicate parameters, `filename*`, obs-fold, critical-header duplication, and each configured limit fail closed;
4. boundary-like bytes not at a delimiter line remain payload;
5. malformed JSON, unknown case keys, invalid Base64, non-standard JSON numbers, and unreadable input exit `2`;
6. `application/json` reports `applicable: false`, no violations, and does not activate the workflow;
7. tests run offline and print no payload bytes or credentials.

## Evaluation Prompts

1. **Normal:** “Inspect this redacted multipart/form-data capture offline. Prove boundary agreement, preserve the binary tail bytes, and return a normalized part tree.”
2. **Difficult edge:** “A proxy and backend disagree on this capture. Fail closed on ambiguous Content-Disposition parameters while accepting a closing boundary at EOF or before an epilogue; identify the exact violation.”
3. **Should not activate:** “My request is application/json and has no multipart body. Should this multipart wire-conformance workflow activate?” Expected routing: no; use ordinary JSON validation.

## Sources and Scope

Accessed 2026-08-16:

- RFC 2046 §5.1.1, multipart boundary grammar and delimiter rules: https://datatracker.ietf.org/doc/html/rfc2046#section-5.1.1
- RFC 7578 §4.1, multipart/form-data boundary parameter: https://datatracker.ietf.org/doc/html/rfc7578#section-4.1
- RFC 7578 §4.2, Content-Disposition requirements and forbidden `filename*`: https://datatracker.ietf.org/doc/html/rfc7578#section-4.2
- Crow closing-boundary CRLF interoperability report: https://github.com/CrowCpp/Crow/issues/1040
- Bun FormData closing-boundary report: https://github.com/oven-sh/bun/issues/2644
- Go strict-parser disagreement over extended field notation: https://github.com/golang/go/issues/79950

The RFCs define wire grammar; issue reports demonstrate independent interoperability costs but are not normative. The strict duplicate/extended-parameter gate, limits, normalized-tree comparison, rollout order, and recovery procedure are original operational recommendations. No issue prose, reproducer, or third-party implementation code is copied. The helper inspects complete offline captures only; it does not prove asynchronous body-reader safety, memory behavior, or request isolation. Prove those properties with bounded local fixtures against the actual runtime.
