# Normalized Evidence Schema

Use only redacted metadata. The helper never sends requests and refuses common secret-bearing fields, bearer values, URL userinfo, and sensitive URL query parameters.

## Root object

```json
{
  "schema_version": 1,
  "profile": "mcp-2025-11-25",
  "context": "initial",
  "target_resource": "https://mcp.example.test/mcp",
  "challenge": {
    "status": 401,
    "error": "invalid_token",
    "resource_metadata": "https://mcp.example.test/.well-known/oauth-protected-resource/mcp",
    "scope": "tools.read"
  },
  "resource_metadata": {
    "url": "https://mcp.example.test/.well-known/oauth-protected-resource/mcp",
    "resource": "https://mcp.example.test/mcp",
    "authorization_servers": ["https://login.example.test"],
    "scopes_supported": ["tools.read"]
  },
  "authorization_server_metadata": {
    "issuer": "https://login.example.test",
    "authorization_endpoint": "https://login.example.test/authorize",
    "token_endpoint": "https://login.example.test/token",
    "code_challenge_methods_supported": ["S256"]
  },
  "authorization_request": {
    "endpoint": "https://login.example.test/authorize",
    "resource": "https://mcp.example.test/mcp",
    "scope": ["tools.read"],
    "redirect_uri": "http://127.0.0.1:8765/callback",
    "pkce_method": "S256"
  },
  "token_request": {
    "endpoint": "https://login.example.test/token",
    "resource": "https://mcp.example.test/mcp",
    "scope": ["tools.read"],
    "redirect_uri": "http://127.0.0.1:8765/callback",
    "pkce_verifier_present": true
  },
  "token_response": {
    "status": 200,
    "granted_scope": ["tools.read"]
  },
  "retry": {"status": 200}
}
```

`context` is `initial` or `mid_session`. Omit phases that were not observed; never invent them. Presence booleans prove only that the capture established presence—not a value. Do not include headers wholesale.

## Exactness rules

- Preserve the resource URI exactly, including trailing slash and path.
- Preserve issuer and endpoint strings exactly as discovered.
- Record scope as tokens, not a reordered display string, except the challenge's wire `scope` value.
- Record the same redirect URI in authorization and token phases.
- Use HTTPS for resource and metadata URLs. A loopback HTTP redirect URI is accepted; other HTTP URLs fail input validation.
- An expected-invalid fixture must parse successfully and be rejected for its intended finding. Input exit `2` is not a conformance pass.

## Secret boundary

Never include authorization codes, access/refresh/ID tokens, client secrets, PKCE verifiers, cookies, `Authorization` headers, URL userinfo, or sensitive query parameters. If any entered a fixture, stop, quarantine the artifact according to local policy, rotate exposed credentials when necessary, and recapture metadata only.
