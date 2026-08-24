---
name: http-early-hints-proxy-conformance
description: Use when HTTP 103 Early Hints may be dropped, merged, reordered, or corrupted across reverse proxies—replay bounded synthetic exchanges, compare normalized hop captures, and preserve the final response.
version: "1.0.0"
license: MIT
---

# HTTP Early Hints Proxy Conformance

## When to Use

- An origin emits `103 Early Hints`, but a client behind one or more intermediaries does not observe it.
- A proxy, CDN, gateway, browser loader, or HTTP-version translation changed.
- A rollout needs repeatable evidence that multiple hints and the final response remain separate.
- Adjacent captures are available from owned staging systems.

Do **not** activate when there is only a final response with `Link` fields, for WebSocket `101` upgrades, or to probe third-party infrastructure. This is a propagation/localization workflow, not a performance benchmark, vulnerability scanner, or proof that a client acted on a preload.

## Prerequisites

- Owned ephemeral listeners or an authorized staging chain; never send probes to unrelated systems.
- Capture access at each ingress/egress boundary, with credentials and cookies redacted.
- Python 3.10+ for the offline analyzer.
- A fixed request, timeout, protocol matrix, proxy configuration, and rollback owner.

## Quick Reference

```bash
python3 scripts/analyze_early_hints.py normalized-captures.json > report.json
# 0 + ready: 103 sequence and final response preserved
# 0 + not_applicable: reference emitted no 103
# 2 + blocked: divergence, malformed input, ambiguity, or limit failure
# 3: input/output failure; treat as blocked
```

The analyzer consumes normalized semantic events, not packets. It never opens a network connection. `protocol` is one of `http/1.1`, `h2`, or `h3`; headers are ordered `[name,value]` pairs; `body_sha256` is an optional lowercase digest of a synthetic final body.

```json
{"schema_version":1,"hops":[
  {"name":"origin-egress","protocol":"http/1.1","events":[
    {"status":103,"headers":[["link","</app.css>; rel=preload"]]},
    {"status":200,"headers":[["content-type","text/plain"]],"body_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]},
  {"name":"proxy-egress","protocol":"h2","events":[
    {"status":103,"headers":[["link","</app.css>; rel=preload"]]},
    {"status":200,"headers":[["content-type","text/plain"]],"body_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}
]}
```

## Procedure

### 1. Freeze the boundary and controls

Map the ordered chain, for example `origin → proxy A → proxy B → client`. Pin versions, configuration, TLS termination, ALPN, cache state, retries, redirects, and buffering. Use a unique synthetic path and response body. Disable retries and cache hits so one request produces one observable sequence.

Prepare three controls:

1. one `103` followed by final `200`;
2. multiple ordered `103` responses followed by the same final response;
3. final `200` only, optionally with an ordinary final `Link` field.

A final `Link` is not an Early Hint. `101 Switching Protocols` is terminal, unlike ordinary informational responses. Never use production secrets or weaponized framing examples.

**Completion:** every tested leg and its protocol are named, and fixtures are synthetic, bounded, and reproducible.

### 2. Capture direct origin first

Send the fixed request to the owned origin with a short deadline. Record each response event before any proxy. Require each `103` to have no body and require one terminal final response. Preserve header ordering and repeated `Link` fields. Hash only the inert final body.

If the direct control does not produce the expected sequence, stop: the proxy chain is not yet under test.

### 3. Add one hop at a time

Replay the unchanged fixture directly, then through proxy A, then through A+B. Capture semantic response events at adjacent ingress/egress points. HTTP/1.1 uses sequential header blocks; HTTP/2 and HTTP/3 use informational HEADERS events. Normalize those representations to the same event model—do not compare raw framing bytes across protocols.

Bound the run: three repetitions per supported protocol path, one fresh connection per request, no retries or redirects, and a short explicit timeout. Mark an unobservable boundary as `unobservable`; do not assign blame across it.

### 4. Run the fail-closed analyzer

Create the normalized JSON in chain order and run the bundled helper. It compares ordered `103` `Link` fields between adjacent observations and verifies terminal status plus the optional body digest. Outcomes are:

- `pass`: hints and final response are preserved;
- `dropped`: upstream hints disappear;
- `merged_into_final`: hint `Link` fields moved to the final response—still a failure;
- `mutated_or_reordered`: count, order, or fields differ;
- `final_response_changed`: terminal status or supplied body digest differs.

Malformed JSON, non-finite numbers, duplicate hop names, unsupported protocols, invalid statuses, CR/LF/NUL header values, informational bodies, events after a final response, missing terminal responses, I/O errors, and resource-limit failures block the gate.

**Completion:** the report is `ready`, or the first divergent adjacent pair is retained as the repair boundary.

### 5. Repair only the localized hop

Inspect informational-response callbacks/forwarding, response buffering, header filters, cache behavior, and protocol translation at the first divergent component. Change one setting or build at a time. Do not “repair” loss by copying hint headers into the final response, and do not weaken final-response checks.

If capture is incomplete, add instrumentation and rerun rather than inferring behavior. On timeout or malformed evidence, keep the deployment blocked.

### 6. Prove recovery and final preservation

Replay the exact frozen controls after the change. Require all repetitions to retain every ordered `103`, keep informational and final fields separate, preserve final status/body evidence, and leave the final-only negative control `not_applicable`. Compare before/after reports and retain component versions and rollback metadata.

Deployment is `ready` only when every supported path passes. This proves propagation, not preload execution or latency improvement; test client preload behavior separately if required.

## Failure Recovery

- **Origin control fails:** repair or instrument the origin before testing intermediaries.
- **Boundary is unobservable:** stop localization there; add owned ingress/egress capture or test a shorter chain.
- **Analyzer returns blocked:** inspect `findings`; do not treat merged final headers or partial evidence as success.
- **Capture parser disagrees with another tool:** retain the semantic event trace and fail closed until the disagreement is resolved.
- **Interrupted rollout:** restore the pinned proxy configuration, drain test connections, and replay only synthetic controls.
- **I/O or limit failure:** fix the local path or choose a measured explicit limit; never bypass the gate silently.

## Verification

From the installed skill directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/analyze_early_hints.py capture.json | python3 -m json.tool
```

Tests must pass. A preserved multiple-`103` chain must return `ready`; a dropped, merged, reordered, malformed, incomplete, or final-changing chain must return `blocked`; a final-only chain must return `not_applicable`.

## Evaluation Prompts

1. **Normal:** A `103` reaches the origin-facing capture, but a client behind two proxies sees only the final `200`. Localize the failing hop with bounded owned tests.
2. **Difficult edge:** Check multiple `103` responses, malformed framing, `101`, HTTP/1.1-to-HTTP/2 translation, final preservation, and recovery without exploit payloads.
3. **Should not activate:** A service emits only a final `200` with `Link` preload headers and no informational response.

## Sources and Recommendations

**Sourced facts:** RFC 8297 defines `103` as an informational response before a final response and discusses intermediary handling. Public Caddy and Brave reports demonstrate dropped Early Hints in independent proxy paths. The NGINX report demonstrates why non-`101` informational response sequencing and final-response boundaries must be handled correctly.

**Recommendations:** hop-by-hop replay, semantic normalization, body digests, fail-closed input limits, final-only negative controls, and the deployment gate are conservative operational guidance synthesized for this skill.

- RFC 8297, 103 Early Hints: https://www.rfc-editor.org/rfc/rfc8297.html
- Caddy issue 6041: https://github.com/caddyserver/caddy/issues/6041
- NGINX issue 1427: https://github.com/nginx/nginx/issues/1427
- Brave issue 57534: https://github.com/brave/brave-browser/issues/57534

No source prose or code was copied. The helper and tests are original and use only the Python standard library.
