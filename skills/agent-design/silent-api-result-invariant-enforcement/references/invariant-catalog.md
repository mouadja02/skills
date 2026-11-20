# Invariant Catalog

Select checks by proven API capability. Never apply a relation because its name sounds relevant.

## Request checks

| Check | Preconditions | Class | Failure action | Cost | Blind spots |
|---|---|---|---|---:|---|
| Parameter allowlist | Authoritative parameter list for this API version | Exact | Reject before transport | 0 | Filters embedded inside an opaque query string; valid name with wrong value format |
| Enum/value grammar | Normative value grammar or enum | Exact | Reject before transport | 0 | Semantically wrong but grammatically valid values |
| Request fingerprint | Canonical serialization is defined locally | Exact for provenance | Refuse answer binding | 0 | Does not prove API behavior |

## Filtered count checks

For conditions `F = C1 ∧ … ∧ Ck`, test every position `i`:

```text
N(F) + N((F without Ci) ∧ NOT Ci) = N(F without Ci)
```

Preconditions:

1. the operation applies all conditions with conjunction;
2. `NOT Ci` is a true, exhaustive complement under the API's null/missing-value semantics;
3. every count covers the same stable snapshot or consistency window;
4. totals are uncapped and use the same population;
5. probes have no side effects.

Class: exact only when all five hold. Cost: two additional reads per condition per attempt. Test every condition position; checking only the last filter misses field-specific failures elsewhere.

Do not use the identity when a backend ignores negation. That behavior can create a false alarm on an otherwise correct positive query; mark complement capability unsupported instead.

## Record-list checks

| Check | Preconditions | Class | Failure action | Blind spots |
|---|---|---|---|---|
| Every record satisfies every filter | Filter predicate can be evaluated from returned fields | Exact | Withhold offending records/result | Omitted fields prevent evaluation |
| Unique IDs | Key is documented stable and unique | Exact | Withhold/deduplicate only under separate policy | Same entity legitimately appears as multiple versions |
| Complete length equals total | Response declares a complete result and total has same scope | Exact | Withhold completeness claim | Ordinary pages and approximate totals |
| Page non-overlap | Stable pagination snapshot and unique key | Exact | Withhold assembled result | Concurrent mutations or unstable ordering |
| Monotonic sort | Sort key and null ordering are normative | Exact | Withhold order-dependent result | Locale/collation mismatch |
| Range bounds | Inclusive/exclusive bounds are normative | Exact | Withhold out-of-range records | Server-side rounding or timezone conversion must be specified |

## Identity and lookup checks

A returned resource ID, tenant, date window, or code must match the request when the API contract says it is echoed. Missing or mismatched identity is exact evidence only when the field is normative and unambiguous. A similar display name is not an identity check.

## Write checks

Read-after-write can verify a documented postcondition only when:

- the write was authorized and isolated;
- an idempotency key prevents duplicate effects;
- read consistency and propagation delay are documented;
- the read targets the exact created/updated identity.

Never blindly retry a write because a read-back failed. The write may have succeeded while the observation path failed.

## Learned checks

Examples include historical ranges, common field presence, empirical relationships, anomaly scores, or categories mined from clean traces. Record the training window and estimated false-alarm evidence. Learned failures warn by default; they do not justify withholding as proven invalid.

## Decision matrix

| First attempt | Same request recheck | Decision |
|---|---|---|
| Exact checks pass | Not run | `verified` |
| Exact check fails | Full recheck passes | `verified_on_recheck` using only the second value |
| Exact check fails | Full recheck fails | `withheld`; raw values hidden |
| Exact probe cannot run | Not speculative | `unsupported` or `error` |
| Learned check fails | Optional diagnostic repeat | `warned`; value remains explicitly unverified by that rule |

## Universal limitations

- Same-source consistency cannot detect a consistently lying API that preserves every tested relation.
- A finite check set cannot prove properties it does not encode.
- Snapshot drift can break valid relations; use consistent reads or classify the check as unsupported.
- Verification establishes consistency with selected invariants, not global truth.
