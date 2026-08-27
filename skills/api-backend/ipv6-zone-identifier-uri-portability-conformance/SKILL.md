---
name: ipv6-zone-identifier-uri-portability-conformance
description: Use when scoped or link-local IPv6 input containing an interface name/index works in one CLI, URL parser, HTTP client, resolver, or OS but fails or changes in another. Classify UI, URI, socket, and wire boundaries offline before any network probe.
version: "1.0.0"
license: MIT
---

# IPv6 Zone Identifier Boundary Conformance

## When to Use

- A link-local or scoped-multicast IPv6 target such as `fe80::1%eth0` works in one tool but not another.
- A URL parser rejects, rewrites, double-decodes, or misidentifies a bracketed scoped host.
- Parser output, hostname policy, interface lookup, and socket behavior disagree.
- You need a redacted, offline preflight before a bounded local network test.

Do **not** activate for an ordinary IPv6 literal with no zone selector, or for DNS, routing, firewall, TLS, or HTTP failures that occur after the scoped address is already proven equivalent end to end.

## Prerequisites

- Python 3.10+ for the bundled offline inspector.
- Exact input mode and raw bytes: `ui`, `uri`, or `socket`.
- Parser/runtime versions and, when lookup parity matters, a redacted list of valid local interface names or indices.
- Explicit approval before any real resolver, interface, or network action. The helper performs none.

## Quick Reference

```bash
python3 scripts/inspect_scoped_ipv6.py fixture.json > report.json
# 0: no error records; 1: parsed report contains error records
# 2: unreadable/malformed input or invalid top-level schema; 3: output failure
```

Input shape:

```json
{
  "max_zone_length": 64,
  "records": [
    {"id":"ui","mode":"ui","input":"fe80::1%eth0","known_zones":["eth0"]},
    {"id":"uri","mode":"uri","input":"http://[fe80::1%25eth0]:8080/status"},
    {"id":"socket","mode":"socket","input":"[ff02::1%3]:5353","known_zones":["3"]}
  ]
}
```

## Current Standards Boundary

**Sourced facts:** RFC 9844 (August 2025) obsoletes RFC 6874 and reverts RFC 6874's change to generic URI syntax. It requires UIs that accept non-global IPv6 addresses to provide a way to select a zone, recommends the RFC 4007 `address%zone` presentation where practical, and says its normative recommendations do not apply to URIs fetched by web browsers. RFC 4007 defines scoped-address architecture; a textual zone has local significance and is not part of the 128-bit address sent on the wire.

**Conservative policy in this skill:** treat `%25zone` inside a URI as an observed legacy/parser extension, not a portable current standard. Never recursively decode. Accept zones only on link-local or multicast literals, restrict fixture zones to `[A-Za-z0-9_.-]+`, cap their length, and require explicit local lookup evidence before connecting. Applications with a broader OS-specific zone grammar may relax that policy only after differential tests.

## Procedure

### 1. Freeze the representation boundary

Record the exact input before parsing and assign one mode:

| Mode | Expected outer form | Meaning |
| --- | --- | --- |
| `ui` | `fe80::1%eth0` | User-facing RFC 4007 presentation. |
| `uri` | `scheme://[...]/` | Generic URI parser boundary; `%25zone` is legacy/implementation-specific after RFC 9844. |
| `socket` | `fe80::1%eth0` or `[ff02::1%3]:5353` | Local resolver/socket presentation, not URI syntax. |

Do not validate one form and dispatch another. Preserve the original bytes, parser version, parsed host, hostname, port, canonical IPv6 address, and separate zone value.

**Completion:** every observation names its mode and no implicit decode or mode conversion remains.

### 2. Run the offline inspector

Create a synthetic or redacted fixture and run the quick-reference command. The helper:

1. parses brackets and ports before IPv6 conversion;
2. recognizes the URI delimiter `%25` but labels it obsolete/non-portable;
3. decodes a URI zone at most once;
4. rejects malformed escapes, suffix injection, empty/control-bearing zones, invalid ports, and zones on unscoped addresses;
5. compares the zone only with a supplied `known_zones` list; and
6. emits stable JSON without DNS, interface enumeration, or network access.

An expected-invalid case passes the test only when the fixture itself parses and the record is rejected with the intended finding.

**Completion:** exit status and every error finding are accounted for; warnings are not silently promoted to portability claims.

### 3. Compare real parsers without connecting

For each application parser/runtime, capture these fields from the same redacted matrix:

```text
runtime/version | raw input | accepted | serialized form | host | hostname | port | zone | error
```

Include at least:

- raw UI `%` versus legacy URI `%25`;
- `%2525` to expose accidental recursive decoding;
- numeric and named zones;
- empty zones, malformed escapes, controls, Unicode, and overlength values;
- bracket suffix injection such as `[fe80::1%25]evil.example]`;
- a scoped multicast address with a port;
- a global IPv6 literal without a zone as the negative activation control.

A parser accepting input is evidence, not proof of safety. Require agreement between the policy parser and the exact parser used by the eventual connector.

**Completion:** disagreements are explicit and no accepted parse has been mistaken for a successful interface lookup or connection.

### 4. Resolve the zone locally and explicitly

Only after offline syntax and policy pass, obtain the interface name/index using the host OS's documented API. Prefer separate address and zone fields. For low-level POSIX flows, convert the address and map the interface independently rather than passing a composite string blindly to `inet_pton()`.

Fail closed when the zone is absent where routing needs one, unavailable locally, ambiguous across namespaces/containers, or changed between validation and use. Never guess an interface or silently strip the zone.

**Completion:** the local interface identity is proven in the same namespace and immediately before the bounded connector test.

### 5. Prove the boundary transition

With explicit approval, use a disposable, link-local-only target and a short timeout. Record:

1. the validated address and local interface identity;
2. the exact socket metadata (for example, scope ID) without credentials;
3. whether the connector preserved the same host/zone tuple; and
4. packet-capture evidence only when policy permits it.

The zone selects local egress context; do not serialize it as IPv6 packet bytes or forward a textual zone received from an untrusted peer. Browser support remains a separate origin-model problem—do not infer it from CLI success.

**Completion:** either the approved local transition succeeds with identity preserved, or the report stops at the first proven mismatch.

## Failure Recovery

- **Parser accepted an injected suffix:** block dispatch, preserve a redacted raw/parsed pair, upgrade or replace the parser, and add the input as a regression fixture.
- **Double-decoding changed the zone:** remove recursive decoding; preserve the once-decoded value and reject ambiguity.
- **Interface lookup failed:** do not fall back to a default interface. Recheck namespace, interface lifecycle, and name/index mapping.
- **URI and socket forms disagree:** keep `{address, zone, port}` as structured data and format only at the immediate API boundary.
- **A network probe started unexpectedly:** stop it, rotate any non-synthetic credentials it could have exposed, and return to the offline fixture.

## Verification

Run from the installed skill directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/inspect_scoped_ipv6.py fixture.json > report.json
```

Verify that tests cover normal UI input, legacy URI syntax, one-pass decoding, injected suffixes, empty/control zones, multicast plus port, unscoped negative controls, malformed JSON/schema, duplicate IDs, expected-invalid classification, and broken stdout. Confirm `offline: true` in every report and review exit codes numerically.

## Pitfalls and Unsafe Operations

- Do not cite RFC 6874 as current; RFC 9844 obsoleted it.
- Do not recursively percent-decode or compare a pre-decode allowlist value with a post-decode connector value.
- Do not use a URL parser's acceptance as proof that its resolver or HTTP transport supports the same scoped host.
- Do not place real hostnames, tokens, cookies, or private interface inventories in fixtures.
- Do not probe arbitrary link-local targets, follow redirects, or bind/listen as part of diagnosis.
- Do not trust a textual zone supplied over the network; zone identifiers are locally significant.

## Evaluation Prompts

1. **Normal:** Compare `fe80::1%eth0`, `http://[fe80::1%25eth0]:8080/`, and `2001:db8::1%eth0` across UI, URI, socket, and wire boundaries using current RFC status.
2. **Difficult edge:** Classify `%2525`, injected bracket suffix, empty/NUL zones, numeric multicast zones, and unavailable interfaces without network access; prove one-pass decoding.
3. **Should not activate:** Decide whether a global IPv6 URL with no percent sign or interface selector needs this workflow.

## Sources

- [RFC 9844 — Entering IPv6 Zone Identifiers in User Interfaces](https://www.rfc-editor.org/rfc/rfc9844.html) (current Proposed Standard; obsoletes RFC 6874)
- [RFC 4007 — IPv6 Scoped Address Architecture](https://www.rfc-editor.org/rfc/rfc4007.html)
- [Go issue 78569 — zone parsing suffix injection](https://github.com/golang/go/issues/78569)
- [Requests issue 6808 — multi-digit zone failure](https://github.com/psf/requests/issues/6808)
- [aiohttp issue 10314 — link-local zone regression](https://github.com/aio-libs/aiohttp/issues/10314)
- [Bruno issue 5797 — encoded zone rejected](https://github.com/usebruno/bruno/issues/5797)

All procedures and code are original synthesis. Standards and issues are factual evidence only; no third-party code or prose is copied.
