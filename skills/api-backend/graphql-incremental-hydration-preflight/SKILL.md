---
name: graphql-incremental-hydration-preflight
description: Use when a GraphQL @defer/@stream multipart response parses but a patch disappears after client, proxy, cache, or SSR hydration. Replay a pinned current ID-based or legacy path-based envelope offline, reject unknown shapes, and make a bounded rollout or recovery decision.
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [graphql, incremental-delivery, defer, stream, hydration, replay]
    related_skills: [rest-graphql-debug]
---

# GraphQL Incremental Hydration Preflight

## Overview

Use the raw HTTP response as the source of truth. The helper validates HTTP framing, multipart boundaries, strict JSON, a pinned envelope profile, patch targets, and the fully hydrated document. It performs no network access.

The key distinction is protocol profile:

- current ID-based: initial `pending[{id,path}]`; patches use `id` plus optional `subPath`; completion uses `completed[{id}]`;
- legacy path-based (`legacy-path-v0.1`): patches carry absolute `path`, may be folded into the initial part, and have no `pending`/`completed` IDs.

Mixing these profiles commonly makes a stream patch look valid while a legacy hydrator ignores its `items` or cannot resolve its location. Never auto-detect or coerce between profiles during incident replay.

## When to Use

- A nested `@stream` list or deferred object exists on the wire but is absent after hydration.
- A proxy, cache, SSR layer, or GraphQL client upgrade changed incremental response handling.
- The capture contains `pending` and `completed` IDs.
- You need a fail-closed rollout gate and an explicit recovery path.

Do not use this helper for live traffic replay, mutation execution, schema correctness, load testing, or an envelope that does not exactly match one of the two named profiles. Redact credentials, cookies, tokens, PII, and unrelated extensions before saving a fixture.

## Quick Reference

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/preflight.py \
  --profile current-id-v1 \
  tests/fixtures/response.http \
  tests/fixtures/expected.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Exit `0` means the pinned offline replay exactly matches the expected final data. Exit `1` means rollout is blocked. Argument errors exit `2`.

## Procedure

### 1. Freeze and redact the failing boundary

Capture the HTTP status line, response headers, and exact multipart bytes at the boundary immediately before the failing hydrator. Record producer, proxy, client/hydrator, and application versions separately. Preserve CRLF and boundary bytes; do not reconstruct them from parsed JSON.

Remove authorization, cookies, request variables, and sensitive response fields without changing envelope keys, IDs, paths, list shape, part order, or framing. Use an equivalent synthetic capture if redaction would alter those properties.

**Complete when:** one redacted byte capture names both capture boundary and component versions, and no secret or customer data remains.

### 2. Pin the profile before parsing

For `current-id-v1`, require:

- initial object-valued `data`, non-empty `pending`, and `hasNext: true`;
- unique non-empty pending IDs with paths that resolve in initial data;
- each incremental entry to reference a live ID and contain exactly one of object-valued `data` or array-valued `items`;
- optional `subPath` to resolve relative to the pending path;
- each completion to reference a live ID exactly once;
- no live IDs when terminal `hasNext: false` arrives;
- only allowlisted envelope keys. Standard non-semantic metadata belongs under `extensions`; an unknown top-level key is not silently ignored.

Pass `--profile current-id-v1` explicitly. A missing, misspelled, legacy, or future profile blocks replay rather than triggering format detection.

For a path-based V0.1 capture, pass `--profile legacy-path-v0.1`; this profile accepts `incremental` on the initial part and proves those folded patches are merged. It rejects ID lifecycle fields. Do not choose a profile by trial and error: identify the producer contract first.

**Complete when:** the selected profile is explicit in both command and report, and any profile mismatch exits nonzero without hydrated output.

### 3. Replay the ID lifecycle and hydration

The replay records each `pending` ID and its base path. A defer patch merges object fields at `base path + subPath`. A stream patch appends `items` to the list at `base path + subPath`. It then consumes `completed` IDs and verifies terminal closure.

Compare the result against a separately authored expected final data object. Do not derive expected JSON by running the same hydrator under investigation. A successful parse or `hasNext: false` alone does not prove hydration.

**Complete when:** patch count, pending IDs, completed IDs, final canonical digest, and exact expected-document match are recorded.

### 4. Localize the disappearance

Compare four artifacts in order:

1. raw multipart part JSON;
2. validated replay output;
3. hydrator/cache write immediately after each part;
4. post-hydration render or cache read.

If the offline replay blocks, treat the wire contract as invalid or unsupported. If replay passes but the application loses the list, the defect is downstream: inspect profile selection, ID lookup, relative `subPath`, `items` append semantics, normalization keys, cache writes, and SSR serialization. Do not “fix” a downstream loss by rewriting upstream payloads until this boundary comparison proves the rewrite is needed.

**Complete when:** the first boundary where expected data differs is identified with producer and consumer versions.

### 5. Make the rollout decision

Roll out only when all are true:

- the exact canary capture passes the pinned profile;
- the fully hydrated output exactly matches independently authored expected JSON;
- every pending ID completes once and no patch references an unknown/completed ID;
- unknown envelope keys are absent or deliberately standardized under reviewed `extensions` handling;
- the same captured bytes hydrate correctly through the canary client/proxy/SSR path;
- rollback artifacts and owners are ready.

Otherwise the decision is **BLOCK**. Never strip an unknown key and continue, auto-detect legacy versus current format, drop an `items` patch, or treat a terminal envelope as success while data is missing.

### 6. Roll out and recover safely

Canary one producer/proxy/client compatibility tuple at a time. Bound traffic and duration; compare nested-list cardinality and final-document digest with the control. Expand only with zero missing-patch, orphan-ID, duplicate-completion, or hydration-mismatch signals.

On any mismatch:

1. stop expansion and route affected traffic to the last known-good tuple;
2. disable incremental delivery for the affected operation only if the non-incremental path is pre-tested and semantically equivalent;
3. invalidate only cache/SSR artifacts proven to contain partial hydrated data;
4. replay retained redacted captures against old and candidate tuples;
5. reconcile user-visible partial results from the authoritative backend, not from the damaged cache;
6. resume with a new canary only after the pinned replay and end-to-end hydration both pass.

Do not globally disable GraphQL validation, discard unknown keys, flush all caches without scope, or retry non-idempotent operations merely because a response hydration failed.

## Fail-Closed Conditions

Block on malformed HTTP/chunking/multipart framing; duplicate JSON keys; BOM, invalid UTF-8, `NaN`, or infinity; unknown envelope or entry keys; GraphQL errors; profile mismatch; unresolved paths; duplicate/reused/unknown IDs; data/items ambiguity; non-list stream targets; patch conflicts; premature completion; live IDs at terminal closure; absent patches; or final-document mismatch.

`extensions` is retained as an allowed metadata container but is not interpreted. If extension semantics can change hydration, define a new reviewed replay profile rather than silently accepting them.

## Objective Verification

1. the fixture hydrates a nested streamed list and deferred object under `current-id-v1`;
2. completion order may differ from pending order but every ID closes exactly once;
3. an unknown top-level envelope key exits `1` and emits no merged document;
4. omitted or wrong `--profile` cannot replay;
5. a folded initial path-based payload passes only under `legacy-path-v0.1`, while cross-profile fields block rather than being coerced;
6. malformed framing, duplicate keys, non-finite numbers, GraphQL errors, unresolved/conflicting patches, and expected mismatch block;
7. chunked and identity-framed captures produce the same hydrated result;
8. tests and helper perform no network access.

## Evaluation Prompts

1. **Normal:** “We are rolling out GraphQL `@defer` through a proxy. The first multipart part may contain both `data` and `incremental`. Give an executable offline preflight that validates raw HTTP and proves the final merged data.”
2. **Difficult edge:** “A nested list patch disappears after hydration. The capture uses `pending`/`completed` IDs and an unknown extra envelope key. Give a fail-closed, profile-pinned replay and rollout/recovery decision.”
3. **Should not activate:** “My ordinary GraphQL JSON response has no `@defer`, `@stream`, `multipart/mixed`, or incremental payloads. Should I use this workflow?” Expected routing: no; use ordinary GraphQL response validation.

## Sources and Scope

The current ID-based shape follows GraphQL.js incremental execution interfaces and examples: pending results carry `id` and absolute `path`; incremental defer/stream results carry `id`, optional relative `subPath`, and `data` or `items`; subsequent envelopes may carry `completed`. GraphQL.js separately documents its legacy path-based format. Incremental delivery remains implementation-sensitive, so this helper intentionally names local replay profiles rather than claiming universal protocol negotiation.

- GraphQL.js current incremental result types (accessed 2026-08-12): https://github.com/graphql/graphql-js/blob/17.x.x/src/execution/incremental/IncrementalExecutor.ts
- GraphQL.js legacy/current comparison (accessed 2026-08-12): https://github.com/graphql/graphql-js/blob/17.x.x/src/execution/legacyIncremental/legacyExecuteIncrementally.ts
- GraphQL-over-HTTP incremental delivery RFC (accessed 2026-08-12): https://github.com/graphql/graphql-over-http/blob/main/rfcs/IncrementalDelivery.md
- Apollo Kotlin folded-initial field-loss report (accessed 2026-08-12): https://github.com/apollographql/apollo-kotlin/issues/6979
- GraphQL Yoga duplicate transfer-encoding report (accessed 2026-08-12): https://github.com/graphql-hive/graphql-yoga/issues/4412
- Relay nested-array hydration loss report (accessed 2026-08-12): https://github.com/facebook/relay/issues/5354
- GraphQL response specification (accessed 2026-08-12): https://spec.graphql.org/draft/#sec-Response

The strict allowlist, profile pin, offline replay, expected-document gate, rollout criteria, and recovery order are original operational recommendations, not claims from the GraphQL specification. No source prose, issue reproducer, or implementation code is copied into the helper or fixtures.
