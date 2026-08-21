# Normalized transcript format

The helper accepts one UTF-8 JSON object. It rejects duplicate members, non-standard numeric constants, unknown members, and credential-bearing keys before protocol analysis.

```json
{
  "profile": "oauth-dpop-nonce-v1",
  "events": [
    {
      "role": "authorization_server",
      "origin": "https://as.example",
      "endpoint": "/token",
      "request_id": 1,
      "operation_id": "token-1",
      "retry_index": 0,
      "proof_present": true,
      "request_nonce": null,
      "jti": "synthetic-j1",
      "iat": 100,
      "status": 400,
      "oauth_error": "use_dpop_nonce",
      "dpop_nonce_headers": ["synthetic-n1"],
      "browser_context": false,
      "cors_exposed_headers": []
    }
  ]
}
```

## Fields

- `role`: `authorization_server` or `resource_server`.
- `origin`: credential-free HTTPS origin only. Keep it separate from `endpoint`.
- `endpoint`: path beginning with `/`, without query or fragment.
- `request_id`: unique non-negative sequence number used to reject stale concurrent updates.
- `operation_id`: stable synthetic correlation label across an original request and its one retry.
- `retry_index`: `0` or `1`. A retry also requires `retry_of` equal to the challenged request ID.
- `proof_present`: presence only. When true, provide synthetic `jti` and integer `iat`; never provide a JWT.
- `request_nonce`: synthetic nonce represented in the request proof, or null.
- `status`: observed HTTP status.
- `oauth_error`: authorization-server JSON error name, when present.
- `www_authenticate_error`: resource-server challenge error name, when present.
- `dpop_nonce_headers`: zero or more separately captured field values. Do not pre-combine repeated fields.
- `browser_context`: whether browser JavaScript must read the response.
- `cors_exposed_headers`: response header names exposed to that browser context.

## Scope and ordering model

Nonce state is keyed by `role|origin|endpoint`. A singleton `DPoP-Nonce` on a successful response is an evidence-bearing proactive update. Within one scope, a response for a lower `request_id` cannot overwrite state learned from a higher request ID. This sequence rule is a conservative implementation recommendation for concurrent clients, not a claim that RFC 9449 defines request IDs.

## Output and exits

- `ready`, exit `0`: applicable evidence passed all enforced predicates.
- `not_applicable`, exit `0`: no DPoP proof/nonce/challenge signal exists.
- `blocked`, exit `1`: input parsed, then a protocol or safety predicate failed.
- `input_error`, exit `2`: unreadable, malformed, non-standard, secret-bearing, or unsupported input. It is never an expected protocol rejection.
