# Input Contract

The analyzer accepts one JSON object. Unknown keys are ignored unless they are credential-bearing. Keep fixtures synthetic.

```json
{
  "kind": "webauthn",
  "public_origin": "https://login.example.test:8443",
  "rp_id": "login.example.test",
  "public_suffix": "test",
  "allowed_origins": ["https://login.example.test:8443"],
  "ceremony": {
    "registration": {"origin": "https://login.example.test:8443", "rp_id": "login.example.test"},
    "authentication": {"origin": "https://login.example.test:8443", "rp_id": "login.example.test"}
  },
  "proxy": {
    "derive_from_forwarded": true,
    "direct_peer_trusted": true,
    "edge_strips_client_forwarded": true,
    "headers_agree": true,
    "trusted_hop_count": 2,
    "observed_hop_count": 2,
    "forwarded_origin": "https://login.example.test:8443"
  },
  "credential_rp_ids": ["login.example.test"]
}
```

`public_suffix` is evidence supplied from a current audited PSL-capable resolver. The helper only checks the declared relationship; it intentionally has no hidden network call and no bundled stale PSL.

Web origins must be HTTPS origins without userinfo, path, query, or fragment. Default port 443 is canonicalized away; other ports remain. IP literals are blocked because their acceptance requires an environment-specific policy. Native Android origins must match the explicit `android:apk-key-hash:` form.

Output `classification` is `ready`, `blocked`, `not_applicable`, or (on stderr) `input_error`. Findings are violation predicates. Observations such as forwarded-origin derivation or explicit native origins are evidence indicators and do not alone block the result.
