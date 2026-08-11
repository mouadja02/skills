---
name: s3-streaming-checksum-portability-conformance
description: Use when S3-compatible PutObject or UploadPart fails after an SDK change—classify aws-chunked/checksum-trailer wire modes, run disposable canaries, and verify integrity before rollout.
version: "1.0.0"
license: MIT
---

# S3 Streaming Checksum Portability Conformance

## When to Use

- `PutObject` or `UploadPart` starts returning `InvalidArgument`, checksum mismatch, or retry exhaustion after an SDK/application upgrade.
- AWS works but an S3-compatible backend rejects `aws-chunked`, `x-amz-trailer`, or a streaming `x-amz-content-sha256` token.
- You need a redacted, repeatable capability matrix before changing checksum or payload-signing settings.
- A canary must prove returned checksums and downloaded bytes before rollout.

Do **not** use this for ordinary `GetObject` checksum verification, IAM failures, bucket-policy debugging, production load testing, or global integrity-check bypasses. The helper is offline and data-only; it sends no request and reads no credentials.

## Prerequisites

- Python 3.9+ for the standard-library analyzer.
- A redacted header inventory captured at the final HTTP emitter; omit authorization, cookies, query strings, object names, signatures, and bodies.
- A disposable bucket/prefix approved for harmless canaries, with cleanup and rollback ownership.
- Exact application, SDK, transport, proxy, and backend versions.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_request.py tests/fixtures/signed-trailer.json.txt
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_request.py request.json --output report.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Exit `0` means applicable evidence has no blocking violation, `1` means an applicable inventory is blocked, and `2` means invalid input/output or a non-upload operation.

## Input and Stable Codes

The input is one JSON object with exactly these keys:

```json
{
  "operation": "PutObject",
  "content_encoding": "aws-chunked",
  "x_amz_content_sha256": "STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER",
  "x_amz_trailer": "x-amz-checksum-crc32",
  "content_length_known": true,
  "returned_checksum_matches": true,
  "download_sha256_matches": true
}
```

`returned_checksum_matches` and `download_sha256_matches` may be `null` before a canary. The analyzer emits `mode`, `observations`, `violations`, and `next_action` plus `status` and `applicable`. Key codes include `aws-chunked`, `checksum-trailer`, `multipart-operation`, `contradictory-streaming-evidence`, `returned-checksum-unverified`, and `download-integrity-unverified`.

## Procedure

### 1. Freeze the failing boundary

Record operation, body shape (known-length versus stream), SDK/transport/backend versions, retry count, and the first status/error. Determine whether a proxy buffers or rewrites framing. Stop retries if failed writes can be dropped or duplicated; preserve a rollback version.

**Complete when:** one request path and one upgrade boundary are named without credentials or object data.

### 2. Capture the final emitted inventory

At the transport boundary, record only `Content-Encoding`, `x-amz-content-sha256`, `x-amz-trailer`, whether length was known, operation, and integrity outcomes. Do not infer wire mode from an SDK option name. `aws-chunked` plus a trailer token is evidence; the exact `x-amz-content-sha256` sentinel determines the declared streaming mode.

**Complete when:** the analyzer accepts the redacted JSON and unknown/contradictory combinations fail closed.

### 3. Classify before changing settings

Run `analyze_request.py`. Supported declared modes are:

| Mode | Required evidence |
| --- | --- |
| `signed-payload-trailer` | `aws-chunked` plus `STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER` and `x-amz-trailer` |
| `unsigned-payload-trailer` | `aws-chunked` plus `STREAMING-UNSIGNED-PAYLOAD-TRAILER` and `x-amz-trailer` |
| `signed-streaming-payload` | `aws-chunked` plus `STREAMING-AWS4-HMAC-SHA256-PAYLOAD`, without a trailer |
| `unsigned-payload` | no `aws-chunked`/trailer plus `UNSIGNED-PAYLOAD` |
| `fixed-payload-hash` | no streaming framing and a lowercase 64-hex SHA-256 value |
| `ambiguous` | unknown or contradictory evidence; rollout is blocked |

Do not equate `STREAMING-AWS4-HMAC-SHA256-PAYLOAD` with the `...-TRAILER` variant. A proxy may alter transfer framing, so capture on both sides when hops disagree.

### 4. Run a disposable capability matrix

Use a fresh canary key and harmless deterministic bytes. Test both known-length and streaming bodies for `PutObject`; test `UploadPart` separately if the application uses multipart upload. Vary only one reviewed SDK setting at a time across the modes the client can actually emit. Bound object size, requests, retries, and time.

For every case, retain: emitted mode, backend status/error, returned checksum, downloaded byte count, and independent SHA-256. Abort incomplete multipart uploads and delete canaries. Never use production keys or customer objects.

### 5. Choose the narrowest compatible setting

Prefer a mode that preserves both transport/request integrity and end-to-end byte verification. If a backend cannot accept trailer mode, scope a documented SDK option to that endpoint/client and preserve an explicit checksum or payload hash where supported. Do **not** disable checksum validation globally, change all S3 clients, or treat a 2xx response as integrity proof.

### 6. Canary, roll out, and prove recovery

A release passes only when `PutObject` and applicable `UploadPart` canaries succeed, returned checksum semantics are understood, downloaded bytes match independently, retries remain bounded, and the old version/config remains deployable. Roll out gradually while watching write failures and dropped-data indicators.

## Failure Recovery and Pitfalls

- **Contradictory/unknown headers:** block rollout and capture the redacted final wire inventory; never guess from SDK configuration.
- **2xx but digest mismatch:** quarantine/delete the canary, stop rollout, and inspect proxy/body transformation before retrying.
- **Retry exhaustion or possible data loss:** restore the known-good application/SDK configuration and reconcile missing objects from authoritative application state.
- **Multipart failure:** abort the disposable multipart upload; test `UploadPart` independently from `PutObject`.
- **Credentials captured:** delete the artifact, rotate exposed credentials, and recapture only allowlisted fields.
- **Global integrity disable proposed:** reject it; use endpoint-scoped compatibility settings plus independent verification.
- **Output write failure:** the helper exits `2` and preserves an existing report via atomic replacement.

## Objective Verification

Completion requires:

1. normal signed-trailer input reports `signed-payload-trailer`, `aws-chunked`, and `checksum-trailer`;
2. contradictory `UNSIGNED-PAYLOAD` plus chunked trailer evidence reports `ambiguous` and `contradictory-streaming-evidence`;
3. `GetObject` reports `applicable=false` and exits `2`;
4. malformed shape, unknown keys, duplicate keys, `NaN`/`Infinity`, invalid booleans, unsafe output paths, and write failures fail closed;
5. disposable canary downloads match byte-for-byte and by independent SHA-256;
6. no test or helper performs network access.

## Evaluation Prompts

1. **Normal:** “Classify this redacted `PutObject` signed-trailer inventory and state the disposable-canary integrity gate.”
2. **Difficult edge:** “An `UploadPart` says `UNSIGNED-PAYLOAD` but also emits `aws-chunked` and a checksum trailer; decide whether rollout may continue.”
3. **Should not activate:** “A normal `GetObject` checksum and downloaded SHA-256 both match.”

## Sources and Fact/Recommendation Boundary

Sourced facts: AWS documents SigV4 streaming payload/trailer forms and upload checksum behavior. Loki, Nexus Repository, Apache Polaris, and Fleet report failed or data-losing writes after SDK/application changes selected modes rejected by NetApp ONTAP, Alibaba OSS, or Ceph/RadosGW.

Recommendations—the allowlisted redacted inventory, stable taxonomy, disposable matrix, independent download digest, endpoint-scoped mitigation, and rollback order—are original operational guidance.

- AWS SigV4 streaming signatures (accessed 2026-08-11): https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html
- AWS upload integrity checks (accessed 2026-08-11): https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity-upload.html
- Grafana Loki issue 21926: https://github.com/grafana/loki/issues/21926
- Sonatype Nexus Repository issue 1012: https://github.com/sonatype/nexus-public/issues/1012
- Apache Polaris issue 3346: https://github.com/apache/polaris/issues/3346
- Fleet issue 47850: https://github.com/fleetdm/fleet/issues/47850

No source prose or code was copied. This original helper and its fixtures are MIT-licensed.
