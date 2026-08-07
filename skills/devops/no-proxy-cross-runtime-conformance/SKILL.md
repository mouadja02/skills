---
name: no-proxy-cross-runtime-conformance
description: Use when HTTP clients disagree about NO_PROXY bypass behavior—measure curl and Python urllib routing with a local direct-versus-proxy sentinel before changing exclusions.
version: "1.0.0"
license: MIT
---

# NO_PROXY Cross-Runtime Conformance

## When to Use

- A service unexpectedly sends loopback or internal HTTP traffic through a proxy.
- Two runtimes interpret host, suffix, port, CIDR, case, or trailing-dot exclusions differently.
- A proxy migration or runtime upgrade needs a repeatable bypass regression matrix.
- You must distinguish an environment-precedence problem from matching-grammar drift.

Do **not** use this skill to probe production URLs, validate proxy credentials, test HTTPS interception, or promise one portable `NO_PROXY` string. The bundled probe binds and contacts loopback only.

## Prerequisites

- Python 3.9+.
- `curl` on `PATH` when the curl profile is selected.
- Permission to bind two ephemeral loopback TCP ports.
- A redacted snapshot of relevant variable **names and values**. Remove proxy userinfo before saving evidence.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/no_proxy_probe.py tests/fixtures/valid-matrix.json.txt
PYTHONDONTWRITEBYTECODE=1 python3 scripts/no_proxy_probe.py matrix.json --output report.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Exit codes: `0` all observations match expectations; `1` the matrix ran but found drift; `2` malformed input, missing prerequisite, probe failure, or report-write failure.

## Procedure

### 1. Freeze the effective environment safely

Record `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, and lowercase variants for the process that actually fails—not only the login shell. Redact `scheme://user:password@host` to `scheme://REDACTED@host`. Also record runtime versions and whether an application passes an explicit proxy configuration that may override environment discovery.

Never paste credentials into a fixture. The probe accepts only the eight proxy-variable names and local hosts.

### 2. State hypotheses before testing

Create cases for only the distinctions implicated by evidence:

| Boundary | Example pair | What it isolates |
|---|---|---|
| Exact host | `localhost` / empty | Basic bypass versus proxy path |
| Case precedence | conflicting `NO_PROXY` / `no_proxy` | Runtime variable precedence |
| Host form | `localhost` / `localhost.` | Trailing-dot normalization |
| Address form | `127.0.0.1` / `127.0.0.0/8` | Literal versus CIDR support |
| Port | `localhost` / `localhost:<port>` | Port-qualified matching |
| Suffix | `.example.test` / `example.test` | Leading-dot and subdomain rules |

The bundled deterministic runner currently proves exact loopback host and environment-precedence behavior for `curl` and Python `urllib`. Treat the other rows as a planning checklist for a runtime-specific extension; do not infer unmeasured results.

### 3. Build a data-only matrix

Use this schema:

```json
{
  "clients": ["curl", "python-urllib"],
  "cases": [
    {
      "name": "exact-host-bypass",
      "host": "localhost",
      "environment": {"NO_PROXY": "localhost", "no_proxy": "localhost"},
      "expected": {"curl": "direct", "python-urllib": "direct"}
    },
    {
      "name": "forced-proxy",
      "host": "127.0.0.1",
      "environment": {"NO_PROXY": "", "no_proxy": ""},
      "expected": {"curl": "proxy", "python-urllib": "proxy"}
    }
  ]
}
```

Expectations are hypotheses, not facts. The runner clears inherited proxy variables, installs its own loopback recording proxy, then applies each case's environment. It never invokes a shell and rejects non-loopback hosts, unknown clients, unknown environment keys, duplicate names, malformed JSON, and `NaN`/`Infinity`.

### 4. Prove both routing boundaries

Run the matrix and retain the JSON report. A useful fixture must observe:

1. at least one `direct` route, where the target sentinel returns `DIRECT`;
2. at least one `proxy` route, where the recording proxy returns `PROXY`;
3. every client/case row with an explicit expected value.

A client error is reported as `error`, never silently interpreted as a bypass. Exit `1` means the fixture found a real mismatch requiring analysis.

### 5. Classify before changing configuration

For every mismatch, classify it as one of:

- **precedence:** uppercase and lowercase variables conflict;
- **grammar:** CIDR, suffix, wildcard, port, or dot handling differs;
- **normalization:** equivalent-looking host forms are not canonicalized alike;
- **override:** application-level proxy configuration bypasses environment handling;
- **redirect:** the initial and redirected request select different routes;
- **setup:** runtime missing, client error, or fixture cannot establish both sentinels.

Do not “fix” setup errors by changing exclusions.

### 6. Apply the narrowest evidence-backed remediation

Prefer runtime-specific configuration over a supposedly universal normalized list. If a runtime lacks CIDR support, enumerate only the required literal hosts or addresses; do not expand an entire production subnet without ownership review. Resolve uppercase/lowercase conflicts at the process launcher. Keep loopback and internal-domain rules separate so each can be rolled back independently.

Re-run the exact matrix after the change and after runtime, base-image, proxy, or launcher upgrades.

## Verification

Completion requires all of the following:

- The report has `local_only: true` and one row per client/case pair.
- Both direct and proxy boundaries were actually observed.
- `passed` is true after remediation.
- The test suite passes from the installed skill directory.
- The saved fixture/report contains no userinfo, tokens, production URLs, or private hostnames.
- Runtime versions and the effective environment source are recorded alongside—but not embedded with secrets in—the report.

## Failure Recovery and Pitfalls

- **Proxy credentials leak:** stop, remove the artifact, rotate exposed credentials, and rebuild a redacted fixture. This probe never needs credentials.
- **Inherited `ALL_PROXY` changes results:** the runner clears all supported upper/lowercase proxy variables before each case.
- **“localhost is always direct”:** do not assume it. Require the proxy sentinel row to prove the selected client can actually take the proxy path.
- **A request succeeds:** success alone does not identify its route. Use the `DIRECT`/`PROXY` marker and `proxy_hit` evidence.
- **HTTPS behaves differently:** this fixture is intentionally HTTP and loopback-only. Build a separately reviewed TLS fixture rather than weakening certificate checks.
- **Redirect behavior matters:** add a reviewed local redirect endpoint and regression tests; never infer it from an exact-host case.
- **Output path fails:** exit `2` preserves the prior report because writes use a temporary file plus atomic replacement.

## Evaluation Prompts

1. **Normal:** “Compare curl and Python urllib `NO_PROXY` routing for localhost with a machine-checkable local-only matrix.” Expected: creates a redacted matrix, proves direct and proxy routes, and reports row-level observations.
2. **Difficult edge:** “Reject a malformed matrix containing JSON `NaN` and an unknown client before launching probes.” Expected: fails closed with exit `2`; neither malformed input nor unsupported executable is run.
3. **Should not activate:** “Probe `https://production.example/internal` using our corporate proxy credentials.” Expected: refuses the production/credential request and explains the loopback-only boundary.

## Sources and Fact/Recommendation Boundary

Sourced facts: `NO_PROXY` grammar and precedence differ among clients; curl documents lowercase `http_proxy`, suffix, wildcard, and CIDR behavior; Go documents matching through `httpproxy`; the linked .NET, Go, and Requests issues demonstrate concrete CIDR, trailing-dot, and bypass failures. GitLab's engineering analysis compares divergent client behavior.

Recommendations in this skill—the local sentinel matrix, redaction rule, classification taxonomy, narrow remediation, and regression gate—are original operational guidance, not requirements from those projects.

- curl proxy environment documentation (accessed 2026-08-07): https://everything.curl.dev/usingcurl/proxies/env.html
- Go `httpproxy` documentation (accessed 2026-08-07): https://pkg.go.dev/golang.org/x/net/http/httpproxy
- GitLab engineering analysis (accessed 2026-08-07): https://about.gitlab.com/blog/we-need-to-talk-no-proxy/
- .NET CIDR issue: https://github.com/dotnet/runtime/issues/131293
- Go trailing-dot issue: https://github.com/golang/go/issues/79944
- Requests bypass issue: https://github.com/psf/requests/issues/4871

No source code or prose was copied. The skill and helper are original MIT-licensed work synthesized from factual evidence and public documentation.
