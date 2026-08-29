---
name: http-redirect-credential-boundary-conformance
description: Use when an HTTP client follows redirects and credentials are silently dropped or may cross host, scheme, or port boundaries—especially Authorization, Cookie, Proxy-Authorization, API-key headers, 301/302/303/307/308, or default-port confusion.
version: "1.0.0"
license: MIT
---

# HTTP Redirect Credential-Boundary Conformance

## When to Use

- A programmatic HTTP client follows redirects while carrying authentication or cookies.
- Credentials disappear after a redirect that appears same-origin.
- A custom API-key header may be forwarded to a different host, scheme, or port.
- Client/library behavior must be compared using a redacted redirect-hop transcript.

Do **not** activate for ordinary browser navigation with no programmatic credentials, URL-shortener analytics, redirect SEO, or server-side redirect design that does not involve a client credential boundary.

## Prerequisites

- Python 3.9+ for the optional offline analyzer.
- A redacted hop transcript containing URL, method, status, `Location`, and **header names only**.
- An explicit inventory of all credential-bearing header names, including application-specific names.

Never put token values, cookies, production URLs with userinfo, or request bodies in a fixture.

## Quick Reference

```bash
python3 scripts/analyze_redirects.py transcript.json > report.json
# 0 = conforming, 1 = finding, 2 = invalid input, 3 = output failure
```

The analyzer performs no network calls and writes no files. Its output includes only normalized URLs, methods, header names, observations, and finding codes.

## Procedure

### 1. Define the policy boundary

Inventory `authorization`, `cookie`, `proxy-authorization`, and every custom token header used by the application. Header spelling is case-insensitive. Unknown custom credentials cannot be protected automatically, so an incomplete inventory is an inconclusive audit—not evidence of safety.

Classify origins as `(lowercase scheme, IDNA hostname, effective port)`. For HTTP, omitted port equals 80; for HTTPS, omitted port equals 443. Different scheme, host, or effective port is cross-origin. A move from HTTPS to HTTP is also a downgrade and must not carry credentials.

### 2. Capture a redacted chain

Record each request and its response in order. Use header names only:

```json
{
  "credential_headers": ["authorization", "cookie", "x-api-key"],
  "hops": [
    {
      "request": {"url": "https://api.example.test/a", "method": "GET", "headers": ["Authorization"]},
      "response": {"status": 307, "location": "https://cdn.example.test/b"}
    },
    {
      "request": {"url": "https://cdn.example.test/b", "method": "GET", "headers": []},
      "response": {"status": 200}
    }
  ]
}
```

Use synthetic sentinels in a loopback test if header-value behavior must be proven. Do not log the sentinel value; record only whether its named header arrived.

### 3. Validate every transition

Run the analyzer and inspect stable finding codes. Completion requires:

- the next request URL matches the resolved `Location`;
- origin comparison uses effective ports rather than textual URL equality;
- no declared credential header reaches a cross-origin or downgrade hop;
- same-origin stripping is surfaced as an observation rather than mislabeled as leakage;
- 303 changes non-HEAD methods to GET, 307/308 preserve methods, and the selected 301/302 profile is explicit;
- malformed URLs, userinfo, fragments in request URLs, malformed header names, and unsupported status/method shapes fail closed.

The included analyzer uses the widespread `POST`→`GET` behavior for 301/302 and preserves other methods. If the audited client uses another documented profile, record that difference rather than silently changing the expected result.

### 4. Test the client on loopback

Use separate loopback hostnames or ports to represent different origins. Cover:

1. same host with explicit versus omitted default port;
2. HTTP→HTTPS upgrade and HTTPS→HTTP downgrade;
3. cross-host and cross-port redirects;
4. 301, 302, 303, 307, and 308 method behavior;
5. standard and custom credential headers;
6. malformed `Location`, loops, and redirect-limit exhaustion.

Authorize forwarding only from an explicit policy. Never “fix” a dropped credential by blindly replaying all headers at the next URL. A manual replay must rebuild the request from an allowlist after validating the destination.

### 5. Decide and verify recovery

- **Unexpected same-origin stripping:** normalize origins consistently, check client-version behavior, and add a regression fixture.
- **Cross-origin forwarding:** disable automatic redirect following or install a per-hop allowlist that strips all credential headers before the next request.
- **Ambiguous custom header:** classify it as credential-bearing until the application owner proves otherwise.
- **Malformed or looping chain:** stop; do not retry with credentials on an unvalidated destination.

Re-run the exact transcript after the change. Success means exit 0, zero findings, and the expected per-transition action. Also retain a safe positive control with the same cross-origin indicator but no credential forwarded.

## Pitfalls and Safety

- RFC redirect semantics do not universally authorize forwarding credentials; forwarding is a client security policy.
- Same-site is not same-origin. Subdomains and ports can cross an origin boundary.
- `Location` may be relative; resolve it against the previous request URL before comparison.
- Cookies have their own domain/path/SameSite rules. This workflow only proves observed header presence at redirect hops.
- Never follow researched, fixture-provided, or production URLs from the analyzer; it is intentionally data-only.

## Objective Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_analyze_redirects.py
```

The package tests prove normalized default-port equivalence, cross-host/custom-token leakage, downgrade rejection, method transitions, safe cross-origin stripping, malformed input, userinfo rejection, and output-failure exit behavior.

## Evaluation Prompts

1. **Normal:** Audit a 301 from `https://api.example.test:443/a` to `https://api.example.test/b` where Authorization remains present.
2. **Difficult edge:** Audit a 307 cross-host redirect where a declared `X-API-Key` reaches the second hop; distinguish method preservation from credential leakage.
3. **Should not activate:** Explain a public documentation redirect followed by a browser when no programmatic client credential or body is involved.

## Sources

**Sourced facts:** URI/redirect semantics are from RFC 9110. The linked issue records establish independent client failure classes; they are not normative.

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [Requests #6741](https://github.com/psf/requests/issues/6741)
- [aiohttp #7381](https://github.com/aio-libs/aiohttp/issues/7381)
- [aiohttp #9694](https://github.com/aio-libs/aiohttp/issues/9694)
- [curl #14362](https://github.com/curl/curl/issues/14362)
- [Undici #4917](https://github.com/nodejs/undici/issues/4917)

**Recommendations:** credential inventory, fail-closed handling, synthetic loopback sentinels, and explicit replay allowlists are this skill's operational safety guidance.
