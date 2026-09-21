---
name: dns-svcb-https-parameter-conformance
description: Use when validating RFC 9460 DNS SVCB and HTTPS resource records, verifying presentation and wire-format parameter encodings, ensuring canonical ascending key order, or preventing AliasMode and ServiceMode deployment misconfigurations.
version: 1.0.0
author: Mouad Jaouhari
license: MIT
platforms: [linux, darwin]
metadata:
  hermes:
    tags: [dns, svcb, https, rfc9460, networking, http3, alpn, zonefile]
    related_skills: [http-message-signature-profile-conformance, http-redirect-credential-boundary-conformance]
---

# DNS SVCB and HTTPS Parameter Conformance (RFC 9460)

Validate, serialize, and audit RFC 9460 SVCB (type 64) and HTTPS (type 65) DNS resource records across zonefile presentation formats and wire RDATA encodings. Ensures strict adherence to AliasMode versus ServiceMode boundaries, enforces wire-level canonical SvcParamKey ascending ordering, prevents forbidden DNS name compression on TargetNames, and verifies parameter-specific syntax rules for `mandatory`, `alpn`, `no-default-alpn`, `port`, `ipv4hint`, `ech`, and `ipv6hint`.

## When to Use

- Deploying or auditing DNS HTTPS (type 65) or SVCB (type 64) resource records for HTTP/2, HTTP/3, and Encrypted ClientHello (ECH).
- Diagnosing DNS provider drift or zone compilation errors where empty parameters (e.g. `no-default-alpn`), quoted parameters, or key ordering trigger `FORMERR` or rejected zone loads (CoreDNS #5993, PowerDNS #15135, DNSControl #3814).
- Validating AliasMode (`SvcPriority = 0`) versus ServiceMode (`SvcPriority > 0`) invariants before publishing zone records.
- Verifying cross-runtime wire compatibility and canonical byte representations before feeding records into DNS authoritative nameservers or resolvers.

## When Not to Use

- Standard DNS CNAME, A, AAAA, MX, or TXT record validation where binding parameters do not apply.
- Live public DNS recursive query resolution or live network probing (use `dig` or standard resolver tools).
- TLS client certificate or PKI validation unrelated to DNS record parameters.

## Prerequisites

- Python 3.9+ (standard library only; no external dependencies).
- BIND-compatible presentation zone lines or hex-encoded raw DNS wire RDATA bytes.

## Quick Reference

Run the deterministic offline validator CLI on a zone presentation line:

```bash
python3 scripts/validate_svcb_record.py 'example.com. 7200 IN HTTPS 1 . alpn="h2,h3" port=443'
```

Inspect and validate raw DNS wire RDATA bytes (hex format):

```bash
python3 scripts/validate_svcb_record.py --wire 000100000100060268320268330003000201bb
```

Input JSON file evaluation:

```bash
python3 scripts/validate_svcb_record.py input.json
```

Sample input JSON:

```json
{
  "record": "example.com. 3600 IN HTTPS 1 svc.example.com. alpn=\"h3\" port=8443 no-default-alpn"
}
```

## Step-by-Step Procedure

### 1. Differentiate Record Mode (RFC 9460 §2.4)

Inspect `SvcPriority`:
- **AliasMode (`SvcPriority = 0`):**
  - Designed for apex domain aliasing (similar to CNAME but permitted at zone apex).
  - TargetName MUST NOT be `.` (root).
  - SvcParams MUST NOT be present. Any parameter attached to priority 0 is an RFC 9460 §2.4.2 violation.
- **ServiceMode (`SvcPriority > 0`):**
  - Supplies endpoint binding parameters for direct connection.
  - TargetName may be `.` (indicating that the target name matches the owner name) or a fully qualified domain name.
  - SvcParams supply transport capabilities (ALPN, port, IP hints, ECH).

### 2. Validate Parameter Invariants

- **`mandatory` (key 0):**
  - Value must be a non-empty list of SvcParamKeys.
  - MUST NOT include `mandatory` (key 0) itself.
  - Every key listed in `mandatory` MUST also appear as an active parameter in the same record.
- **`alpn` (key 1):**
  - Sequence of length-prefixed ASCII protocol strings (e.g. `h2`, `h3`).
  - Wire format requires 1-octet length followed by protocol bytes. Identifiers cannot be empty or exceed 255 octets.
- **`no-default-alpn` (key 2):**
  - Flag parameter indicating that the client cannot assume default protocol support.
  - In presentation format, it has no value (e.g. `no-default-alpn`, not `no-default-alpn="true"`).
  - In wire format, its value length MUST be exactly 0 octets. A non-zero length wire value is an error.
- **`port` (key 3):**
  - 2-octet unsigned big-endian integer (0–65535).
- **`ipv4hint` (key 4):**
  - Comma-separated list of valid IPv4 addresses; wire format must be a multiple of 4 bytes.
- **`ech` (key 5):**
  - Encrypted ClientHello ECHConfigList structure.
- **`ipv6hint` (key 6):**
  - Comma-separated list of valid IPv6 addresses; wire format must be a multiple of 16 bytes.

### 3. Enforce Canonical Wire Constraints (RFC 9460 §2.2)

- **TargetName Compression:** TargetNames in SVCB and HTTPS RDATA MUST NOT be compressed using DNS name compression pointers (`0xC0`). Parsers detecting compression in SVCB/HTTPS RDATA must reject the record.
- **Key Ordering:** In wire format, SvcParams MUST appear in strictly ascending order by `SvcParamKey` integer ID. Duplicate keys are strictly prohibited.

## Failure Recovery & Common Pitfalls

| Symptom | Cause | Remedy |
| :--- | :--- | :--- |
| `FORMERR` or provider reject on `no-default-alpn` | Tool serialized empty string as 1-octet empty string or boolean | Ensure wire length is 0 and presentation omits `=...` assignment |
| Record rejected with SvcParams in priority 0 | SvcParams placed on AliasMode | Move parameters to a ServiceMode record (priority > 0) or remove parameters from alias |
| Incompatible wire parser error on TargetName | Authoritative server applied DNS name compression | Use uncompressed IDNA/root wire format for SVCB/HTTPS TargetName |
| Client fails connection despite valid record | Mandatory key missing from parameter list | Verify all keys in `mandatory` are explicitly defined in the record |

## Objective Verification

Execute the test suite to verify all RFC 9460 presentation and wire validation paths:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"
```
