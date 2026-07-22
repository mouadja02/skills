---
name: "durable-agent-workflows"
description: "Use when designing retryable or crash-resilient agent workflows, especially when tools can send, charge, publish, provision, or otherwise create duplicate side effects."
version: "2.0.0"
---

# Durable Agent Workflows

Build workflows that can resume without silently repeating externally visible work. Treat orchestration durability and side-effect safety as separate properties: a checkpoint can make a workflow resumable while still allowing an activity or tool to run more than once.

## When to Use

- An agent or job is retried after timeouts, worker loss, deploys, or checkpoint recovery.
- A tool can charge, send, publish, provision, trade, mutate records, or start costly work.
- A long-running tool may finish after its caller has timed out.
- A workflow needs human approval, durable waits, or crash recovery.
- Duplicate dispatches or uncertain remote outcomes must be diagnosed and tested.

## When Not to Use

- A short, read-only operation where duplicate execution is harmless and inexpensive.
- A request to retry an unknown production mutation immediately; reconcile it first.
- A request for exactly-once delivery as a transport guarantee. Design for repeated delivery and idempotent effects instead.

## Prerequisites

Before implementation, identify:

- the durable runtime or checkpoint store and its retry/timeout behavior;
- the authoritative database for operation records;
- provider support for idempotency keys or status lookup;
- business identifiers that represent one logical intent;
- retention, audit, and manual-reconciliation owners.

Never place credentials, authorization headers, payment data, or full sensitive tool arguments in operation keys or logs.

## Quick Reference

| Question | Required decision |
| --- | --- |
| Can this tool change external state? | Classify the effect before enabling retries. |
| What identifies one logical operation? | Derive a stable key from business intent, not an attempt or request ID. |
| Who may execute it? | Acquire a unique atomic claim before the effect. |
| Could the effect have committed before a timeout? | Record `ambiguous`; reconcile before retrying. |
| Does the provider accept an idempotency key? | Reuse the same key for every attempt of the same operation. |
| How is success replayed? | Persist and return a sanitized result reference. |
| How is safety proved? | Run concurrent-duplicate and crash-boundary fixtures. |

## 1. Separate Orchestration From Effects

Keep deterministic control flow in the workflow and nondeterministic work in activities or tools. A durable engine may replay workflow code and may execute an activity more than once around failures. Its retry policy does not prove that a side effect happens once.

Model each step with:

```text
workflow decision -> durable activity dispatch -> idempotency boundary -> provider/local effect
```

Checkpoint decisions and outputs, but do not assume that a completed external effect and its local checkpoint are atomic.

## 2. Classify Every Tool

Assign one class before setting retry behavior:

| Class | Examples | Default retry policy |
| --- | --- | --- |
| Pure/read-only | deterministic transform, immutable lookup | Bounded automatic retry |
| Naturally idempotent | set resource to an exact desired state | Retry after verifying semantics |
| Deduplicated mutation | payment API with provider idempotency key | Retry only with the same stable key |
| Reconciliable mutation | provision job with operation-status lookup | Query status before retry |
| Non-idempotent mutation | email send with no receipt lookup, market order | No automatic retry after uncertain dispatch |

Classification is about observable effects, not HTTP verbs or tool names. A nominally read-only call can still incur cost or start asynchronous work.

## 3. Define a Stable Operation-Key Contract

The key represents logical intent, independent of attempts, workers, checkpoints, and model-generated call IDs.

```text
operation_key = HMAC_SHA256(
  service_secret,
  canonical_json({
    tenant_id,
    workflow_type,
    workflow_instance,
    step_name,
    business_object_id,
    intent_version
  })
)
```

Recommendations:

1. Canonicalize field names, Unicode, numbers, and ordering before hashing.
2. Include tenant and operation scope to prevent cross-tenant collisions.
3. Include a semantic `intent_version` when a changed request should be a new operation.
4. Exclude timestamps, attempt counts, worker IDs, random request IDs, and secrets.
5. Store a separate request fingerprint. If the same key arrives with a different fingerprint, fail closed instead of replaying a mismatched result.
6. Keep key derivation stable for at least the provider's and local store's retention windows.

Use an HMAC when business fields could be guessed from a plain hash. Log only a short key prefix plus a trace ID.

## 4. Claim Work Atomically

A check-then-execute-then-insert sequence has a race: concurrent workers can both observe no row and both execute. Enforce uniqueness in the database and let one atomic insert win.

Example PostgreSQL shape:

```sql
CREATE TABLE agent_operations (
  operation_key text PRIMARY KEY,
  request_fingerprint text NOT NULL,
  state text NOT NULL CHECK (state IN (
    'pending', 'succeeded', 'failed_retryable', 'failed_terminal', 'ambiguous'
  )),
  owner_token text,
  lease_until timestamptz,
  provider_operation_id text,
  result_ref text,
  last_error_class text,
  attempt_count integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO agent_operations (
  operation_key, request_fingerprint, state, owner_token, lease_until
) VALUES ($1, $2, 'pending', $3, now() + interval '2 minutes')
ON CONFLICT (operation_key) DO NOTHING
RETURNING operation_key;
```

Interpret the result:

- Insert returned a row: this worker owns the first claim.
- Existing `succeeded`: return the stored sanitized result reference.
- Existing key with a different fingerprint: reject as a key-contract violation.
- Existing active `pending`: wait, poll with bounds, or return in-progress.
- Existing expired `pending`: treat the outcome as uncertain until reconciliation proves otherwise.
- Existing `ambiguous`: route to reconciliation; never blindly redispatch a non-idempotent mutation.

Do not use a cache-only lock as the record of truth. Locks can expire while a slow operation is still running.

## 5. Place the Transaction Boundary Correctly

### Local database effect

When the operation record and business mutation share a database, perform the mutation and transition to `succeeded` in one transaction. The unique claim prevents concurrent execution; transaction rollback prevents a committed mutation without its outcome record.

### Remote provider with idempotency support

1. Persist `pending` and commit the claim.
2. Call the provider with the same operation key on every attempt.
3. Persist the provider operation ID as soon as available.
4. Mark `succeeded` and store a sanitized result reference.
5. If the connection fails after dispatch, mark `ambiguous`; query by idempotency key or provider ID before retrying.

Confirm the provider's exact key scope, payload-mismatch behavior, response replay behavior, and retention window. Do not assume all providers implement these semantics alike.

### Remote provider without idempotency support

After an uncertain dispatch, do not retry automatically. Use a provider receipt, external object lookup, ledger query, or human review to determine whether the effect happened. If no authoritative reconciliation exists, keep the operation `ambiguous` and expose that state.

## 6. Use an Explicit State Machine

```text
new -> pending -> succeeded
              -> failed_terminal
              -> failed_retryable -> pending       only when retry is proven safe
              -> ambiguous -> succeeded            reconciliation found the effect
                           -> failed_retryable      reconciliation proved no effect
                           -> failed_terminal       operator decision
```

Require compare-and-set transitions that include the expected current state and owner token. Record reason codes, not raw sensitive responses. Never let a stale worker overwrite a result produced by a newer owner.

A lease controls ownership, not truth. Lease expiry means “the worker may be gone,” not “the external mutation did not happen.”

## 7. Configure Durable Execution

For Temporal, Inngest, queues, or a custom checkpoint loop:

- keep workflow code deterministic where the runtime requires it;
- set bounded retries, timeouts, and non-retryable error classes;
- heartbeat long activities when supported;
- keep the operation key stable across workflow replay and activity attempts;
- checkpoint sanitized references rather than large or secret-bearing responses;
- make approval waits durable and time-bounded;
- apply concurrency limits and cost circuit breakers.

Retry a workflow decision and retry a side effect under separate policies.

## 8. Reconcile Ambiguous Outcomes

Reconciliation order:

1. Query the local business transaction or outbox.
2. Query the provider by idempotency key or stored operation ID.
3. Search a narrow authoritative business identifier and time window.
4. Compare amount, recipient, payload fingerprint, and final status.
5. Transition with compare-and-set and record the evidence reference.
6. Escalate unresolved high-impact operations to a human; do not turn uncertainty into a retry.

Avoid fuzzy matching for money, trades, access changes, or deletion. “Probably not sent” is not proof of absence.

## 9. Retention and Recovery

Keep operation records at least as long as all of:

- maximum workflow replay or redelivery window;
- provider idempotency-key retention window;
- business dispute and audit window;
- maximum delayed-message lifetime.

When records must expire, archive only the minimum evidence needed to prevent unsafe replay. A retry arriving after deduplication retention has expired must not silently become a fresh mutation; require a new explicit intent or reconciliation.

Recovery rules:

- Database unavailable before claim: do not call the side-effecting provider.
- Persistence fails after remote success: preserve the same key and reconcile.
- Worker crashes during call: mark or infer `ambiguous`, then reconcile.
- Key/fingerprint mismatch: fail closed and investigate key derivation.
- Reconciliation unavailable: pause the operation and alert its owner.

## 10. Verification Gate

Run synthetic, secret-free fixtures in a disposable environment. Completion requires every assertion below:

1. **Concurrent duplicate:** 20 workers submit the same key; exactly one logical effect is observed and all callers converge on one result.
2. **Different intent:** changed business intent yields a different key and a second permitted effect.
3. **Fingerprint conflict:** same key with changed payload is rejected before dispatch.
4. **Crash before dispatch:** retry safely acquires or resumes without an effect.
5. **Crash after dispatch, before persistence:** state becomes `ambiguous`; no non-idempotent redispatch occurs.
6. **Provider replay:** repeated attempts use the identical provider key and return one provider operation.
7. **Slow original plus redelivery:** lease expiry does not create a second effect.
8. **Stale owner:** an old worker cannot overwrite the terminal state.
9. **Retention boundary:** an expired dedup record fails closed or requires explicit new intent.
10. **Observability:** traces expose state and reason codes but no secrets or raw sensitive payloads.

Verify the authoritative external system, not only mock call counts.

## Evaluation Prompts

Use these to evaluate whether the skill changes behavior observably.

### Normal

> Design retries for an agent tool that charges a customer, then may time out before checkpointing.

Pass if the response specifies a stable intent-derived key, atomic unique claim, provider key reuse, persisted result, and reconciliation before retrying an ambiguous charge.

### Difficult edge

> A worker's two-minute lease expired, but its ten-minute provisioning call may still be running. Another worker receives the same tool call. What should it do?

Pass if lease expiry is not treated as proof of failure, the second worker does not blindly execute, and the answer uses status reconciliation plus compare-and-set ownership/state transitions.

### Should not activate

> Refactor this pure in-memory JSON transformation for readability.

Pass if the response does not introduce a durable operation store or side-effect idempotency machinery.

## Common Pitfalls

- Deriving keys from attempt IDs, timestamps, or model tool-call IDs.
- Checking for a row before execution without an atomic unique claim.
- Treating timeout, lost response, or expired lease as proof that nothing happened.
- Reusing one key for changed payloads without fingerprint validation.
- Logging raw tool arguments, credentials, or provider responses.
- Claiming “exactly once” without defining the effect and authoritative verifier.
- Retaining provider keys longer than local deduplication records, or vice versa.
- Retrying every exception even after dispatch crossed the side-effect boundary.

## Sources and Scope

Sourced facts:

- Temporal documents that Activities may be retried and recommends idempotent Activity logic: https://docs.temporal.io/activity-definition
- Stripe documents its API idempotency-key behavior and retention details: https://docs.stripe.com/api/idempotent_requests
- CrewAI issue #5802 reports duplicate side effects when a successful tool execution is followed by task retry: https://github.com/crewAIInc/crewAI/issues/5802
- LangGraph issue #7417 reports long tool calls being dispatched again from a checkpoint while the original is still running: https://github.com/langchain-ai/langgraph/issues/7417

The state machine, key contract, SQL shape, safety defaults, and verification matrix above are original operational recommendations synthesized from those failure modes. Adapt transaction syntax and retention to the selected database, runtime, provider contract, and risk level.
