# RFC 9460 SVCB/HTTPS Evaluations and Scenarios

This document outlines the evaluation scenarios used to benchmark the skill against a standard baseline.

## Scenario 1: Normal ServiceMode Record with ALPN and Port

**Prompt:**
```text
Evaluate this RFC 9460 HTTPS DNS record presentation text for deployment:
example.com. 7200 IN HTTPS 1 . alpn="h2,h3" port=443
Analyze its mode, target name, wire encoding constraints, and parameter validity. Output a JSON object with keys: mode, target_name, valid, errors, wire_keys.
```

**Expected Outcome:**
- `mode`: "ServiceMode"
- `target_name`: "."
- `valid`: true
- `errors`: empty
- `wire_keys`: `[1, 3]` (ascending order: alpn=1, port=3)

## Scenario 2: Edge Case Pitfalls (AliasMode with Params & no-default-alpn assignment)

**Prompt:**
```text
Evaluate this RFC 9460 presentation record containing potential pitfalls:
example.com. 3600 IN HTTPS 0 target.example.com. alpn="h3"
and this second record:
example.com. 3600 IN HTTPS 1 svc.example.com. mandatory=no-default-alpn,port port=8443 no-default-alpn="true"
Identify any RFC 9460 violations in both records. Output a JSON object with: record1_valid, record1_errors, record2_valid, record2_errors.
```

**Expected Outcome:**
- `record1_valid`: false (RFC 9460 §2.4.2: AliasMode cannot contain SvcParams)
- `record2_valid`: false (RFC 9460 §7.1: no-default-alpn must have empty value in presentation and 0 wire length)

## Scenario 3: Negative Control / Should Not Activate

**Prompt:**
```text
We need to set up standard DNS records for our mail server: an MX record pointing to mail.example.com with priority 10, and an SPF TXT record 'v=spf1 mx ~all'. Give me the BIND zone file configuration.
```

**Expected Outcome:**
- Standard DNS zone configuration provided.
- Does not invoke SVCB/HTTPS logic or parameters.
