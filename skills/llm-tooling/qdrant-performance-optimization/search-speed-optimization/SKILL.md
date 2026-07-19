---
name: search-speed-optimization
description: "Use when diagnosing slow Qdrant queries, low search throughput, filtered-search regressions, or optimizer interference."
version: "1.0.0"
license: Apache-2.0
source: "https://github.com/qdrant/skills"
attribution: "qdrant/skills by Qdrant"
---

> **Attribution:** Sourced from [qdrant/skills](https://github.com/qdrant/skills) by [Qdrant](https://qdrant.tech).

## When to Use

- A single query has excessive latency, or throughput falls under concurrent load.
- Filtered searches are materially slower than equivalent unfiltered searches.
- Search competes with ingestion or background optimization.

Do not use this skill for ingestion-only bottlenecks or capacity planning without query evidence. Use the sibling indexing or memory skill instead.

## Prerequisites and Quick Reference

- Capture a representative query, latency/QPS target, Qdrant version, collection configuration, optimizer status, and host CPU/RAM/disk metrics.
- Change one variable at a time and keep a rollback copy of collection settings.
- Classify first: **single-query latency**, **throughput under load**, **filtered-only**, or **background-work interference**.
- Compare warm and cold runs; use the same dataset and query set before and after each change.

The Qdrant links below are sourced facts and upstream guidance. The diagnostic order, rollback discipline, and acceptance checks are repository recommendations.

# Diagnose a problem

There the multiple possible reasons for search performance degradation. The most common ones are:

* Memory pressure: if the working set exceeds available RAM
* Complex requests (e.g. high `hnsw_ef`, complex filters without payload index)
* Competing background processes (e.g. optimizer still running after bulk upload)
* Problem with the cluster (e.g. network issues, hardware degradation)


## Single Query Too Slow (Latency)

Use when: individual queries take too long regardless of load.

### Diagnostic steps:

- Check if second run of the same request is significantly faster (indicates memory pressure)
- Try the same query with `with_payload: false` and `with_vectors: false` to see if payload retrieval is the bottleneck
- If request uses filters, try to remove them one by one to identify if a specific filter condition is the bottleneck

### Common fixes:

- Tune HNSW parameters: [Fine-tuning search](https://qdrant.tech/documentation/ops-optimization/optimize/?s=fine-tuning-search-parameters)
- Enable in-memory quantization: [Scalar quantization](https://qdrant.tech/documentation/manage-data/quantization/?s=scalar-quantization)
- Reduce Vector Dimensionality with Matryoshka Models: [Matryoshka Models](https://qdrant.tech/documentation/inference/matryoshka-models/)
- Use oversampling + rescore for high-dimensional vectors [Search with quantization](https://qdrant.tech/documentation/manage-data/quantization/?s=searching-with-quantization)
- Enable io_uring for disk-heavy workloads on Linux [io_uring](https://qdrant.tech/articles/io_uring/)


## Can't Handle Enough QPS (Throughput)

Use when: system can't serve enough queries per second under load.

- Reduce segment count (`default_segment_number` to 2) [Maximizing throughput](https://qdrant.tech/documentation/ops-optimization/optimize/?s=maximizing-throughput)
- Use batch search API instead of single queries [Batch search](https://qdrant.tech/documentation/search/search/?s=batch-search-api)
- Enable quantization to reduce CPU cost [Scalar quantization](https://qdrant.tech/documentation/manage-data/quantization/?s=scalar-quantization)
- Add replicas to distribute read load [Replication](https://qdrant.tech/documentation/scaling/distributed_deployment/?s=replication)


## Filtered Search Is Slow

Use when: filtered search is significantly slower than unfiltered. Most common SA complaint after memory.

- Create payload index on the filtered field [Payload index](https://qdrant.tech/documentation/manage-data/indexing/?s=payload-index)
- Use `is_tenant=true` for primary filtering condition: [Tenant index](https://qdrant.tech/documentation/manage-data/indexing/?s=tenant-index)
- Try ACORN algorithm for complex filters: [ACORN](https://qdrant.tech/documentation/search/search/?s=acorn-search-algorithm)
- Avoid using `nested` filtering conditions as a primary filter. It might force qdrant to read raw payload values instead of using index.
- If payload index was added after HNSW build, trigger re-index to create filterable subgraph links


## Optimize search performance with parallel updates

### Diagnostic steps

- Try to run the same query with `indexed_only=true` parameter, if the query is significantly faster, it means that the optimizer is still running and has not yet indexed all segments.
- If CPU or IO usage is high even with no queries, it also indicates that the optimizer is still running.

### Recommended configuration changes

- reduce `optimizer_cpu_budget` to reserve more CPU for queries
- Use `prevent_unoptimized=true` to prevent creating segments with a large amount of unindexed data for searches. Instead, once a segment reaches the so called indexing_threshold, all additional points will be added in ‘deferred state’. 

Learn more [here](https://qdrant.tech/documentation/search/low-latency-search/?s=query-indexed-data-only)


## What NOT to Do

- Set `always_ram=false` on quantization (disk thrashing on every search)
- Put HNSW on disk for latency-sensitive production (only for cold storage)
- Increase segment count for throughput (opposite: fewer = better)
- Create payload indexes on every field (wastes memory)
- Blame Qdrant before checking optimizer status

## Verification and Recovery

1. Replay the same representative query set at the same concurrency and record p50, p95, p99, QPS, errors, CPU, memory, and disk I/O.
2. Accept a change only when the target metric improves without violating recall/quality or error-rate requirements.
3. Repeat a warm-cache run and a cold/restarted run when memory pressure is suspected.
4. If latency, quality, or stability regresses, restore the saved settings, wait for optimizer activity to settle, and rerun the baseline.

Never tune production first. Validate on a representative non-production collection, and schedule changes that rebuild indexes or alter storage placement.

## Evaluation Prompts

- **Normal:** “Qdrant p95 latency doubled, but only for queries filtering on `tenant_id`; give me a measured diagnosis plan.” Expected: isolate filtered search, inspect payload/tenant indexing, and require before/after metrics.
- **Difficult edge:** “Warm queries are fast, cold queries are slow while bulk ingestion is active.” Expected: separate memory pressure from optimizer contention and avoid changing several controls at once.
- **Should not activate:** “My Qdrant upserts are slow but search latency is stable.” Expected: route to indexing-performance optimization rather than applying search tuning.
