---
name: indexing-performance-optimization
description: "Use when diagnosing slow Qdrant ingestion, delayed optimizer completion, long HNSW builds, or payload-index construction."
version: "1.0.0"
license: Apache-2.0
source: "https://github.com/qdrant/skills"
attribution: "qdrant/skills by Qdrant"
---

> **Attribution:** Sourced from [qdrant/skills](https://github.com/qdrant/skills) by [Qdrant](https://qdrant.tech).

## When to Use

- Upload/upsert throughput is below target.
- Optimizer work or HNSW construction does not finish in the expected window.
- Payload-index creation dominates an ingestion or migration window.

Do not use this skill when ingestion is healthy and only query latency or memory footprint is problematic. Use the sibling search or memory skill instead.

## Prerequisites and Quick Reference

- Record Qdrant version, point/vector sizes, batch size, client concurrency, shard count, collection configuration, optimizer status, and CPU/disk/network utilization.
- Keep a tested rollback configuration and a representative non-production collection.
- Classify first: **client/network**, **server ingestion**, **optimizer backlog**, **HNSW build**, or **payload-index build**.
- Measure points/second, request errors, optimizer completion time, resource saturation, and post-build search quality.

The Qdrant links below are sourced facts and upstream guidance. The isolation order, rollback discipline, and acceptance checks are repository recommendations.

# What to Do When Qdrant Indexing Is Too Slow

Qdrant does NOT build HNSW indexes immediately. Small segments use brute-force until they exceed `indexing_threshold_kb` (default: 20 MB). Search during this window is slower by design, not a bug.

- Understand the indexing optimizer [Indexing optimizer](https://qdrant.tech/documentation/ops-optimization/optimizer/?s=indexing-optimizer)


## Uploads/Ingestion Too Slow

Use when: upload or upsert API calls are slow.
Identify bottleneck: client-side (network, batching) vs server-side (CPU, disk I/O)

For client-side, optimize batching and parallelism:

- Use batch upserts (64-256 points per request) [Points API](https://qdrant.tech/documentation/manage-data/points/?s=upload-points)
- Use 2-4 parallel upload streams

For server-side, optimize Qdrant configuration and indexing strategy:

- Create more shards (3-12), each shard has an independent update worker [Sharding](https://qdrant.tech/documentation/scaling/distributed_deployment/?s=sharding)
- Create payload indexes before HNSW builds (needed for filterable vector index) [Payload index](https://qdrant.tech/documentation/manage-data/indexing/?s=payload-index)

Suitable for initial bulk load of large datasets:

- Disable HNSW during bulk load (set `indexing_threshold_kb` very high, restore after) [Collection params](https://qdrant.tech/documentation/concepts/collections/?s=update-collection-parameters)
- Setting `m=0` to disable HNSW is legacy, use high `indexing_threshold_kb` instead

Careful, fast unindexed upload might temporarily use more RAM and degrade search performance until optimizer catches up.

See https://qdrant.tech/documentation/manage-data/bulk-upload/


## Optimizer Stuck or Taking Too Long

Use when: optimizer running for hours, not finishing.

- Check actual progress via optimizations endpoint (v1.17+) [Optimization monitoring](https://qdrant.tech/documentation/ops-optimization/optimizer/?s=optimization-monitoring)
- Large merges and HNSW rebuilds legitimately take hours on big datasets
- Check CPU and disk I/O (HNSW is CPU-bound, merging is I/O-bound, HDD is not viable)
- If `optimizer_status` shows an error, check logs for disk full or corrupted segments


## HNSW Build Time Too High

Use when: HNSW index build dominates total indexing time.

- Reduce `m` (default 16, good for most cases, 32+ rarely needed) [HNSW params](https://qdrant.tech/documentation/manage-data/indexing/?s=vector-index)
- Reduce `ef_construct` (100-200 sufficient) [HNSW config](https://qdrant.tech/documentation/concepts/collections/?s=indexing-vectors-in-hnsw)
- Keep `max_indexing_threads` proportional to CPU cores [Configuration](https://qdrant.tech/documentation/ops-configuration/configuration/)
- Use GPU for indexing [GPU indexing](https://qdrant.tech/documentation/ops-configuration/running-with-gpu/)

## HNSW index for multi-tenant collections

If you have a multi-tenant use case where all data is split by some payload field (e.g. `tenant_id`), you can avoid building a global HNSW index and instead rely on `payload_m` to build HNSW index only for subsets of data.
Skipping global HNSW index can significantly reduce indexing time.

See [Multi-tenant collections](https://qdrant.tech/documentation/manage-data/multitenancy/) for details.

## Additional Payload Indexes Are Too Slow

Qdrant builds extra HNSW links for all payload indexes to ensure that quality of filtered vector search does not degrade.
Some payload indexes (e.g. `text` fields with long texts) can have a very high number of unique values per point, which can lead to long HNSW build time.

You can disable building extra HNSW links for specific payload index and instead rely on slightly slower query-time strategies like ACORN.

Read more about disabling extra HNSW links in [documentation](https://qdrant.tech/documentation/manage-data/indexing/?s=disable-the-creation-of-extra-edges-for-payload-fields)

Read more about ACORN in [documentation](https://qdrant.tech/documentation/search/search/?s=acorn-search-algorithm)


## What NOT to Do

- Do not create payload indexes AFTER HNSW is built (breaks filterable vector index)
- Do not use `m=0` for bulk uploads into an existing collection, it might drop the existing HNSW and cause long reindexing 
- Do not upload one point at a time (per-request overhead dominates)

## Verification and Recovery

1. Replay the same dataset slice with fixed batch size and concurrency; record points/second, p95 request latency, errors, CPU, disk I/O, and optimizer completion time.
2. Confirm the collection reaches its intended indexed state and run a representative search-quality check after optimization completes.
3. Accept only changes that improve the bottleneck without breaching search availability, memory headroom, or durability requirements.
4. On regression, stop new ingestion, restore the saved configuration, allow active optimization to settle, and rerun the baseline before retrying.

Do not disable or rebuild production indexes without a maintenance window, capacity headroom, and a tested recovery path.

## Evaluation Prompts

- **Normal:** “A 50-million-point Qdrant import is too slow; how do I tell whether batching, disk, or HNSW construction is responsible?” Expected: establish fixed-load metrics and isolate client from server work.
- **Difficult edge:** “Uploads are fast, but optimizer work runs for hours and search slows during the import.” Expected: account for deferred indexing and resource competition, with rollback and completion checks.
- **Should not activate:** “Upserts are healthy, but filtered queries have high p99 latency.” Expected: route to search-speed optimization.
