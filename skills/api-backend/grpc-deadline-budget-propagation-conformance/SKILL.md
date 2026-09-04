---
name: grpc-deadline-budget-propagation-conformance
description: Use when gRPC deadlines grow across proxy hops, grpc-timeout parsing disagrees, server clamps are unclear, or expired RPC work continues without cancellation.
version: "1.0.0"
license: MIT
---

# gRPC Deadline Budget Propagation Conformance

## When to Use

- `grpc-timeout` is rejected, rounded, or expanded by a client, proxy, or server.
- A downstream RPC outlives the caller's deadline or elapsed time is deducted twice/not at all.
- A service maximum deadline clamp or missing-deadline policy needs verification.
- Unary or streaming work continues after deadline expiry without cancellation evidence.

Do **not** use for generic HTTP client timeouts, retry/backoff policy, latency tuning without gRPC metadata, or claims about `DEADLINE_EXCEEDED` versus `CANCELLED` from status alone.

## Prerequisites

- Exact runtime, proxy, and language versions.
- A synthetic or redacted monotonic trace; never include authorization metadata or payloads.
- Python 3.10+ for the offline standard-library helper.
- Current gRPC protocol and deadline documentation reopened before production decisions.

## Quick Reference

```bash
SKILL_DIR=skills/api-backend/grpc-deadline-budget-propagation-conformance
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/analyze_grpc_deadline.py" trace.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$SKILL_DIR/tests" -p 'test_*.py' -v
```

Exit `0` means `ready` or `not_applicable`; exit `1` means a parsed trace is `blocked`; exit `2` means input/schema failure and proves no conformance result.

## Procedure

### 1. Establish scope and clocks

Record `kind: grpc_deadline_trace`, RPC type, the original `grpc-timeout`, and monotonic elapsed durations—not wall-clock timestamps. Keep each RPC/stream separate. If no gRPC deadline evidence exists, classify the case `not_applicable`.

**Completion:** the capture has one synthetic RPC and no payload or credentials.

### 2. Parse the wire timeout before arithmetic

The gRPC HTTP/2 protocol defines a positive integer of at most eight ASCII digits followed by one unit: `H`, `M`, `S`, `m`, `u`, or `n`. Reject whitespace, signs, decimals, unknown units, zero, and nine-digit values. Convert with integer arithmetic; do not use floating point.

**Completion:** malformed metadata becomes a protocol finding, never a guessed duration or a successful expected-invalid test.

### 3. Deduct elapsed time once per hop

For each hop, subtract that hop's monotonic `elapsed_ns` from the budget it received. The forwarded timeout may be equal to or less than the remainder because implementations can round or clamp; it must not exceed the remainder. The next hop receives the forwarded value, not the pre-hop budget.

A server maximum is an explicit local policy. Model it as a clamp before the first hop and report it as an observation; do not call a smaller budget a propagation violation.

**Completion:** every forwarding transition is non-expanding and has an explicit received, elapsed, available, and sent budget.

### 4. Separate omission, expiry, and cancellation

An omitted deadline is not malformed. Require an explicit `missing_deadline_policy` of `allow` or `block`; do not silently invent infinity. If the available budget reaches zero before dispatch, block dispatch. After expiry, check whether application work remains active and whether cancellation was observed.

Deadline expiry, cancellation observation, and final status are distinct evidence. Scheduler races can produce `DEADLINE_EXCEEDED` at the caller while a server observes `CANCELLED`; do not infer propagation correctness from either code alone.

**Completion:** expired-before-dispatch and work-after-expiry have separate findings.

### 5. Exercise every RPC shape

Run the same budget invariant for `unary`, `client_streaming`, `server_streaming`, and `bidi_streaming`. Streaming does not refresh the original deadline when messages arrive. Application loops must check cancellation at bounded work intervals.

**Completion:** the selected RPC type is explicit and cancellation evidence covers blocking/stream work, not only handler return.

### 6. Repair and rerun

Fix the first owner boundary: parser, hop propagation, server clamp configuration, or application cancellation polling. Rerun normal, malformed, safe-clamp, expired, and not-applicable fixtures. Only then use a separately authorized loopback/staging RPC.

**Completion:** helper output is `ready`, all packaged tests pass, and any live probe is bounded and credential-free.

## Findings

| Finding | Meaning |
| --- | --- |
| `invalid_timeout` | Present metadata violates the wire grammar. |
| `deadline_budget_expanded` | A hop sent more time than remained after its own elapsed duration. |
| `expired_before_dispatch` | No budget remained when a hop attempted dispatch. |
| `missing_deadline_blocked` | Omission conflicts with the declared policy. |
| `work_continued_after_expiry` | Work remains active after the original effective budget with no cancellation observation. |

## Failure Recovery and Pitfalls

- **Input exit 2:** repair JSON/schema/I/O first; do not count it as an expected-invalid pass.
- **Negative or non-integer elapsed duration:** treat the trace as unusable, not as protocol evidence.
- **Clock skew:** capture local monotonic deltas. gRPC propagates a timeout with elapsed time deducted to avoid wall-clock skew.
- **Rounding:** permit reductions; never permit expansion. Preserve exact captured wire values.
- **Status ambiguity:** `DEADLINE_EXCEEDED` and `CANCELLED` are observations, not sufficient violation predicates.
- **Unsafe capture:** stop if payloads or credentials appear; recapture metadata-only synthetic evidence.
- **Production mutation:** the helper is offline and makes no network calls. Do not terminate server work or rewrite proxy settings automatically.

## Objective Verification

A complete run proves:

- strict 1–8 digit timeout grammar and all six units;
- integer, monotonic, exactly-once hop accounting;
- safe server clamp and explicit missing-deadline policy;
- expired-before-dispatch and work-after-expiry boundaries;
- all four RPC shapes share the invariant;
- malformed input is distinct from parsed-invalid protocol evidence;
- a non-gRPC timeout remains `not_applicable`.

See [trace schema](references/trace-schema.md) and [evaluation prompts](references/evaluations.md).

## Sources and Scope

The timeout grammar and deadline propagation/cancellation behavior are sourced facts. Server clamps, missing-deadline policy, and cancellation polling intervals are deployment recommendations that must be supplied explicitly.

This is original synthesis; no source code or issue prose was copied. gRPC, Armeria, grpc-web, and Praxis declare Apache-2.0.

- [gRPC HTTP/2 protocol](https://grpc.github.io/grpc/core/md_doc__p_r_o_t_o_c_o_l-_h_t_t_p2.html)
- [gRPC deadline guide](https://grpc.io/docs/guides/deadlines/)
- [Armeria maximum grpc-timeout](https://github.com/line/armeria/issues/5709)
- [Armeria timeout scheduler](https://github.com/line/armeria/issues/3155)
- [grpc-web client deadlines](https://github.com/improbable-eng/grpc-web/issues/1029)
- [Praxis deadline propagation](https://github.com/praxis-proxy/praxis/issues/275)
