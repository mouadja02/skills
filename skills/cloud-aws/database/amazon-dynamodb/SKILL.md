---
license: Apache-2.0
source: https://github.com/aws/agent-toolkit-for-aws
attribution: "Amazon Web Services - agent-toolkit-for-aws (Apache-2.0)"
name: amazon-dynamodb
description: Designs, reviews, and debugs DynamoDB data layers from design axioms — enumerates access patterns, chooses partition/sort keys and GSIs, decides single-table vs. multi-table, configures Streams, Global Tables, TTL, vector indexes for similarity search, and zero-ETL integrations to OpenSearch/Redshift/SageMaker Lakehouse, and produces a defensible data-layer design with a monthly cost estimate and optional live validation. Applies whenever a user is designing, reviewing, or refactoring anything backed by DynamoDB — schemas, access patterns, GSIs, single- vs. multi-table choices, Streams consumers, transactional outboxes, Global Tables, zero-ETL pipelines, or storing embeddings and running semantic/vector similarity search with SearchVectors on items already in DynamoDB — even when they don't say "axioms" or "design review." Also applies when debugging hot partitions, throttling, unbounded Scans, LWW conflicts, or surprise bills on DynamoDB workloads.
version: 2
---

> **Attribution:** Sourced from [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws) (commit `44ba1a54`) by [Amazon Web Services](https://aws.amazon.com), licensed Apache-2.0. Modified for this collection: the design interview, numbered axioms, patterns, glossary, and the cost, live-validation, iteration, and best-practice sections were moved unchanged into `references/`.

# DynamoDB Axioms

This document is a set of design axioms for DynamoDB applications. It is intended to be read by an agent with no other context about the application and used to produce a defensible data-layer design.

## Guardrail — where this skill's own files live (MCP vs local install)

This skill can be loaded two ways, and they resolve the skill's own bundled
files from different places. Determine how the skill was loaded before reading
a reference or running a script:

- **Loaded through the AWS MCP `retrieve_skill` tool:** The skill is not
  installed on the local filesystem. You MUST fetch each reference or script
  via `retrieve_skill` with the `file` parameter (e.g.
  `file="references/vector-search.md"` or `file="scripts/calculate_costs.py"`), and
  run the script from the returned content. Do NOT `file_read` these paths
  locally — they do not exist on disk.
- **Installed locally** (e.g. `.kiro/skills/amazon-dynamodb/` or
  `~/.claude/skills/amazon-dynamodb/`): Read and run files from the local skill
  directory using relative paths.

This distinction applies only to the skill's own packaged files. User data and
session artifacts are always read from and written to the user's working
directory. Never fetch or write customer data through `retrieve_skill`.

Separately from where these files live: this skill calls real AWS APIs when it
validates a design, deploys a scratch table or benchmarks one. **The AWS MCP
server is recommended for those AWS interactions where it is available** — it
gives consistent credential handling and region resolution across hosts. It is
**not required**: every script here uses boto3 and the AWS CLI against the
ambient credential chain, so the skill works unchanged when no MCP server is
present.

The `${SKILL_DIR}` resolution below applies to the **locally installed** case: over
MCP there is no directory to resolve, and the scripts this skill ships cannot be
executed from a returned string — so a cost estimate or live validation requires
the locally installed form.

## Resolving the skill's own paths

This skill is host-agnostic — it runs under Claude Code, Kiro, Codex, Cursor, a plain terminal, or CI. Where it lives on disk depends on the host (`~/.claude/skills/…`, `~/.kiro/…`, `~/.codex/…`, `~/.cursor/…`, a repo checkout, anywhere). The agent's working directory is the **user's project**, not the skill bundle, so relative paths like `scripts/calculate_costs.py` will not resolve. Throughout this document, `${SKILL_DIR}` means **the absolute path of the directory that contains this SKILL.md file** (the skill root, which holds `scripts/` and `references/`).

**Resolve `${SKILL_DIR}` once per session, then reuse it.** Pick the first method that works in your host:

1. **You already know it.** You loaded SKILL.md from a path — `${SKILL_DIR}` is the directory that file is in. This is the most reliable source; prefer it.
2. **An environment variable.** If `$DDB_SKILL_DIR` is set, trust it.
3. **The bundled resolver** (host-neutral, no host assumptions). It searches the common install roots *and* verifies the hit against sentinel files, so it never returns the wrong directory silently:

   ```bash
   # If you already know the path to the script, just run it directly:
   #   SKILL_DIR="$(sh /path/to/amazon-dynamodb/scripts/find_skill_dir.sh)"
   # If you don't, this host-neutral one-liner searches the common roots
   # (~/.claude, ~/.kiro, ~/.codex, ~/.cursor, ~/.config, ~/.local/share, $PWD):
   SKILL_DIR="$(find "$HOME" "$PWD" -maxdepth 7 -type f -name SKILL.md -path '*amazon-dynamodb*' 2>/dev/null \
                | head -1 | xargs -I{} dirname {})"
   # Verify it before trusting it (sentinel check), then hand off to the resolver
   # for its loud-on-failure diagnostics:
   SKILL_DIR="$(sh "$SKILL_DIR/scripts/find_skill_dir.sh" 2>/dev/null || echo "$SKILL_DIR")"
   ```

   The resolver prints the verified skill root and exits 0, or prints nothing and exits non-zero with a fix-it message — so `SKILL_DIR="$(sh …/find_skill_dir.sh)"` is safe to trust when it succeeds. It is plain POSIX `sh`, so it behaves identically across hosts.

Once resolved, **export it so every later command is a clean substitution** and the scripts can also pick it up:

```bash
export DDB_SKILL_DIR="$SKILL_DIR"
python3 "$DDB_SKILL_DIR/scripts/calculate_costs.py" --model dynamodb_data_model.json --output cost_report.md
```

Internally the scripts locate their own siblings (other scripts, `scripts/benchmark_lambda.py`) relative to themselves, so you only ever need the **root** path — never each individual script path.

**Rules:**

- Always invoke scripts with an absolute path (the `$DDB_SKILL_DIR/…` form). Do **not** `cd` into the skill directory — the user's working directory must stay put so their artifacts (`dynamodb_data_model.json`, `cost_report.md`, …) land where they expect.
- If none of the three methods resolves the directory, **stop and ask the user where the skill is installed** rather than guessing. A wrong `${SKILL_DIR}` produces confusing "file not found" failures downstream; one clarifying question is cheaper.

## The pipeline at a glance

The skill is one tool per stage. **The default path touches no AWS: most work is stage 1 (a design you can discuss and refine conversationally).** Stage 2 (cost) runs on request or when the design is being finalized — not reflexively every turn. Stages 3–6 are a distinctly opt-in, heavyweight fork that creates real AWS resources and incurs a real bill; enter it only on explicit user agreement. Each stage's detailed contract is in the section named in the last column.

| # | Stage | Command (after `export DDB_SKILL_DIR=…`) | Reads | Writes | AWS? | Section |
|---|---|---|---|---|---|---|
| 1 | Design | *(no script — you produce the access-pattern list + schema)* | — | *(in-reply artifacts)* | no | *Artifacts to produce* |
| 2 | Cost | `python3 "$DDB_SKILL_DIR/scripts/calculate_costs.py" --model dynamodb_data_model.json --output cost_report.md` | `dynamodb_data_model.json` | `cost_report.md` | no | *Cost estimation* |
| 3 | Deploy | `python3 "$DDB_SKILL_DIR/scripts/deploy_model.py" --model dynamodb_data_model.json --config benchmark_config.json --manifest-out created_resources.json --yes-deploy` | model + config | `created_resources.json` | **yes** | *Live validation* |
| 4 | Benchmark | `python3 "$DDB_SKILL_DIR/scripts/benchmark_model.py" --model dynamodb_data_model.json --config benchmark_config.json --manifest created_resources.json --raw-out perf_raw.jsonl --summary-out perf_summary.json` | model + config + manifest | `perf_raw.jsonl`, `perf_summary.json` | **yes** | *Live validation* |
| 5 | Report | `python3 "$DDB_SKILL_DIR/scripts/generate_perf_report.py" --model dynamodb_data_model.json --summary perf_summary.json --output performance_report.md` | model + summary | `performance_report.md`, `design_findings.json` | no | *Live validation* |
| 6 | Teardown | `python3 "$DDB_SKILL_DIR/scripts/generate_teardown.py" --manifest created_resources.json --out teardown.sh` → review → `bash teardown.sh --confirm` | manifest | `teardown.sh` | **yes** (on `--confirm`) | *Live validation* step 6 |
| — | Iterate | `python3 "$DDB_SKILL_DIR/scripts/iterate_design.py" …` (wraps 3→4→5→cost as one human-driven round) | model + config + loop-state + manifest | `loop_state.json` + the above | **yes** (gated) | *Iterative design loop* |

**Who reads what.** *You (the agent)* read the compact artifacts: `cost_report.md`, `design_findings.json`, `loop_state.json`. *The user* reads `performance_report.md`. Never read `perf_raw.jsonl` (large) — it only feeds stage 5.

**Consent gates.** Stage 3+ needs `--yes-deploy`; the benchmark refuses to spend over `cost_guardrail_usd` without `--allow-spend`; teardown needs the user's attested review **and** intent before you run `bash teardown.sh --confirm`. Details in *Live validation*.

**AWS access (MCP recommended, not required).** Stages 3–6 talk to AWS (create tables, a Lambda, an IAM role, then benchmark and tear down). For the best experience with AWS API calls the **AWS MCP server is recommended but not required** — every script here uses `boto3` directly and runs from a plain shell with standard AWS credentials (a profile, SSO, or environment credentials), so the skill works identically with or without the MCP server. Nothing in this skill assumes MCP-specific tools.

## How to use these axioms

1. **Read the reference architecture first** when the task is to design, review, or critique a full-app data layer (multi-entity schemas, multi-table layouts, end-to-end composition with streams/search/notifications). `${SKILL_DIR}/references/reference-architecture.md` is a complete multi-tenant kanban task-board ("TaskBoard") SaaS on AWS backed by DynamoDB, with all of the surrounding pieces (Cognito, CloudFront, HTTP API, Lambdas, Streams, OpenSearch, AppSync Events, SQS/EventBridge, cascades, idempotency middleware) worked out and justified. The axioms tell you *what* must be true; the reference shows *how* these pieces fit together in practice. Not reading it on a multi-table design means you will miss patterns that are in the reference but hard to re-derive from axioms alone — idempotency middleware, phantom-upsert guards, AppSync channel authorization, the Notifications-as-EventBridge-not-table decision, cascade-delete via chunked `BatchWriteItem`. Skip this step only for small-scope questions — a single-table question, a query-cost calculation, a pointed debugging question.
2. Produce the **access-pattern list** (next section) before applying any axiom below. Every modeling axiom assumes this list exists; an axiom that asks "is this pattern frequent?" or "what does this query return?" cannot be applied without it.
3. Produce the **artifacts** listed under *Artifacts to produce*. These are the outputs of a design, not intermediate notes. The axioms shape the artifacts; the artifacts are what the agent hands back.
4. Apply the **Patterns** section alongside the axioms. Patterns are not axioms — they are load-bearing implementation details that the reference made concrete, and that a design will need even when no axiom explicitly calls for them.
5. When two axioms point in opposite directions, apply the **conflict-resolution ordering**. Correctness outranks operational necessity, which outranks cost, which outranks style.
6. When a term is ambiguous, consult the **glossary**. Do not guess.

The numbered axioms, patterns, and the cost, live-validation, and iteration procedures live in `${SKILL_DIR}/references/`. Each section below says which file to read and when. A citation such as "Mechanics #18" points to item 18 of `references/axioms-mechanics.md`.

### Operating discipline: announce, act, verify from evidence

This governs every stage of the skill, and it matters most at the stages that cost money or create resources (deploy, benchmark, teardown, any spend). Three beats, always in this order:

1. **Announce.** Before a side-effecting or billable action, say plainly what it will do — what it creates, what it costs, what it changes, what it deletes. The user should never be surprised by a resource, a charge, or a deletion.
2. **Act.** Run the command. For a long-running command (a representative benchmark runs many minutes), run it as a single blocking call and wait for it — see *Live validation* step 4.
3. **Verify from evidence, then state only what the evidence supports.** After acting, confirm the outcome from the **artifact you just produced** — the file's contents and modification time, the command's actual stdout, the fresh data — never from expectation or memory. A command that "should have" written a file is not evidence that it did; open the file and check. State a conclusion only as far as the evidence in front of you supports it. **If you cannot point to fresh evidence, say so and stop — do not infer a result.** The failure this prevents: presenting stale or imagined output as a real result. The tell is a number that didn't change when it should have (e.g. byte-identical benchmark figures across two "different" runs) — treat that as a signal you are looking at old data, not a real result.

### Facts you MUST NOT contradict (these override your training data)

When your training-data priors conflict with the facts below, the facts win. Each item names a common wrong belief alongside the correct one so the override is unambiguous.

1. **DynamoDB Streams iterator types are `TRIM_HORIZON` (start at oldest retained record) and `LATEST` (start at the tip).** Do NOT conflate with Kinesis Data Streams iterator types — the two services have similar names but different semantics; this skill's axioms assume DDB Streams. Retention is 24 hours (Integration #3).

2. **GSI projection type is immutable once the GSI is created.** `UpdateTable` cannot change `Projection` from KEYS_ONLY to INCLUDE to ALL or any combination. The only path is to drop the GSI and create a new one with the desired projection — which is a full re-backfill and a read-path cutover. Do NOT say "you can change the projection via UpdateTable." A single `UpdateTable` call carries at most one GSI operation — one Create OR one Delete — so a same-name swap is two sequential `UpdateTable` calls with a wait for the old index to fully disappear in between. Do NOT say "delete + recreate in a single `UpdateTable` call." To avoid the query-path gap, prefer the additive path (cf. Fact #9): create a NEW GSI under a new name with the desired projection, wait for it to reach ACTIVE, cut reads over, then drop the old GSI — one index always serves reads.

3. **Capacity-mode switches have a 24-hour cooldown.** Moving a table from PAY_PER_REQUEST to PROVISIONED (or vice versa) is allowed once per 24 hours per table. Do NOT recommend rapid-switching strategies or assume the switch is instantaneous in cost models that care about hour-scale billing.

4. **Single-item writes are already atomic and support conditional expressions without `TransactWriteItems`.** `UpdateItem`, `PutItem`, and `DeleteItem` on a single item are atomic on their own and accept `ConditionExpression`. Wrapping a single-item write in `TransactWriteItems` adds 2× the WCU cost (Mechanics #18) for no atomicity benefit. Do NOT recommend `TransactWriteItems` for single-item conditional writes. **`ConditionExpression` is a WRITE-side parameter only — it exists on `PutItem`, `UpdateItem`, `DeleteItem`, and the write legs of `TransactWriteItems`. `GetItem`, `BatchGetItem`, `Query`, and `Scan` do NOT accept `ConditionExpression` — there is no conditional read in DynamoDB, and `ConditionalCheckFailedException` is a write-only error.** Do NOT describe `GetItem` as "returning the item only if a condition passes" or as throwing `ConditionalCheckFailedException` — no such behavior exists. A read returns the item to anyone who supplies the key; the only read-side filter is `FilterExpression` (Query/Scan only — applied after the items are read and billed, never on `GetItem`), and even that does not authorize, it only narrows the result a caller already paid to read. The correct way to keep a caller from reading another tenant's item is to make the data unaddressable to them — partition-key the table on the authorization identifier (Data modeling #14) so a foreign key simply isn't in a partition the caller can reach — NOT to bolt a "conditional GetItem" on top.

5. **Maximum item size is 400 KB, hard cap.** The 1 MB limit is the `Query`/`Scan` response-page cap, not an item cap. Do NOT quote 1 MB as the item limit. Items near 400 KB also cost more per write (WRU = 1 per 1 KB rounded up, Mechanics #18), so large items are expensive even before the cap bites.

6. **`BatchGetItem` and `BatchWriteItem` are NOT atomic.** Partial failures are normal and returned via `UnprocessedKeys` (BatchGetItem) or `UnprocessedItems` (BatchWriteItem). The client must retry the unprocessed portion with exponential backoff. Do NOT describe batch operations as atomic or all-or-nothing — use `TransactWriteItems` when atomicity across multiple items is required (subject to Mechanics #14 bounds).

7. **Reserved Capacity applies to PROVISIONED capacity only, not to on-demand (PAY_PER_REQUEST).** Do NOT recommend Reserved Capacity for on-demand tables — there is no such product. On-demand savings come from usage-based discounts or table-class selection (Standard vs Standard-IA), not reservations.

8. **A failed `ConditionExpression` still consumes write capacity.** `ConditionalCheckFailedException` charges the same WCU as a successful write of the same shape. Do NOT claim that failed conditional writes are free or that the condition check happens "before" the write-cost is assessed. Plan cost models around expected failure rates (Mechanics #18 uses `conditional_fail_rate` for this reason).

9. **A GSI's key schema (partition key / sort key) is immutable once the GSI is created.** `UpdateTable` can add a new GSI or drop an existing one, but it cannot alter the KeySchema of an existing GSI. Re-keying an index — including write-sharding a hot GSI partition key by adding a hash suffix — is therefore an **additive migration**, not a code-only change: create a new GSI with the new key → let it populate → cut reads over → drop the old GSI. A *historical* backfill is needed only when the new index must cover items that were already written and won't be touched again; a sparse or small in-flight index (e.g. one holding only active orders) populates from ongoing writes alone and needs no backfill. Do NOT describe a GSI key change as "just a code change" or "no schema migration."

10. **DynamoDB has native vector search. Semantic similarity does NOT require a second datastore.** A **vector index** is a third index type alongside GSIs and LSIs: declare it with the `VectorIndexes` parameter on `CreateTable` or the `VectorIndexUpdates` parameter on `UpdateTable`, store embeddings as a list of numbers on your items, and query it with the **`SearchVectors`** API (approximate nearest neighbour). Do NOT say DynamoDB cannot do vector or similarity search, and do NOT route a semantic-search requirement to OpenSearch, pgvector, or S3 Vectors by default — the vectors live on the same items as the operational data, with no replication pipeline (Integration #8 routes the workload types). `Query`, `Scan`, PartiQL and DAX do **not** work against a vector index; `Query` is rejected with `ValidationException: Query operation not supported on this index type.` A vector index is NOT a GSI and is NOT configured through one — there is no `VectorIndexConfig` and no vector block on a secondary index. Vector indexes require **on-demand capacity** (Mechanics #19).

    **DynamoDB does NOT recompute embeddings, and the index cannot fix a stale one.** The vector is ordinary item data: DynamoDB indexes the numbers you wrote and nothing more. Edit the source text and the stored embedding still describes the *old* text, so it keeps matching the old meaning — indefinitely, with no error and no staleness signal anywhere. This is **not** index-propagation lag, and vector-index write propagation does not "close the window": no amount of waiting regenerates a vector. Whenever content behind an embedding is mutable, say so explicitly and give the fix — detect the content change and re-embed with the *same* model, then write the new vector back (DynamoDB Streams into a re-embedding consumer is the usual shape; synchronous regeneration in the write path is also fine). Never imply the index refreshes vectors on its own.

    **`Dimensions`, `DistanceFunction`, `Projection` and `SearchSchema` are ALL immutable** — every one of them is fixed at `CreateTable`, not just the projection. Changing any single one means creating a replacement index and migrating; there is no in-place `UpdateTable` for them (Mechanics #7).

    **A stale SDK is not evidence the feature is missing.** The operations ship in **botocore/boto3 ≥ 1.43.64** and **AWS CLI v2 ≥ 2.36.16**. Below those versions they are absent from the client entirely — `aws dynamodb search-vectors` fails with `Found invalid choice` and `hasattr(client, "search_vectors")` is `False`. Testing for that `hasattr` is better than comparing version strings: it checks the capability directly and cannot go stale. If it is absent, tell the user to upgrade; do NOT conclude the feature does not exist. Full API surface, sharp edges and troubleshooting: `${SKILL_DIR}/references/vector-search.md`.

    **Quoted service limits are a design envelope, not a fact to argue with.** The per-table index count, maximum dimensions, `TopK` range and inline-filter count quoted in this skill are subject to change, and quotas of this kind generally rise. Design inside them, but before telling a user their design exceeds a limit, confirm the current value in AWS Service Quotas or the DynamoDB developer guide — a raised quota that this skill has not caught up with should not become a wrongly rejected design.

These ten facts are not the full axiom set — they are the subset where LLM prior is most likely to be wrong. When a user's question intersects one of them, state the correct fact plainly and move on; do not hedge with "I think" or "typically."

## The access-pattern list

Before touching a schema, enumerate every pattern the application must serve. For each pattern record:

- A one-line description of what the caller is asking for.
- Expected RPS (treat "unknown" as a design gap to close, per Mechanics #2).
- Items returned per call and approximate item size in KB.
- Consistency requirement (strong, eventual, or transactional).
- Authorization scope — the identifier that must be verified before the call is permitted (per Data modeling #14).

The list is a numbered, ranked table. The rest of this document assumes it exists. Any modeling decision that cannot be traced back to an entry on this list is unjustified.

## Per-entity operational-config inputs

> **This interview is required before proposing any table boundary.** Ask it first; do not design and then backfill assumptions.

Per entity (or per aggregate), ask about backup and recovery granularity, Streams consumers, capacity mode, TTL, and encryption and IAM scope. Missing answers are gaps to close, not defaults to guess. The exact questions and how each answer drives table splitting are in `${SKILL_DIR}/references/design-interview.md`.

## Per-entity attribute walkthrough (drives item size)

Item size is the second-largest cost driver after RPS. Walk each entity's attribute list with the user, estimate bytes per attribute, label guesses as assumptions, and **always show the per-entity table** (`attribute | type | bytes | source`) in your reply. The byte heuristics and calibration examples are in `${SKILL_DIR}/references/design-interview.md`.

## Artifacts to produce

> **Produce artifacts in the order listed below.** Schema + per-pattern plan are the primary outputs; cost estimate (item 7) and live validation (item 8) come **after** the design exists, not instead of it. A response that leads with a cost analysis and buries the schema in an appendix has the dependency backwards — the user asked for a design, and the cost is a property *of* the design. The access-pattern list (item 1), schema (item 2), and per-pattern plan (item 3) must be visible and discussable in the reply **before** any cost numbers appear. Items 1–6 are the no-AWS design itself and are the default deliverable; item 7 (cost) is produced on request or at finalization (see *Cost estimation*); item 8 (live validation) is the opt-in AWS fork. Putting these artifacts only in `dynamodb_data_model.json` does not satisfy this — the user reads your prose, not the JSON. ❌ BAD reply shape (a real failure mode): a reply that opens "## Summary for the CFO — $1,019/month" with the schema living only in `dynamodb_data_model.json` on disk and the reply's only design content a trailing "artifacts produced" file list. ✅ GOOD: access-pattern list + per-table schema + per-pattern plan + per-entity byte table (per *Per-entity attribute walkthrough* step 6) rendered in the reply, **then** the cost summary, **then** "`cost_report.md` written."

A complete design hands back:

1. **The access-pattern list** as above.
2. **A schema per table**: primary key (named per Data modeling #7), GSIs with their key attributes and projection type, and the operational configuration (Streams, PITR, TTL, capacity mode, Global Tables replication, encryption, IAM scope — all per Data modeling #3).
3. **A per-pattern plan**: for each access pattern in the list, the exact API call (`GetItem`, `Query`, or `BatchGetItem`, per Mechanics #16), the table or GSI it targets, the key conditions, the filter expressions if any, and the projected cost using the formulas in Mechanics #18.
4. **A fan-out topology**: for each table with Streams enabled, the consumers (Lambda, EventBridge Pipe, Kinesis shim), the filters at the source (Integration #4), and the on-failure destinations and retry bounds (Integration #5).
5. **A list of deviations and their justification**: any axiom or pattern not applied, with a stated reason.
6. **Idempotency and conditional-write guards**: which routes use idempotency-key middleware (Patterns #1), which `UpdateItem`s carry `attribute_exists` guards against phantom upserts (Patterns #2), and which `PutItem`s carry `attribute_not_exists` guards against double-creation.
7. **A monthly cost estimate** — produced **on request or at finalization**, not reflexively on every design turn. While the user is still exploring or refining the model, stay in design discussion and don't run the calculator each turn. Produce the estimate (via `${SKILL_DIR}/scripts/calculate_costs.py` — see *Cost estimation* below) when the user asks what it costs, or when the design is being settled (they signal they're committing to it / taking it to review / want the numbers). When you do produce it, use the calculator — never inline arithmetic. Skip entirely for questions too narrow to have produced a full design (a single-query sizing, a debugging thread, a pointed mechanics question).

8. **A live validation** (optional, on offer, last step): after the cost estimate, ask the user whether they want to deploy this schema to an AWS account they nominate and measure real per-operation capacity, latency, and GSI amplification against live DynamoDB. If yes, follow *Live validation* below. Skip for narrow questions, when the cost estimate was skipped, or when the user has no sandbox account. Unlike the cost estimate, this step creates real resources and incurs real charges, so both the offer and the consent must be explicit.

## Conflict-resolution ordering

When axioms point in opposite directions, apply in this priority order:

1. **Correctness** — authorization boundary alignment (Data modeling #14), consistency requirements, transactional atomicity, idempotency. A design that leaks data across tenants or serves stale data where strong consistency is required is wrong regardless of its other merits.
2. **Operational necessity** — divergent PITR, Streams, capacity, or replication configuration (Data modeling #3), recovery granularity (Data modeling #5), per-partition throughput ceilings (Mechanics #3), transaction bounds (Mechanics #14). These are physical or service constraints; preference does not override them.
3. **Cost and performance** — access-pattern co-location (Data modeling #1), dedicated GSIs (Data modeling #6), projection choice (Mechanics #7), cost formulas (Mechanics #18), capacity mode (Mechanics #19).
4. **Style and convention** — naming (Data modeling #7), single-table vs. multi-table framing (Data modeling #11) absent other signal. The cheapest to override when a higher-tier axiom disagrees.

Two concrete examples:

- Data modeling #1 (co-locate by shared access) vs. Data modeling #14 (partition by authorization boundary): #14 wins. If the natural access key and the authorization key differ, key on the authorization identifier and expose the alternate access via a GSI.
- Data modeling #1 (co-locate) vs. Data modeling #3 (split on divergent operational config): #3 wins. Two entities sharing a read pattern but requiring different PITR retention or Streams consumers belong in separate tables.

## Glossary

Definitions of access pattern, aggregate, item collection, and the other terms the axioms use are in `${SKILL_DIR}/references/glossary.md`. Consult it when a term is ambiguous; do not guess.

## Data modeling

The numbered data-modeling axioms (co-location by shared access pattern, table count as an output, GSIs versus overloaded keys, the vector-index budget, single-table design as a tactic, Global Tables conflict handling, partition keys aligned with the authorization boundary, and the rest) are in `${SKILL_DIR}/references/axioms-data-modeling.md`. Read it before proposing any table, key, or index. When text cites "Data modeling #N", it means item N there.

## Integration

The integration axioms (idempotent Streams consumers, the transactional outbox, stream view types, source-side event filtering, event source mappings, TTL-driven versus user deletes, and routing search and analytics to a vector index or a zero-ETL target) are in `${SKILL_DIR}/references/axioms-integration.md`. Read it whenever a design uses Streams or TTL deletes, or needs search or analytics. "Integration #N" means item N there.

## Mechanics

Aggregate tightness, RPS per pattern, partition and GSI throughput, projections (a hard, immutable boundary on vector indexes), transactions, capacity modes (on-demand is mandatory with a vector index), and the capacity-unit math (Mechanics #18) are in `${SKILL_DIR}/references/axioms-mechanics.md`. Read it for any sizing, hot-partition, throttling, or cost question. "Mechanics #N" means item N there.

## Patterns

Load-bearing implementation patterns (idempotency-key middleware, conditional-write guards against phantom upserts, cascade deletes, and others) are in `${SKILL_DIR}/references/axioms-patterns.md`. Apply them alongside the axioms on any full design. "Patterns #N" means item N there.

## Cost estimation

Produce a monthly estimate only when the user asks what it costs or the design is being finalized, never reflexively, and skip it when no full design exists. The model file format (vector indexes included, as `vector_indexes` plus a `SearchVectors` access pattern), calculator usage, and how to present the report are in `${SKILL_DIR}/references/cost-estimation.md`.

## Live validation

After a cost estimate you may offer, in one line, to deploy the design to an AWS account the user nominates and benchmark it. It creates real resources and a real bill, so run it only on explicit agreement. **Read `${SKILL_DIR}/references/live-validation.md` in full before making the offer.** It holds the safety statements you must state verbatim, the deploy, benchmark, report, and teardown steps, and their consent gates.

## Iterative design loop

`${SKILL_DIR}/scripts/iterate_design.py` runs one human-driven round (apply an agreed change, deploy or reuse, benchmark, report, suggest, stop). It is AWS-gated like live validation; read `${SKILL_DIR}/references/iterative-design-loop.md` before the first round.

## Security considerations

Security is woven through the axioms above (authorization-aligned keys in Data modeling #14, conditional-write guards in Patterns #2, transactional uniqueness in Mechanics #13). This section consolidates the risks an agent following this skill MUST surface to the user regardless of which axiom is in play, plus the controls specific to the skill's executable scripts. State the relevant ones in any design review; do not assume the user already knows them.

1. **Authorization-boundary alignment (IDOR) is the first security check.** The most common DynamoDB data-exposure bug is a partition key set to a client-supplied identifier (a `review_id`/`order_id` from a URL) instead of the server-derived authorization identifier (`user_id`, `tenant_id`, `account_id`). When they diverge, a caller can pass a foreign key and reach data across the tenancy boundary. Align the partition key with the authorization/tenancy boundary (Data modeling #14) so a foreign key is simply unaddressable; a per-call `ConditionExpression` is discipline, not a structural fix, and does not cover reads (Fact #4). On any design review, evaluate and state this **before** hot-partition, projection, or cost findings.

2. **Encryption at rest — always on; choose the key tier deliberately.** DynamoDB encrypts every table at rest with no way to turn it off. The default is an **AWS-owned key** — no cost, no key management, and the implicit state when no `SSESpecification` is set (which is what the live-validation deploy does; the bench manifest records the at-rest state read back from `DescribeTable`). It is right for ephemeral/bench tables and most workloads. For data under a compliance regime (audit of key usage, independent key rotation/revocation, cross-account key policy, or a regulatory requirement to hold the key), recommend a **customer-managed KMS key (CMK)** — set `SSESpecification` with `SSEType: KMS` and a `KMSMasterKeyId` (note: DynamoDB's only non-default `SSEType` is `KMS`; there is no `AES256` type on DynamoDB), and note the per-request KMS cost and the need for a key policy. Surface the encryption choice in the design (it is one of the per-entity operational-config inputs) rather than leaving it implicit. **Encryption in transit** is always on for every AWS API call these scripts make: boto3 talks to DynamoDB/Lambda/IAM over TLS (HTTPS) by default and there is no plaintext path — agents replicating this pattern should treat all data-in-transit as protected and never disable TLS verification.

3. **Generated artifacts are sensitive — treat them accordingly.** The deploy writes `created_resources.json`, a manifest that contains the AWS **account ID, resource ARNs, and the profile name** used. It is not a secret store (it holds no credentials), but it identifies the account and resources, so do not paste it into a shared channel, commit it to a public repo, or include it verbatim in a report. The skill's scripts never write AWS credentials, tokens, or connection strings to any artifact — keep it that way; if you extend them, do not log credential material.

4. **Benchmark resources go only in a sandbox/test account.** The live-validation deploy creates real, billable resources. It must run only against a sandbox/testing account the user names — never production, never an account holding real user data. The deploy refuses on prod-marker account aliases/ARNs (`prod`/`production`/`prd`/`live`), but the agent is responsible for stating the four live-validation facts and confirming the account's purpose first (see *Live validation*).

5. **Credential hygiene.** Never persist AWS profiles, access keys, session tokens, or `credential_process` blobs into any file the skill generates, and never echo them to output. The scripts authenticate from the ambient AWS credential chain (a named profile, SSO, or environment credentials); they neither read arbitrary environment variables wholesale nor record what they resolved. When you write `benchmark_config.json`, store only the profile *name* and region — not the resolved credentials behind them.

6. **Vector search does not honour fine-grained access control, and a vector index partition key is not a tenant boundary.** Two distinct hazards, both of which MUST be surfaced on any multi-tenant design that includes semantic search — followed by the compensating detective control they require.

    First, the `dynamodb:` FGAC condition keys — `dynamodb:LeadingKeys`, `dynamodb:Attributes`, `dynamodb:Select` — are absent from the `SearchVectors` request context. A statement whose `Condition` references one therefore does not match, and the outcome is denial rather than a grant. Adding `dynamodb:SearchVectors` to an existing FGAC-conditioned statement silently breaks vector search while that statement's other actions keep working normally, which presents as a broken index rather than a policy fault. Grant `dynamodb:SearchVectors` in its **own** statement, scoped to the index resource ARN (`arn:aws:dynamodb:<region>:<account-id>:table/<table>/index/<index>`), with no `dynamodb:` FGAC conditions attached.

    Second, scoping searches to one tenant's partition-key value is a data-locality and performance optimization, **not** an access-control mechanism. Any principal holding `dynamodb:SearchVectors` on the index can search any partition-key value, and because the FGAC condition keys do not apply you cannot constrain which values they reach at the IAM layer. Where strict tenant isolation at the data layer is required, use separate tables or separate indexes with distinct per-tenant IAM grants; an application layer that injects the caller's tenant identifier and never accepts it from the client is a complement, not a substitute. This is the vector-search form of the authorization-boundary check in item 1 — and unlike the base table, the key schema does **not** make foreign data unaddressable here, so the structural fix is grant separation rather than partitioning. Encryption at rest is inherited from the base table; there is no separate setting for a vector index.

    Third, because grant separation constrains which *index* a principal may search but never which partition-key values, recommend **CloudTrail data-event logging** on any multi-tenant vector-indexed table as the compensating detective control. It is the only record of which value each principal searched — the precise dimension IAM cannot gate — so a cross-tenant search from a compromised principal or a failed application-layer injection is otherwise unobservable. A CloudWatch alarm on per-principal `VectorSearchRequestBytes` catches partition enumeration as a volume anomaly. Note also that the embeddings are themselves sensitive: similarity results disclose that two records are semantically close even when no raw text is returned, so the vector attribute's exclusion from results by default is a security default worth keeping, and anything logging whole items needs the same care as the table. Full treatment: `${SKILL_DIR}/references/vector-search.md § Security`.

## Best practices

Operational defaults to enable unless the artifacts justify otherwise, starting with deletion protection on every table, are in `${SKILL_DIR}/references/best-practices.md`. Check a design against it before handing it back.

## Reference architectures

Worked examples that apply these axioms end-to-end to a concrete application. Consult when a design question is easier to answer against a running model than against the axioms alone.

- `${SKILL_DIR}/references/reference-architecture.md` — a multi-tenant kanban task-board ("TaskBoard") SaaS on AWS backed by DynamoDB. Covers the access-pattern list, table and GSI layout, Streams fan-out to OpenSearch and EventBridge, authorization-aligned partitioning, real-time delivery, and the trade-offs made at each step. Start here when a user asks about a full-stack DynamoDB design, multi-tenancy, or end-to-end composition of the services around the database.
- `${SKILL_DIR}/references/vector-search.md` — the vector index API surface (`VectorIndexes`, `VectorIndexUpdates`, `SearchVectors`), SearchSchema design, distance functions and score direction, the readiness predicate, projection and immutability rules, silent de-indexing, IAM including the fine-grained-access-control gap, the byte-based cost dimensions, and a troubleshooting table keyed on the service's verbatim error strings. Read this whenever a design or debugging thread involves semantic similarity, RAG retrieval, recommendations, or AI-agent memory (Fact #10, Integration #8). Skip it otherwise.
- `${SKILL_DIR}/references/cost-model-schema.md` — the JSON shape consumed by `${SKILL_DIR}/scripts/calculate_costs.py`. Read this the first time you produce a monthly cost estimate (see *Cost estimation* above). Skip it for non-cost questions.
- `${SKILL_DIR}/references/performance-model-schema.md` — the JSON shape of `benchmark_config.json` consumed by the live-validation scripts. Read this the first time you run a live validation (see *Live validation* above). Skip it when live validation is not on the table.
- `${SKILL_DIR}/references/performance-report-format.md` — the structure of `performance_report.md` generated by `${SKILL_DIR}/scripts/generate_perf_report.py`. Read this before interpreting the report or drafting the design-reflection section.
- `${SKILL_DIR}/references/loop-state-schema.md` — the shape of `loop_state.json`, the compact per-round genealogy file written by `${SKILL_DIR}/scripts/iterate_design.py`. Read this when running the iterative design loop (see *Iterative design loop* above).
