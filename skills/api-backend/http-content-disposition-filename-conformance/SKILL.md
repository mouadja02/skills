---
name: http-content-disposition-filename-conformance
description: Use when an HTTP download gets the wrong, garbled, unsafe, or client-dependent filename—especially Content-Disposition filename/filename*, RFC 8187 percent encoding, duplicate parameters, redirects, path traversal, device names, or media-type extension mismatches.
version: "1.0.0"
license: MIT
---

# HTTP Content-Disposition Filename Conformance

## When to Use

- A browser, curl, framework, or download worker chooses a different filename from another client.
- `filename` and `filename*` disagree, are duplicated, or contain malformed encoding.
- A server-supplied download name must be treated safely before a file is created.
- Redirect fallback, Unicode, path, reserved-name, or extension policy needs a reproducible audit.

Do **not** activate for HTML `<title>` selection, multipart upload-part names, local file renaming with no HTTP response, or generic MIME attachment handling outside HTTP.

## Prerequisites

- A redacted raw `Content-Disposition` field value and optional `Content-Type`.
- Python 3.9+ for the offline analyzer.
- A project-owned media-type-to-extension policy when extension consistency matters.

Never put response bodies, credentials, production URLs, or existing destination paths in a fixture. The analyzer performs no network or filesystem writes beyond reading its input and emitting JSON.

## Quick Reference

```bash
python3 scripts/analyze_content_disposition.py case.json > report.json
# 0 = accepted filename, 1 = rejected filename, 2 = invalid input, 3 = output failure
```

```json
{
  "content_disposition": "attachment; filename=\"resume.csv\"; filename*=UTF-8''r%C3%A9sum%C3%A9.csv",
  "content_type": "text/csv",
  "media_type_extensions": {"text/csv": [".csv"]}
}
```

Completion requires `decision: "accept"`, an empty `finding_codes` array, and a reviewed `safe_basename`. This authorizes only the name decision—not a download or write.

## Procedure

### 1. Preserve the decision inputs

Capture the final response's field value exactly, after the HTTP implementation has combined field lines according to its documented behavior. Also record which redirect supplied the final representation, but do not feed URLs to the analyzer or assume a final URL basename is authorized.

Keep these layers separate:

1. **presentation:** raw header syntax and quoted-string escaping;
2. **extended value:** `charset'language'percent-encoded-value`;
3. **selection:** valid `filename*` takes precedence over `filename`;
4. **consumer policy:** basename, controls, device names, and extension checks;
5. **write boundary:** fresh-directory creation and atomic publication.

### 2. Parse before choosing

Reject the field when disposition syntax, quoting, parameter shape, or an extended value is malformed. Parameter names are case-insensitive. Duplicate parameter names make the field invalid; never select the first or last duplicate merely because one library does.

For `filename*`, parse the three RFC 8187 parts before percent-decoding. Reject malformed percent triplets, invalid bytes for the declared charset, unsupported charsets, and invalid language syntax. Do not MIME-word-decode `filename`; RFC 6266's HTTP profile does not define encoded-word recovery as a filename selection rule.

A valid `filename*` is selected ahead of `filename`. A malformed `filename*` is not silently repaired or downgraded to a potentially attacker-chosen fallback. Ask the producer for one unambiguous header.

### 3. Treat the received name as advisory

Before any write, require a single basename. Reject:

- `/`, `\\`, dot segments, leading/trailing whitespace, and trailing dots;
- C0/DEL or Unicode format controls, including bidirectional overrides;
- platform special names such as `CON`, `NUL`, `COM1`, and `LPT1`;
- normalization changes that the consuming platform has not explicitly reviewed;
- an extension outside the supplied media-type policy.

The analyzer reports NFC differences rather than changing them silently. Extension policy is a **project recommendation**, not an RFC media-type mandate: supply it explicitly, verify payload type independently, and never infer executable safety from a filename alone.

### 4. Compare clients with synthetic fixtures

Run the same redacted matrix through the analyzer and each target client/framework:

| Boundary | Fixtures |
| --- | --- |
| Selection | only `filename`; only `filename*`; both; duplicate each |
| Encoding | UTF-8; ISO-8859-1; malformed `%`; invalid UTF-8; language tag |
| Syntax | token; quoted escape; empty value; unterminated quote; folded input |
| Safety | separators; `.`/`..`; bidi/control; device name; trailing dot/space |
| Policy | matching and mismatching verified media type/extension |
| Navigation | header on initial response, final response, neither, and conflicting redirects |

Record observed client behavior separately from conformance. A client saving a file is not evidence that the field was valid or the name safe.

### 5. Enforce the write boundary

After acceptance, create output only inside a fresh quota-limited temporary directory. Join the reviewed basename to that directory, resolve the parent, and prove it remains the intended directory. Open with exclusive creation, stream under byte/time limits, verify the expected payload digest or authenticated metadata, flush, and atomically publish only with explicit caller authorization.

On collision, write failure, changed metadata, or digest mismatch, preserve neither a partial destination nor an automatically incremented attacker-controlled name. Return to the caller for a new policy decision.

## Failure Recovery

- **Duplicate or malformed parameter:** fix the producer; do not pick a convenient value.
- **Client disagreement:** retain the raw field, client/version, selected parameter, and resulting basename; compare these transitions rather than only final filenames.
- **Unsafe but decodable name:** reject it. If business rules permit a replacement, generate a local name independent of the supplied path and retain the original only in escaped audit metadata.
- **Redirect with no valid filename:** apply an explicitly documented local fallback policy; do not trust the final URL path by default.
- **Output failure:** treat exit `3` as no report. Do not mistake buffered write failure for a completed audit.

## Pitfalls and Safety

- RFC 6266 defines received filenames as advisory; precedence does not make a filename safe.
- `filename*` uses RFC 8187 encoding, not form/query `+`-for-space rules.
- MIME multipart `Content-Disposition` has a different profile; use the multipart wire-conformance skill for uploads.
- Unicode normalization, reserved names, and extension allowlists are consumer/platform policy. Keep them distinguishable from standards violations.
- Never fetch a researched or fixture-supplied URL, extract an archive, or overwrite an existing file as part of this audit.

## Objective Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_analyze_content_disposition.py
```

The tests prove `filename*` precedence, UTF-8 and ISO-8859-1 decoding, duplicate and malformed-percent separation, invalid UTF-8 rejection, path/bidi/device/extension policy findings, malformed schema/JSON/non-finite rejection, unreadable input handling, and controlled stdout failure.

## Evaluation Prompts

1. **Normal:** Audit `attachment; filename="resume.csv"; filename*=UTF-8''r%C3%A9sum%C3%A9.csv` under a `.csv` policy without writing a file.
2. **Difficult edge:** Reject duplicate `filename` values plus a malformed `filename*` containing encoded traversal, bidi, and extension-confusion evidence; identify independently provable findings without silently repairing.
3. **Should not activate:** Choose an HTML document title when there is no HTTP response header or downloaded file.

## Sources

**Sourced facts:** syntax, duplicate invalidity, extended-value precedence, decoding, and advisory-filename requirements come from the standards. Issue records establish independent implementation and fallback failures; they are not normative.

- [RFC 6266: Content-Disposition in HTTP](https://www.rfc-editor.org/rfc/rfc6266.html)
- [RFC 8187: HTTP Header Field Parameters](https://www.rfc-editor.org/rfc/rfc8187.html)
- [Spring Framework #31940](https://github.com/spring-projects/spring-framework/issues/31940)
- [Spring Framework #36805](https://github.com/spring-projects/spring-framework/issues/36805)
- [curl #10533](https://github.com/curl/curl/issues/10533)
- [curl #20318](https://github.com/curl/curl/issues/20318)

**Recommendations:** strict fail-closed fallback, NFC review, explicit extension policy, synthetic differential fixtures, quota-limited exclusive creation, and atomic publication are this skill's operational safety guidance.
