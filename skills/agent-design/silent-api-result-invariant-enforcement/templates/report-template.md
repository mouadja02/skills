# Silent API Verification Report

## Scope

- API and version:
- Operation:
- Request fingerprint:
- Evidence window / snapshot:
- Harness version:
- Fixture or environment:

## Capability inventory

| Capability | Supported / unsupported / unknown | Evidence |
|---|---|---|
| Parameter allowlist |  |  |
| Complement/negation |  |  |
| Complete-list retrieval |  |  |
| Stable unique key |  |  |
| Normative total semantics |  |  |
| Stable pagination/sort |  |  |
| Safe read-after-write |  |  |

## Check registry

| Check ID | Exact / learned | Preconditions | Extra-call cost | Failure action | Enabled |
|---|---|---|---:|---|---|
|  |  |  |  |  |  |

## Observation decision

- Observation ID:
- Requested value/records:
- First-attempt decision:
- Recheck decision:
- Final state: `verified` / `verified_on_recheck` / `withheld` / `warned` / `unsupported` / `error`
- Released value or withheld marker:
- Final-answer provenance binding:

## Probe evidence

| Attempt | Check ID | Inputs | Observed relation | Pass / fail / unavailable |
|---:|---|---|---|---|
|  |  |  |  |  |

## Cost and coverage

- Primary reads:
- Extra probe reads:
- Rechecks:
- Added latency:
- Rate-limit impact:
- Clean-fixture false alarms:
- Covered fault classes:
- Unsupported operations:

## Limitations

- Could a consistently lying API preserve these relations?
- Which filters or value formats remain opaque?
- Could snapshot drift invalidate a relation?
- Which learned checks can false-alarm?
- What independent source of truth is absent?

## Decision and rollback

- Release / warn / withhold / abstain:
- Reason:
- Disablement or rollback trigger:
- Owner and next review:
