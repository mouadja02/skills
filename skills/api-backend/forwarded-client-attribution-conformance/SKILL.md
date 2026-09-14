---
name: forwarded-client-attribution-conformance
description: Use when proxy or CDN headers produce wrong, spoofable, or inconsistent client IP/port attribution in logs, rate limits, audits, access controls, or geolocation. Validate Forwarded and X-Forwarded-For chains offline against an explicit trust policy.
version: "1.0.0"
license: MIT
---

# Forwarded Client Attribution Conformance

## When to Use

- A proxied application records a load balancer, CDN, or attacker-supplied address as the client.
- Frameworks disagree about the first, last, fixed-hop, or nearest-untrusted address.
- Audit, rate-limit, access-control, fraud, or geolocation logic consumes a forwarded address.
- A `Forwarded` node without a port is being combined with the proxy socket port.

Do **not** activate for ordinary reverse-proxy setup when no application decision or record uses client attribution. This workflow does not configure a proxy, discover provider CIDRs, or authorize network changes.

## Prerequisites

- Python 3.10+ for the bundled offline analyzer.
- Redacted header field instances in arrival order and the authenticated socket peer.
- One explicit policy: trusted CIDRs or fixed hop count.
- Current, operator-controlled evidence for every trusted proxy range or path length.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_forwarded_chain.py fixture.json > report.json
# 0: all records pass; 1: one or more records fail attribution
# 2: unreadable/malformed input or invalid schema; 3: output failure
```

```json
{"records":[{"id":"edge","mode":"xff-cidr","socket_peer":"10.0.0.9:43100","trusted_cidrs":["10.0.0.0/8"],"x_forwarded_for":["198.51.100.7, 10.0.0.8"]}]}
```

Modes are `xff-cidr`, `forwarded-cidr`, and `fixed-hop-count`. The helper is dependency-free, bounded, data-only, and performs no DNS or network access.

## Trust Boundary

**Sourced facts:** RFC 7239 defines ordered `Forwarded` elements and warns that the field can be modified by any node, including the client; useful conclusions require trusted proxies and protected links. Express supports Boolean, CIDR, and numeric trust profiles and checks CIDR chains right-to-left. Werkzeug requires an exact trusted value count for each forwarded header.

**Recommendation:** prefer CIDR trust when network identity is stable and authenticated. Use fixed-hop mode only when every route to the application has the same verified length. Never call “leftmost” or “rightmost” a trust policy by itself.

## Procedure

### 1. Name the consumer and consequence

Record the exact field that consumes the attributed address and what it controls. Separate logging from authorization: a wrong audit label is not the same failure as a spoofable allowlist, but both need provenance.

**Completion:** each use names its decision, data-retention boundary, and failure behavior.

### 2. Freeze the wire observations

Capture, in order and with secrets removed:

- authenticated socket peer address and port;
- every `Forwarded` or `X-Forwarded-For` field instance;
- proxy path and edge rewrite/append contract;
- framework/runtime version and current trust configuration.

Keep repeated field instances separate until grammar-aware parsing. Do not comma-split quoted `Forwarded` values. Keep node address and optional port separate.

**Completion:** the fixture preserves field-instance and element order without inventing missing values.

### 3. Declare one policy

| Mode | Selection rule | Fail-closed boundary |
| --- | --- | --- |
| `xff-cidr` | Start at socket peer; walk right-to-left while each IP belongs to an explicit trusted CIDR. | malformed, unknown, or obfuscated nearest boundary; no untrusted IP remains |
| `forwarded-cidr` | Parse RFC 7239 elements, then apply the same authenticated-peer walk. | malformed syntax, missing/duplicate `for`, or non-IP nearest boundary |
| `fixed-hop-count` | Require the declared number of header nodes and select exactly that position from the socket. | observed path is shorter than configured count |

An indicator such as “multiple hops” is not itself a violation. The violation is selecting across an unverified boundary, silently clamping a short path, or misattributing identity data.

**Completion:** policy, trusted inputs, and refusal conditions are explicit before parsing.

### 4. Run the analyzer

Run the quick-reference command against synthetic or redacted data. Review `selected_source`, not only `selected_address`. For header nodes, `selected_port` is `null` unless that same node supplied a valid port; the socket port belongs to the proxy connection.

The helper preserves IPv6 brackets and explicit ports, recognizes `unknown` and obfuscated nodes, rejects malformed quoted strings and duplicate parameters, caps input/records/hops, rejects JSON `NaN`/`Infinity`, and exits nonzero on findings.

**Completion:** every record either identifies one attributable IP with provenance or fails at the nearest unresolved boundary.

### 5. Differentially test the application

Replay the same synthetic matrix through the framework parser without external traffic. Include:

- a direct untrusted peer with spoofed headers;
- one and multiple trusted proxies;
- two valid routes with different lengths;
- IPv4, quoted bracketed IPv6 with port, `unknown`, and obfuscated nodes;
- repeated field instances, malformed quotes, duplicate `for`, and empty elements;
- a missing client port and a safe positive control sharing the same multi-hop indicator.

Compare the application's selected address **and provenance** with the offline report. Parser agreement is not proof that the proxy actually rewrites hostile inbound fields.

**Completion:** unsafe and safe controls both behave as declared, and every route exercises the same trust contract.

### 6. Prove recovery at the edge and application

In a disposable environment, configure the edge to remove or overwrite client-supplied forwarding fields, append only authenticated observations, and configure the application with matching trust policy. Repeat the matrix from both direct and proxied paths.

Do not auto-fetch mutable provider CIDRs inside request handling. Pin an operator-reviewed source and monitor changes through a separate controlled update path.

**Completion:** direct spoofing fails, valid paths select the expected client, short paths fail closed, and audit output retains provenance without unnecessary raw chains.

## Failure Recovery

- **Direct peer was trusted:** disable forwarded attribution, preserve redacted evidence, correct ingress reachability/trust, then rerun direct-spoof controls.
- **Path lengths differ:** replace fixed-hop policy with authenticated CIDRs or make edge rewriting uniform; never choose the leftmost value as a fallback.
- **Nearest node is `unknown` or obfuscated:** return unattributable; do not skip it to find a convenient earlier IP.
- **Port was synthesized:** keep it unknown and repair the consumer schema so address and port have independent provenance.
- **Provider ranges changed:** fail closed or use a reviewed transition set; do not silently trust arbitrary fetched data.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_forwarded_chain.py tests/fixtures/matrix.json
```

Verify all three modes, direct-spoof rejection, repeated fields, quoted IPv6, unknown/obfuscated boundaries, short fixed paths, malformed JSON/schema, `NaN`, duplicate IDs, size/hop caps, and broken stdout. An expected-invalid fixture passes only when parsing succeeds and the intended record-level finding is emitted; input/I/O failure is not equivalent.

## Pitfalls and Unsafe Operations

- Do not trust all forwarded headers unless the last reachable proxy removes hostile inbound values.
- Do not infer trust from private addressing alone when untrusted workloads can reach the application.
- Do not combine `Forwarded` and `X-Forwarded-For` into one guessed chain; define precedence at the trusted edge.
- Do not resolve hostnames or accept DNS names as client IP nodes in the offline trust walk.
- Do not store production headers, session identifiers, or full internal topology in fixtures or reports.
- Do not use attribution as authentication; proxy identity and client identity are separate claims.

## Evaluation Prompts

1. **Normal:** Select a client from two `X-Forwarded-For` hops and a trusted socket peer under CIDR policy, preserving source index and a null missing port.
2. **Difficult edge:** Compare a too-short fixed-hop path with repeated `Forwarded` fields ending in an obfuscated nearest boundary and quoted IPv6.
3. **Should not activate:** Configure a proxy for a static site when no downstream decision records or consumes a client address.

## Sources

- [RFC 7239 — Forwarded HTTP Extension](https://www.rfc-editor.org/rfc/rfc7239.html)
- [Express behind proxies](https://expressjs.com/en/guide/behind-proxies.html)
- [Werkzeug ProxyFix](https://werkzeug.palletsprojects.com/en/stable/middleware/proxy_fix/)
- [Authentik issue 25811 — changing CDN trust ranges](https://github.com/goauthentik/authentik/issues/25811)
- [Metabase issue 80096 — first/last client address disagreement](https://github.com/metabase/metabase/issues/80096)
- [Spring Framework issue 37114 — misleading synthesized client port](https://github.com/spring-projects/spring-framework/issues/37114)

All instructions, code, and fixtures are original synthesis. Sources establish facts and observed failures; no third-party prose or code is copied.
