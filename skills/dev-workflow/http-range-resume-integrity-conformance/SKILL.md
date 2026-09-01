---
name: http-range-resume-integrity-conformance
description: Use when interrupted HTTP downloads resume with Range/If-Range, partial caches may be stale, or 200/206/416 and Content-Range handling could append incompatible bytes.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# HTTP Range Resume Integrity Conformance

## When to Use

- A large download must resume from a partial file without mixing representations.
- A client receives surprising `200`, `206`, `416`, `Content-Range`, ETag, or encoding combinations.
- Cached partial artifacts need a deterministic append/restart/quarantine decision.
- Cross-client tests must prove corruption recovery before rollout.

Do **not** activate for a small ordinary download with no partial state or resume requirement. This workflow does not test server performance, bypass access control, or replace final digest verification.

## Prerequisites

- Python 3.9+ for the offline auditor.
- A redacted checkpoint: local byte count, strong ETag when available, and independently obtained final SHA-256.
- A captured request offset and response status/headers/body byte count. Never include credentials or signed URLs.

## Quick Reference

```bash
python3 scripts/audit_resume.py transcript.json --pretty
# 0 = safe transition, 1 = parsed findings, 2 = invalid input, 74 = output failure
python3 tests/test_audit_resume.py
```

The helper is offline and read-only. It never opens a URL or writes a downloaded file.

## Procedure

### 1. Freeze representation identity

Before requesting bytes, persist the partial length and a **strong** ETag. Prefer an independent final digest. A weak ETag, file name, URL, `Last-Modified` alone, or equal length does not prove byte identity. Send `If-Range` with the strong validator when the client supports it; still validate the response.

### 2. Capture a redacted transcript

```json
{
  "checkpoint": {
    "local_size": 100,
    "etag": "\"v1\"",
    "expected_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "request": {"range_start": 100},
  "response": {
    "status": 206,
    "body_length": 100,
    "headers": {
      "Content-Range": "bytes 100-199/1000",
      "Content-Length": "100",
      "ETag": "\"v1\"",
      "Content-Encoding": "identity"
    }
  }
}
```

Record decoded-body byte count only when offsets refer to that same representation. Resume conservatively with identity content encoding.

### 3. Audit before any write

Run the helper and require `classification: "append"` before appending. It checks:

- request, local, and returned start offsets are equal;
- `206` has a valid, bounded byte `Content-Range`;
- range span, body length, and `Content-Length` agree;
- the strong response ETag matches the checkpoint;
- content encoding does not change byte coordinates.

A plain ranged `200` means restart from byte zero into a new temporary file. A `200` that also claims a partial `Content-Range` is contradictory and rejected. Never append either response.

### 4. Handle 416 without guessing

For `416`, require `Content-Range: bytes */N`. If `N` equals local size and a trusted final digest exists, `verify_local_complete` means hash the existing file; it does **not** declare success. A mismatched length is stale partial state. Without a digest, equal length remains unproven.

### 5. Recover safely

1. Preserve or quarantine the partial and checkpoint for diagnosis.
2. Restart into a fresh temporary path; never overwrite the partial in place.
3. Disable resume when identity or byte coordinates are ambiguous.
4. Enforce size limits, redirect policy, authentication scope, and TLS in the actual downloader.
5. Verify exact final size and independent digest, then atomically publish.

Do not append after a changed/missing/weak validator, malformed range, transformed content, short body, or contradictory status. Do not “repair” a file by truncating it to fit an untrusted response.

## Verification

Completion requires:

- the synthetic unsafe fixtures are rejected for their intended finding codes;
- a valid `206` fixture is append-eligible at exactly the persisted offset;
- plain ranged `200` selects restart, never append;
- `416` size equality triggers local hashing, not automatic success;
- the real downloader verifies final digest before atomic publication.

The helper proves transcript consistency only. It does not prove received bytes match the expected digest.

## Pitfalls and Safety

- `Accept-Ranges` advertises capability; it does not authorize append.
- Same URL does not imply same representation across redirects, authorization, or content negotiation.
- `Content-Length` is not the complete object size in a valid partial response.
- Never log cookies, bearer tokens, signed query strings, or production response bodies.
- Parse/I/O errors are invalid evidence, not expected-invalid test passes.

## Evaluation Prompts

1. **Normal:** Classify a matching strong-ETag `206` whose range starts at the persisted partial length and state every pre-write check.
2. **Difficult edge:** Compare a ranged `200` with partial `Content-Range`, a changed-ETag `206`, and a `416` whose complete length equals local size.
3. **Should not activate:** Download a small immutable icon with no partial file and a published digest; use an ordinary atomic download instead.

## Sourced Facts vs Recommendations

RFC 9110 defines range response semantics and validators. Public issue records demonstrate costly client failures. The transcript schema, conservative strong-validator rule, stable finding codes, quarantine sequence, and requirement for an independent digest are this skill's recommendations.

## Sources

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [Hugging Face Hub issue 4060](https://github.com/huggingface/huggingface_hub/issues/4060)
- [Hugging Face Hub issue 4196](https://github.com/huggingface/huggingface_hub/issues/4196)
- [Hugging Face Hub issue 3007](https://github.com/huggingface/huggingface_hub/issues/3007)
- [rclone issue 6980](https://github.com/rclone/rclone/issues/6980)
- [uv issue 16934](https://github.com/astral-sh/uv/issues/16934)
- [GitHub CLI issue 13919](https://github.com/cli/cli/issues/13919)
- [ModelScope Hub issue 50](https://github.com/modelscope/modelscope_hub/issues/50)

See [references/evidence.md](references/evidence.md) for evidence and licensing scope.
