---
name: qdrant-search-quality
description: >-
  Diagnoses and improves Qdrant search relevance by separating embedding-model, data/chunking,
  configuration, and query-strategy causes; links to diagnosis and search-strategy sub-skills. Use
  when search results are bad, irrelevant, or missing expected matches, or when precision or recall is
  low.
allowed-tools:
  - Read
  - Grep
  - Glob
source: "https://github.com/qdrant/skills"
attribution: "qdrant/skills by Qdrant"
license: Apache-2.0
---

> **Attribution:** Sourced from [qdrant/skills](https://github.com/qdrant/skills) by [Qdrant](https://qdrant.tech).

# Qdrant Search Quality

First determine whether the problem is the embedding model, Qdrant configuration, or the query strategy. Most quality issues come from the model or data, not from Qdrant itself. If search quality is low, inspect how chunks are being passed to Qdrant before tuning any parameters. Splitting mid-sentence can drop quality 30-40%.

- Start by testing with exact search to isolate the problem [Search API](https://search.qdrant.tech/md/documentation/search/search/?s=search-api)


## Diagnosis and Tuning

Isolate the source of quality issues, tune HNSW parameters, and choose the right embedding model. [Diagnosis and Tuning](diagnosis/SKILL.md)


## Search Strategies

Hybrid search, reranking, relevance feedback, and exploration APIs for improving result quality. [Search Strategies](search-strategies/SKILL.md)
