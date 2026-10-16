# DynamoDB axioms: integration

Moved verbatim from SKILL.md so the entry file stays small. The numbering is unchanged, so "Integration #3" elsewhere means item 3 below. Data modeling, Mechanics, and Patterns citations refer to the sibling files in this folder.

## Integration

1. Ensure Streams consumers are idempotent or deduplicated by event identifier. DynamoDB Streams deliver at-least-once — handlers will see the same record twice after a Lambda timeout, a batch retry, or replay during an incident, and must produce the same outcome whether invoked once or many times.

   Two strategies are viable:
   - **Idempotent handler**: structure the operation so repeating it is a no-op. Conditional writes, set-based mutations (`ADD` to a set), and idempotency tokens on downstream APIs all qualify.
   - **Explicit dedupe**: record the `eventID` from the stream record in a dedupe store (a DynamoDB table with TTL is the usual choice) and skip records already present.

   Example (dedupe by `eventID`, TTL bounded to the redelivery window):

   ```python
   def handler(event, context):
       for record in event["Records"]:
           try:
               dedupe_table.put_item(
                   Item={"event_id": record["eventID"], "ttl": int(time.time()) + 86400},
                   ConditionExpression="attribute_not_exists(event_id)",
               )
           except ClientError as e:
               if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                   continue  # already processed
               raise
           process(record)
   ```

   Dedupe on `eventID`, not on application identifiers like `order_id` — the same aggregate legitimately produces many events, and keying on the business identifier will drop valid change records.

2. Use the transactional outbox pattern for reliable event publication. Write the state change and an outbox record in a single `TransactWriteItems` call; have a downstream consumer read the outbox via Streams and publish the event. This eliminates the "updated but did not emit" failure mode without resorting to two-phase commit.

3. Default the stream view to `NEW_AND_OLD_IMAGES`. Zero-ETL integrations with OpenSearch, most change-data-capture consumers, and any logic that depends on diffs all require both images.

4. Filter events at the source, not in the handler. Source-side filtering has **two mechanisms — mention both when diagnosing or proposing a fix**:

   - **Lambda Event Source Mapping `FilterCriteria`** — filters stream records *before* Lambda invocation. A handler that previously ran on 10M events/day but cares about 500k of them becomes a handler that runs 500k times, billed for 500k invocations instead of 10M. Filter shape (JSON pattern matching against the DynamoDB stream record): `{"dynamodb": {"NewImage": {"status": {"S": ["shipped", "delivered"]}}}}`.
   - **EventBridge Pipes filters** — the same source-side discarding, applied when the Pipe is the consumer. Use Pipes when the fan-out crosses multiple downstream targets (an event → Lambda + SQS + EventBridge bus), since the 2-concurrent-consumer limit on Streams (Data modeling #4) makes Pipes the common path for >2-consumer topologies.

   Both mechanisms eliminate invocation cost AND the work the handler would have done filtering. Inline filter logic inside the handler pays full invocation cost for every discarded event — a filter that drops 95% of traffic means 95% of invocations are pure waste. If the question is about source-side filtering, the answer names both mechanisms and routes the recommendation to the one that fits the consumer topology.

5. Treat Event Source Mapping configuration as a reliability surface. `BatchSize`, `MaximumBatchingWindowInSeconds`, `ParallelizationFactor`, `MaximumRetryAttempts`, `MaximumRecordAgeInSeconds`, `BisectBatchOnFunctionError`, and on-failure destinations together define delivery semantics. Several defaults are actively dangerous: `MaximumRetryAttempts` and `MaximumRecordAgeInSeconds` both default to `-1`, meaning a single unprocessable record will block its shard for the full 24-hour stream retention and then disappear silently. Bound retries, bound record age, and configure an on-failure destination so poison records are quarantined rather than stalling the shard or vanishing. Leaving any of these at defaults is a deliberate choice, not a neutral one.

6. Treat stream enablement as a durable interface commitment. Disabling a stream and re-enabling it produces a new stream ARN. Any Lambda Event Source Mapping or EventBridge Pipe bound to the old ARN becomes orphaned. Stream lifecycle is part of the table's public contract and should be managed accordingly.

7. Distinguish TTL-driven deletes from user-driven deletes. DynamoDB delivers TTL deletions through Streams with `userIdentity.principalId` set to `dynamodb.amazonaws.com`. Consumers should branch on this attribute to route TTL events separately — typically to archival or audit pipelines — rather than treating them as ordinary user deletes.

8. Match the analytical or search workload to the right target; do not reshape the operational table to serve either. DynamoDB is an OLTP store for *analytical* workloads, and the supported path to a read-optimized system is a managed integration, not a `Scan` and not a bespoke GSI. **Semantic similarity is the exception and stays in DynamoDB** (Fact #10). Route by workload type:

    - **Semantic similarity — "find similar", "more like this", RAG retrieval, recommendations, AI-agent memory, embedding-based anomaly detection** → a **vector index on the DynamoDB table itself**, queried with `SearchVectors`. No second datastore, no replication pipeline, no PITR prerequisite. This is the default for anything expressed as similarity over embeddings. See `${SKILL_DIR}/references/vector-search.md`.
    - **Full-text, keyword, typo-tolerant or fuzzy matching, faceting, aggregations, geospatial/radius search** → zero-ETL to Amazon OpenSearch Service. Initial load from a PITR snapshot, ongoing change capture via DynamoDB Streams, near real-time freshness (seconds). Requires PITR enabled on the source and Streams enabled with `NEW_AND_OLD_IMAGES`.
    - **SQL analytics, BI, materialized views, data sharing** → zero-ETL to Amazon Redshift. Initial load from a PITR export, ongoing change capture via incremental exports every 15–30 minutes. Requires PITR enabled on the source and KMS configured with an AWS-owned or customer-managed key (AWS-managed KMS is not supported).
    - **Open-format data lake, Apache Iceberg, multi-engine analytics (Athena, EMR, Spark, Redshift), or ML feature stores** → zero-ETL to Amazon SageMaker Lakehouse. Glue-orchestrated initial export plus incremental exports that write Iceberg tables to S3 or S3 Tables, typically 15–30 minutes fresh. Requires PITR enabled and a resource-based policy granting Glue the export actions.
    - **Point-in-time batch dump with custom downstream processing and no freshness requirement** → DynamoDB export to S3 (not branded zero-ETL, but the correct fallback when no zero-ETL target fits). Consumes no RCU.

    In every zero-ETL path above, PITR on the source table is a hard prerequisite — this does NOT apply to the vector-index path, which is not an integration. Do not approximate search with `begins_with` queries and bespoke GSIs. Do not scan the operational table for analytics. The integrations exist because these workloads compose with a column store, a search engine, or an Iceberg table and do not compose with a NoSQL key-value store.

    **Split a bundled ask; do not send it all to one place.** A request for "search" often bundles several kinds. Semantic similarity goes to a vector index; lexical, fuzzy and geo go to OpenSearch; SQL goes to Redshift. A workload legitimately needing both semantic and full-text search uses both a vector index and OpenSearch. Two directions are both wrong: routing semantic similarity out to OpenSearch by reflex, and routing typo-tolerant keyword or geo-radius search *into* a vector index. ANN over embeddings does no substring, prefix or edit-distance matching.

    When one operational table feeds BOTH the Redshift (SQL/BI) and SageMaker Lakehouse (Iceberg) paths, prefer a single DynamoDB→Lakehouse Iceberg export and have Redshift read the same Iceberg tables (Redshift Spectrum / native Iceberg support) rather than running two parallel zero-ETL integrations — this avoids a second incremental export and the duplicate per-GB charge with no loss of SQL/join capability. Use two separate integrations only when the consumers genuinely need divergent freshness or isolation.
