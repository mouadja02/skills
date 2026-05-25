---
name: cloudflare-registrar
description: "Cloudflare Registrar: domain availability check, prices, registration via API."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Cloudflare Registrar

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use for Cloudflare Registrar domain availability, pricing, listing, and registration.

## Guardrails

- Always run `domain-check` immediately before registration.
- Registration is billable/non-refundable. Get explicit confirmation before registering.
- Do not print tokens or secrets.

## Required Credentials

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN` (with Registrar permissions)

## Check Availability / Pricing

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/registrar/domain-check" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com"]}' | jq '.result'
```

## List Registrations

```bash
curl -s \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/registrar/registrations" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq '.result[] | {domain, expires_at, auto_renew}'
```

## Register (after explicit confirmation)

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/registrar/registrations" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_name": "example.com",
    "auto_renew": false,
    "privacy_mode": "redaction"
  }' | jq '.result'
```

## Notes

- Always confirm pricing in `domain-check` before registering.
- Registration is immediate and non-reversible — require explicit user confirmation.
- `privacy_mode: "redaction"` enables WHOIS privacy.
