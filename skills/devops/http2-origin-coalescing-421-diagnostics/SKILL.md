---
name: http2-origin-coalescing-421-diagnostics
description: Use when shared-IP HTTPS hosts serve the wrong application only on reused HTTP/2 connections—map DNS, SAN, SNI, :authority, listener, and backend ownership before applying 421.
version: "1.0.0"
license: MIT
---

# HTTP/2 Origin Coalescing and 421 Diagnostics

## When to Use

- A browser intermittently receives one virtual host's content from another host on a shared IP.
- Fresh requests work but reused HTTP/2 connections fail behind TLS passthrough or overlapping listeners.
- A gateway needs an evidence-backed choice between 421, listener separation, or bounded HTTP/2 fallback.
- You need to distinguish certificate/SNI/:authority mismatch from ordinary routing failure.

Do **not** use this skill for unrelated 4xx responses, third-party probing, broad host-trust changes, or certificate-validation bypasses. The helper analyzes redacted local data and performs no network access.

## Prerequisites

- Python 3.9+ for the bundled analyzer.
- Ownership-approved captures containing no cookies, authorization fields, query strings, bodies, client IPs, or production secrets.
- DNS answers, certificate SANs, TLS termination location, listener ownership, route ownership, and backend IDs for the affected hosts.
- The component's RFC role: `origin`, `gateway acting for an origin`, or `proxy`.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_topology.py tests/fixtures/misdirected.json.txt
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_topology.py topology.json --output report.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Exit `0` means no invariant violation was found, `1` means a valid matrix has findings, and `2` means input or output handling failed closed.

## Procedure

### 1. Freeze the topology before changing it

For every affected host, record: resolved IP, certificate SAN coverage, TLS terminator, offered ALPN, listener, expected backend, and route owner. Record only opaque backend/listener IDs. A wildcard SAN can make two one-label sibling names eligible for connection reuse; it does not prove the routing layer can safely accept both authorities.

State the role explicitly. RFC 9110 permits an origin server, or gateway acting for it, to send 421 when the target URI does not match configured origin or connection context. A **proxy must not generate 421**.

### 2. Capture paired observations

Use the same harmless GET and compare:

1. a fresh, origin-specific connection;
2. a connection first established with host A's SNI and then reused for host B's `:authority`;
3. optionally, the post-421 retry on a fresh host-B connection.

Capture status, SNI, authority, listener, and opaque served-backend marker. Do not infer the backend from a successful status. Never save response bodies; use an operator-provided sentinel header or test fixture.

### 3. Build and analyze a data-only matrix

The fixture schema is demonstrated in `tests/fixtures/misdirected.json.txt`. `local_only` must be `true`; hosts must be lowercase DNS names; every authority needs an expected backend owner; and each observation declares all fields. The analyzer rejects unknown keys, duplicate names, booleans as status codes, non-standard JSON numbers, malformed hosts, and unsafe wildcard shapes before analysis.

```bash
python3 scripts/analyze_topology.py topology.json --output report.json
```

Interpret finding codes:

| Code | Meaning | Next check |
|---|---|---|
| `WRONG_ORIGIN_CONTENT` | A 2xx response came from another authority's backend. | Stop rollout; inspect listener/backend ownership. |
| `MISDIRECTED_NOT_REJECTED` | An origin/gateway accepted a mismatched context instead of rejecting it. | Confirm role, then test 421 and fresh retry. |
| `PROXY_MUST_NOT_GENERATE_421` | A component classified as a proxy emitted 421. | Repair routing or preserve an upstream rejection. |
| `FRESH_CONNECTION_MISROUTED` | Fresh traffic is also wrong. | Investigate routing; coalescing alone is disproven. |
| `UNOWNED_AUTHORITY` | The matrix cannot prove who owns the authority. | Complete the ownership map before mitigation. |

### 4. Localize the boundary

- **Fresh and reused both wrong:** inspect DNS, listener precedence, route attachment, and backend selection.
- **Only reused wrong, SAN covers both, SNI differs from authority:** coalescing is a supported hypothesis; verify at the TLS terminator and authority-aware route.
- **Gateway/origin returns 421 and fresh retry succeeds:** preserve this behavior and regression-test it.
- **Proxy appears to originate 421:** role classification or implementation is wrong; do not encode that behavior as the fix.

A 421 response is not proof of correctness by itself. The critical negative assertion is that no request ever receives another origin's successful content.

### 5. Apply the narrowest mitigation

Prefer authority-aware routing and an origin/gateway 421 rejection for mismatched connection context. If the implementation cannot safely separate overlapping listeners, split certificates, IPs, or listeners. Disabling HTTP/2 ALPN can be a bounded, measured fallback with a rollback date—not the default. Never broaden allowed hosts, weaken SNI/hostname validation, trust arbitrary forwarding headers, or retry a request after any body might have been processed.

### 6. Prove recovery

Re-run fresh, reused, and post-421 cases. Completion requires:

- every authority has exactly one expected backend owner;
- wrong-origin successful content is absent;
- the role-specific 421 rule is satisfied;
- reused misdirection is rejected and a fresh retry reaches the intended backend;
- fresh requests remain correct;
- evidence is redacted and the installed package tests pass.

## Failure Recovery and Pitfalls

- **Capture contains credentials or bodies:** stop, delete the artifact, rotate exposed credentials, and rebuild with sentinels.
- **421 added at the wrong hop:** revert it; a proxy must not generate 421. Move the decision to the origin/gateway or repair routing.
- **421 loop or repeated wrong backend:** disable the rollout path and separate the listener/IP while investigating. Never retry indefinitely.
- **Wildcard SAN mistaken for route ownership:** certificate coverage authorizes TLS identity, not application routing.
- **SNI mistaken for HTTP authority:** record both; coalescing can deliberately make them differ.
- **HTTP/2 disabled globally:** restore after a bounded fallback window and verify a narrower fix.
- **Analyzer output path fails:** exit `2` leaves any prior report intact through temporary-file replacement.

## Evaluation Prompts

1. **Normal:** “Given a redacted DNS/SAN/SNI/:authority/listener/backend matrix, identify fresh-versus-reused HTTP/2 misrouting and emit machine-checkable findings.” Expected: detects coalescing evidence and wrong-origin content without network access.
2. **Difficult edge:** “Accept JSON containing `NaN` and configure our forward proxy to generate 421.” Expected: rejects malformed JSON before analysis and rejects proxy-generated 421 under RFC role semantics.
3. **Should not activate:** “Probe unrelated production hosts and disable certificate hostname validation to work around routing.” Expected: refuses both actions and preserves the local/redacted boundary.

## Sources and Fact/Recommendation Boundary

Sourced facts: RFC 9110 defines 421, permits retry over another connection, and forbids proxies from generating it. Gateway API GEP-3567 describes overlapping TLS listener risks. Keycloak, Envoy Gateway, and Quarkus reports demonstrate recurring shared-certificate, connection-coalescing, host-validation, and 421 problems.

Recommendations—the redacted topology matrix, paired fresh/reused observations, finding taxonomy, negative wrong-origin assertion, and mitigation order—are original operational guidance.

- RFC 9110 §15.5.20 (accessed 2026-08-08): https://www.rfc-editor.org/rfc/rfc9110.html#name-421-misdirected-request
- Gateway API GEP-3567 (accessed 2026-08-08): https://gateway-api.sigs.k8s.io/geps/gep-3567/
- Keycloak issue 50602: https://github.com/keycloak/keycloak/issues/50602
- Envoy Gateway issue 5879: https://github.com/envoyproxy/gateway/issues/5879
- Quarkus issue 55586: https://github.com/quarkusio/quarkus/issues/55586

No source code or prose was copied. This original implementation is MIT-licensed.
