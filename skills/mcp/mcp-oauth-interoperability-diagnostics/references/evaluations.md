# Evaluations

Run the same three prompts against the no-skill baseline and the helper. Keep fixtures outside the published skill when evaluating; the examples below use reserved `.test` domains and contain no credentials.

## 1. Normal: exact discovery-to-retry flow

**Prompt:** An MCP `2025-11-25` resource challenges with protected-resource metadata and `tools.read`. The discovered resource, issuer, endpoints, authorization request, token request, granted scope, redirect URI, and PKCE evidence all match exactly; the bounded retry returns 200. Produce a machine-readable phase diagnosis.

**Assertions:** classification is `ready`; `valid` is true; no findings; next action remains bounded and metadata-only; exit `0`.

## 2. Difficult edge: normalized resource and dead-ended mid-session reauth

**Prompt:** During a mid-session `invalid_token` recovery, metadata publishes `https://mcp.example.test/mcp` but authorization uses a trailing slash. A new authorization redirect occurs, yet no token exchange is observed. Classify exact failures without exposing credentials or looping.

**Assertions:** classification is `blocked`; findings include `resource_indicator_mismatch` and `mid_session_reauth_incomplete`; recovery stops at the first failing phase; exit `1`, not input-error exit `2`.

## 3. Should not activate: transport-only upstream reset

**Prompt:** An unauthenticated MCP Streamable HTTP request returns a 502 after an intermediary reset. There is no 401/403, protected-resource metadata, authorization request, token request, or OAuth error. Diagnose the incident.

**Assertions:** classification is `not_applicable`; no OAuth finding is invented; route to transport/TLS/DNS/application diagnostics; exit `0`.

## Regression command

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s skills/mcp/mcp-oauth-interoperability-diagnostics/tests \
  -p 'test_*.py' -v
```
