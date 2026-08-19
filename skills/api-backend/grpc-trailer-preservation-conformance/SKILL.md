---
name: grpc-trailer-preservation-conformance
description: Use when gRPC status or trailing metadata disappears or changes across proxies, gateways, meshes, tunnels, or runtimes, especially for trailers-only and size-boundary failures.
version: "1.0.0"
license: MIT
---

# gRPC Trailer Preservation Conformance

## When to Use

- A direct gRPC call works but a proxied call loses `grpc-status`, `grpc-message`, status details, or application trailers.
- A trailers-only error, zero-message success, or large trailing-metadata response behaves differently across hops.
- A client reports a synthesized `UNKNOWN`/`INTERNAL` status after a proxy or HTTP/2 runtime change.
- A bounded regression matrix is needed before changing trailer/header limits.

Do **not** activate for ordinary JSON HTTP endpoints, request-header limits, message serialization failures, or gRPC-Web unless a separately pinned translation profile is available. Do not probe third-party or production endpoints.

## Prerequisites

- Python 3.9+ for the packaged offline analyzer.
- Owned ephemeral origin, intermediary, and client fixtures with versions/configuration frozen.
- Synthetic redacted metadata, small byte limits, fixed call deadlines, and retries/hedging disabled.
- Trailer-aware instrumentation at each available ingress and egress. Record HTTP version and ALPN per leg.

## Quick Reference

| Observation | Classification | Action |
| --- | --- | --- |
| Expected terminal multimap and clean `END_STREAM` | `PRESERVE` | Continue to next case/hop |
| Documented fail-closed signature plus same-call limit telemetry | `DECLARED_LIMIT` | Review configured policy; do not call it preservation |
| Trailer absent/mutated without that evidence | `LOSS` | Investigate first divergent hop |
| Translation profile, reset, or capture is ambiguous | `OTHER_FAILURE` | Pin the profile or improve instrumentation |

An HTTP `200` or intact DATA body is never enough: the gRPC terminal status belongs in trailing metadata, including status `0`. A trailers-only response is a terminal header block, not ordinary initial metadata.

## Procedure

### 1. Freeze the route and expected result

Record origin, every intermediary, client, HTTP version/ALPN on each leg, relevant response-header/trailer limits, and component accounting rules. Define the origin expectation **before** executing the call: response-message count, terminal status, and ordered value lists for each lower-cased trailer key. Compare decoded fields or gRPC API bytes, not HPACK bytes or frame boundaries.

Use distinct routes when practical: direct origin, each single intermediary, and the full chain. If a boundary cannot be observed, label it `UNOBSERVABLE`; do not infer it.

### 2. Run the bounded semantic matrix

Use synthetic call IDs and no credentials. Cover:

1. unary success with one message and `grpc-status: 0`;
2. trailers-only application error with zero messages;
3. zero-message successful server stream;
4. application error with `grpc-status-details-bin` and duplicate custom trailer values;
5. a small control far below every limit;
6. equality/below/first-failing/above probes around one explicit test-only trailer limit.

Vary only one padding value during a size search. Cap payloads at 16 KiB, use fresh connections, and stop after 12 probes. A non-monotonic result is not a proven size boundary.

At every boundary keep these observations separate: initial headers, DATA/message count, trailing headers, and terminal `END_STREAM` or reset. Redact values before storing a trace.

### 3. Analyze the redacted hop trace

The helper accepts data-only JSON and performs no network access. Field values are arrays so duplicate trailer values remain observable.

```json
{
  "version": 1,
  "cases": [{
    "id": "unary-ok",
    "expected": {
      "grpc_status": "0",
      "messages": 1,
      "trailers_only": false,
      "trailers": {"grpc-status": ["0"], "x-test": ["redacted"]}
    },
    "observations": [{
      "hop": "origin-egress",
      "http_version": "h2",
      "initial_headers": {"content-type": ["application/grpc"]},
      "messages": 1,
      "trailers_only": false,
      "trailers": {"grpc-status": ["0"], "x-test": ["redacted"]},
      "end_stream": true
    }]
  }]
}
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_trace.py trace.json
```

Exit `0` means all observations preserve the expected semantics. Exit `1` means at least one case diverges, including an intentional declared-limit result. Exit `2` means malformed input or output failure; that is not an expected-invalid pass.

For an intentional limit observation, set `declared_limit: true`, `limit_evidence: true`, a positive `configured_trailer_limit_bytes`, a bounded `rejection_signature`, and an empty trailer map. The helper deliberately refuses to infer policy from a configured number alone. It is a semantic trace oracle, not an HTTP/2 parser, packet decoder, performance benchmark, or proof that captured telemetry is truthful.

### 4. Localize and adjudicate

Read `first_divergent_hop`; then inspect that component's ingress and egress for the same synthetic call ID. The first boundary where a previously matching trailer multimap, status, message count, or terminal transition differs owns the initial investigation.

Call a failure `DECLARED_LIMIT` only when all are true:

- a below-boundary control preserves exactly;
- failure is repeatable and monotonic near the pinned limit;
- the first divergent component emits its documented fail-closed signature;
- same-call limit telemetry increments;
- no partial trailer set is forwarded as though complete.

Otherwise missing or changed terminal metadata is `LOSS`. A client-synthesized status describes downstream transport handling, not the origin's status.

### 5. Recover safely

Stop rollout and use the last known-good path if normal security/tenancy controls still hold. Disable automatic retries while outcome provenance is uncertain; reconcile non-idempotent operations through an idempotency key or authoritative application state. Fix protocol handling or pinned policy before raising limits. If large diagnostics trigger the boundary, emit a bounded correlation ID and retain protected details server-side rather than silently dropping trailers.

After a reset, use a fresh connection. Re-run the small control, trailers-only error, zero-message success, application error, and adjacent limit controls. Resume rollout only when every normal/below-limit cell preserves exactly and every deliberate over-limit cell fails closed with evidence.

## Pitfalls and Safety

- Do not treat HTTP success, a body, or client status alone as trailer preservation.
- Do not compare compressed HPACK lengths as application metadata size.
- Do not move `grpc-status` into initial metadata to make a checker pass.
- Do not assume all components count names, values, binary encoding, and overhead identically.
- Do not log production binary metadata, tokens, PII, stack traces, or full error details.
- Do not retry uncertain non-idempotent calls or sweep unbounded sizes.
- gRPC-Web and HTTP/1 translations need their own explicit representation rules.

## Objective Verification

From the installed package run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Completion requires packaged tests to pass, normal/trailers-only/zero-message fixtures to preserve, an unsafe missing-trailer fixture to localize the first lossy hop, and a safe positive control with the same configured-limit indicator to remain distinct from an evidenced fail-closed rejection.

## Evaluation Prompts

1. **Normal:** A direct unary call succeeds, but through two proxies the client reports `UNKNOWN` because `grpc-status` disappeared. Localize the first lossy hop with objective evidence.
2. **Difficult edge:** Build a bounded matrix for trailers-only errors, zero-message success, application error details, and equality/adjacent sizes around a configured trailer limit. Distinguish intentional rejection from silent loss.
3. **Should not activate:** An ordinary JSON HTTP/1.1 endpoint returns `502` and neither side uses gRPC. Route to ordinary HTTP proxy diagnostics instead.

## Sources

Sourced facts (accessed 2026-08-19):

- The gRPC HTTP/2 protocol defines response/trailers-only grammar, requires status in trailers even when OK, and discusses client field-list limits: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
- Cloudflared issue 1641 reports body and trailer loss through a tunnel: https://github.com/cloudflare/cloudflared/issues/1641
- Couper issue 968 reports response trailers dropped by a reverse proxy: https://github.com/coupergateway/couper/issues/968
- Linkerd issue 15199 reports trailer/status failure around a size boundary: https://github.com/linkerd/linkerd2/issues/15199
- Bun issue 21759 reports empty DATA frames, absent trailers, and an intermediary protocol error: https://github.com/oven-sh/bun/issues/21759

The matrix, analyzer schema, classification threshold, bounds, and recovery order are original recommendations. Issue material is factual demand evidence only; no source code or prose was copied.
