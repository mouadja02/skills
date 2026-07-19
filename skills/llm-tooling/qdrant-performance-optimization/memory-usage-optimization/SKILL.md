---
name: memory-usage-optimization
description: "Use when diagnosing Qdrant resident-memory pressure, page-cache confusion, optimization headroom, or RAM-versus-disk placement."
version: "1.0.0"
license: Apache-2.0
source: "https://github.com/qdrant/skills"
attribution: "qdrant/skills by Qdrant"
---

> **Attribution:** Sourced from [qdrant/skills](https://github.com/qdrant/skills) by [Qdrant](https://qdrant.tech).

## When to Use

- Qdrant is near an OOM limit or resident memory grows unexpectedly.
- Operators need to distinguish anonymous resident memory from reclaimable page cache.
- A collection needs a measured RAM-versus-disk placement plan.

Do not use this skill for latency-only or ingestion-only incidents without memory evidence. Use the sibling search or indexing skill instead.

## Prerequisites and Quick Reference

- Capture Qdrant version, collection and quantization settings, vector/payload sizes, resident memory, page cache, swap/OOM events, optimizer status, and storage latency.
- Preserve the current collection configuration and test storage-placement changes on a representative non-production collection.
- Classify first: **resident structures**, **page cache**, **temporary optimizer headroom**, or **dataset/index placement**.
- Measure peak RSS, OOM/restarts, page faults, query latency/QPS, and search quality before and after each change.

The Qdrant links below are sourced facts and upstream guidance. The measurement order, rollback discipline, and acceptance checks are repository recommendations.

# Understanding memory usage

Qdrant operates with two types of memory:

- Resident memory (aka RSSAnon) - memory used for internal data structures like the ID tracker, plus components that must stay in RAM, such as quantized vectors when `always_ram=true` and payload indexes.

- OS page cache - memory used for caching disk reads, which can be released when needed. Original vectors are normally stored in page cache, so the service won't crash if RAM is full, but performance may degrade.

It is normal for the OS page cache to occupy all available RAM, but if resident memory is above 80% of total RAM, it is a sign of a problem.

## Memory usage monitoring

- Qdrant exposes memory usage through the `/metrics` endpoint. See [Monitoring docs](https://qdrant.tech/documentation/ops-monitoring/monitoring/).

<!-- ToDo: Talk about memory usage of each components once API is available -->


## How much memory is needed for Qdrant?

Optimal memory usage depends on the use case.

- For regular search scenarios, general guidelines are provided in the [Capacity planning docs](https://qdrant.tech/documentation/capacity-planning/).

For a detailed breakdown of memory usage at large scale, see [Large scale memory usage example](https://qdrant.tech/documentation/tutorials-operations/large-scale-search/?s=memory-usage).

Payload indexes and HNSW graph also require memory, along with vectors themselves, so it's important to consider them in calculations.

Additionally, Qdrant requires some extra memory for optimizations. During optimization, optimized segments are fully loaded into RAM, so it is important to leave enough headroom.
The larger `max_segment_size` is, the more headroom is needed.


### When to put HNSW index on disk

Putting frequently used components (such as HNSW index) on disk might cause significant performance degradation.
There are some scenarios, however, when it can be a good option:

- Deployments with low latency disks - local NVMe or similar.
- Multi-tenant deployments, where only a subset of tenants is frequently accessed, so that only a fraction of data & index is loaded in RAM at a time.
- For deployments with [inline storage](https://qdrant.tech/documentation/ops-optimization/optimize/?s=inline-storage-in-hnsw-index) enabled.


## How to minimize memory footprint

The main challenge is to put on disk those parts of data, which are rarely accessed.
Here are the main techniques to achieve that:

- Use quantization to store only compressed vectors in RAM [Quantization docs](https://qdrant.tech/documentation/manage-data/quantization/)

- Use float16 or int8 datatypes to reduce memory usage of vectors by 2x or 4x respectively, with some tradeoff in precision. Read more about vector datatypes in [documentation](https://qdrant.tech/documentation/manage-data/vectors/?s=datatypes)

- Leverage Matryoshka Representation Learning (MRL) to store only small vectors in RAM while keeping large vectors on disk. Examples of how to use MRL with Qdrant Cloud inference: [MRL docs](https://qdrant.tech/documentation/inference/matryoshka-models/)

- For multi-tenant deployments with small tenants, vectors might be stored on disk because the same tenant's data is stored together [Multitenancy docs](https://qdrant.tech/documentation/manage-data/multitenancy/?s=calibrate-performance)

- For deployments with fast local storage and relatively low requirements for search throughput, it may be possible to store all components of vector store on disk. Read more about the performance implications of on-disk storage in [the article](https://qdrant.tech/articles/memory-consumption/)

- For low RAM environments, consider `async_scorer` config, which enables support of `io_uring` for parallel disk access, which can significantly improve performance of on-disk storage. Read more about `async_scorer` in [the article](https://qdrant.tech/articles/io_uring/) (only available on Linux with kernel 5.11+)

- Consider storing Sparse Vectors and text payload on disk, as they are usually more disk-friendly than dense vectors.
- Configure payload indexes to be stored on disk [docs](https://qdrant.tech/documentation/manage-data/indexing/?s=on-disk-payload-index)
- Configure sparse vectors to be stored on disk [docs](https://qdrant.tech/documentation/manage-data/indexing/?s=sparse-vector-index)

## Verification and Recovery

1. Replay the same query and optimization workload; record peak RSS, page cache, swap/OOM events, page faults, p95/p99 latency, QPS, and errors.
2. Confirm memory remains below the operational limit through a full optimizer cycle, not only at idle.
3. Run the same relevance/recall check used before any datatype, quantization, or dimensionality change.
4. If latency, quality, or stability regresses, restore the saved settings and storage placement, allow recovery/reindexing to complete, and rerun the baseline.

Do not treat all used RAM as a leak, and do not move latency-critical structures to disk without measured storage behavior and a rollback window.

## Evaluation Prompts

- **Normal:** “Qdrant appears to use all RAM; determine whether this is page cache or dangerous resident growth.” Expected: separate memory classes and collect peak/workload evidence before tuning.
- **Difficult edge:** “Idle RSS is acceptable, but optimization causes OOM and on-disk HNSW hurts p99 latency.” Expected: measure optimizer headroom and storage trade-offs without prescribing an untested blanket change.
- **Should not activate:** “Memory is stable, but bulk upserts are too slow.” Expected: route to indexing-performance optimization.

