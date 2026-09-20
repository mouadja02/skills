---
name: http-message-signature-profile-conformance
description: Use when preflighting RFC 9421 HTTP Message Signatures, validating Signature-Input structured fields and application profiles, reconstructing canonical signature bases, or managing migration from legacy draft-cavage signatures.
version: 1.0.0
author: Mouad Jaouhari
license: MIT
platforms: [linux, darwin]
metadata:
  hermes:
    tags: [http, security, rfc9421, rfc9530, signatures, api, activitypub, federation]
    related_skills: [http-redirect-credential-boundary-conformance, oauth-dpop-nonce-retry-conformance]
---

# HTTP Message Signature Profile Conformance (RFC 9421)

Preflight, validate, and verify RFC 9421 HTTP Message Signatures across applications and federated networks. Ensures strict RFC 8941 Structured Field syntax compliance, prevents silent activity drops during legacy draft-cavage migrations, enforces application profile requirements (required covered components, algorithms, clock windows), and deterministically reconstructs RFC 9421 Section 2.5 signature bases.

## When to Use

- Incoming HTTP request or response signatures need validation against an application security profile.
- Implementing or debugging ActivityPub federation (Pixelfed, Mastodon, Misskey, Lemmy) where peers transition between `draft-cavage-http-signatures` and `RFC 9421`.
- Preventing asynchronous silent drop bugs caused by returning `200 OK` before verifying signatures in queued workers.
- Constructing or auditing deterministic signature base strings per RFC 9421 §2.5.
- Enforcing RFC 9530 `Content-Digest` or `Repr-Digest` coverage over HTTP message bodies.

## When Not to Use

- Standard TLS / mTLS transport-layer authentication without application-level signature verification.
- Simple HMAC webhook signatures (e.g., GitHub `X-Hub-Signature-256`) that use pre-shared secret hashes over raw request bodies rather than structured HTTP component signatures.
- JWT bearer token authentication where tokens are passed in `Authorization: Bearer <token>` without signing HTTP request components.

## Prerequisites

- Python 3.9+ (standard library only; no external dependencies required for the conformance preflight runner).
- Normalized HTTP message headers and target URI.

## Quick Reference

Run the deterministic signature preflight CLI:

```bash
python3 scripts/preflight_signature.py <input-message-and-profile.json>
```

Sample input JSON payload structure:

```json
{
  "profile": {
    "name": "activitypub-federation",
    "required_components": ["@method", "@path", "@authority", "content-digest"],
    "allowed_algorithms": ["ed25519", "rsa-pss-sha512", "rsa-v1_5-sha256"],
    "require_created": true,
    "max_signature_age_seconds": 300,
    "allow_legacy_draft_cavage": false
  },
  "message": {
    "method": "POST",
    "target_uri": "https://example.com/inbox",
    "headers": {
      "Host": "example.com",
      "Content-Digest": "sha-256=:WZDPaVn/7XgHaAy8pmojAkGWoRx2UFChF41A2svX+TaPm+AbwAgBWnrIiYllu7BNNyealdVLvRwEmTHWXvJwew==:",
      "Signature-Input": "sig1=(\"@method\" \"@path\" \"@authority\" \"content-digest\");created=1618884473;keyid=\"test-key-ed25519\"",
      "Signature": "sig1=:ZT1kooQsEHpZ0I1IjCqtQppOmIqlJPeo7DHR3SoMn0s5JZ1eRGS0A+vyYP9t/LXlh5QMFFQ6cpLt2m0pmj3NDA==:"
    }
  },
  "system_clock": 1618884600
}
```

## Step-by-Step Procedure

### 1. Identify Envelope Version

- If `Signature-Input` header is present: Treat message as **RFC 9421**. Look for matching label in `Signature` header.
- If `Signature-Input` is absent, but `Signature` contains `keyId="..."` or `Authorization: Signature ...` is present: Treat message as **legacy draft-cavage**.
- If neither is present: Return `not_applicable` (not an HTTP Message Signature).

### 2. Guard Against Fail-Open and Silent-Drop Migration Pitfalls

- **Synchronous Verification / Double-Knocking:** Never return `200 OK` at HTTP routing before validating the signature if the application uses asynchronous background queues. Reject invalid or unsupported envelopes with `401 Unauthorized` or `400 Bad Request` so compliant peers can fallback/double-knock.
- **Fail-Closed Envelope Isolation:** Never attempt to parse an RFC 9421 `Signature-Input` dictionary with a legacy cavage regex parser.
- **Enforce Profile Policy on Legacy Signatures:** If the application profile specifies `allow_legacy_draft_cavage: false`, immediately reject legacy envelopes with `legacy_draft_cavage_disallowed_by_profile`.

### 3. Validate Structured Field Syntax (RFC 8941)

- Ensure `Signature-Input` parses as a Dictionary whose values are Inner Lists with parameters.
- Ensure `Signature` parses as a Dictionary whose values are Byte Sequences (enclosed in colons `:`).
- Ensure the selected signature label exists in both dictionaries.

### 4. Enforce Application Profile Constraints

- **Covered Components:** Verify that all `required_components` specified by the profile (e.g. `@method`, `@path`, `@authority`, `content-digest`) are present in the signature's covered components set.
- **Algorithms:** If `alg` parameter is provided, verify it is an element of `allowed_algorithms`.
- **Clock & Expiry:**
  - Verify `created` timestamp is not in the future beyond allowed clock skew.
  - Verify elapsed time `(system_clock - created)` does not exceed `max_signature_age_seconds`.
  - If `expires` timestamp is present, ensure `system_clock <= expires`.

### 5. Deterministically Reconstruct the Signature Base (RFC 9421 §2.5)

1. For each covered component in order:
   - Serialize the component identifier: quoted string followed by parameters (e.g. `"@method"`).
   - Append single colon and single space (`: `).
   - Derive the canonical component value:
     - `@method`: Uppercase HTTP method.
     - `@path`: Path component of target URI (defaults to `/`).
     - `@authority`: Lowercase host with explicit non-default port if present.
     - HTTP field name: Lowercase header name, trimmed value without line folds.
   - Append newline (`\n`).
2. Append the `@signature-params` line:
   `"@signature-params": (<ordered-components>);<params>`
3. Return the exact byte string for cryptographic verification.

## Pitfalls & Recovery

- **Missing Content-Digest on Mutating Requests:** RFC 9421 signs message metadata, not content bytes directly. Mutating requests (`POST`, `PUT`, `PATCH`) must cover `content-digest` (RFC 9530) to bind the body payload.
- **Case Sensitivity in Field Names:** RFC 9421 component identifiers for HTTP fields MUST be lowercase.
- **Duplicate Component Identifiers:** RFC 9421 explicitly forbids duplicate component identifiers in covered components; the preflight parser immediately fails closed on duplicate entries.
- **Clock Drift:** Federated nodes frequently experience minor clock skew. Always configure `allowed_clock_skew_seconds` (e.g., 30–60s) in the profile to avoid rejecting legitimate messages.

## Verification

Run test suites and validation scripts offline:

```bash
python3 -m unittest discover -s tests
```
