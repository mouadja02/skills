# RFC 9421 HTTP Message Signature Evaluations

This document defines three evaluation scenarios covering standard RFC 9421 verification, legacy draft-cavage migration edge cases, and non-applicable HMAC webhooks.

## Scenarios

### 1. Normal: RFC 9421 Verification & Base Reconstruction

- **Description:** Verify incoming RFC 9421 signed request against ActivityPub federation profile requiring `@method`, `@path`, `@authority`, and `content-digest`.
- **Expected Result:** Preflight passes; envelope identified as `rfc9421`; signature base accurately reconstructed per RFC 9421 §2.5.

### 2. Edge Case: Legacy Draft-Cavage Migration Gate

- **Description:** Incoming peer sends legacy `draft-cavage` signature in `Signature` header while application profile enforces modern RFC 9421 (`allow_legacy_draft_cavage: false`).
- **Expected Result:** Fails closed; envelope identified as `draft-cavage`; rejected with `legacy_draft_cavage_disallowed_by_profile`.

### 3. Should-Not-Activate: Standard HMAC Webhook

- **Description:** Incoming HTTP POST request with `Authorization: Bearer ...` and `X-Hub-Signature-256: ...`.
- **Expected Result:** Evaluated as `not_applicable`; bypasses signature preflight cleanly without false positive rejection.
