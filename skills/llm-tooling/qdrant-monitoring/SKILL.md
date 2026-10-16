---
name: qdrant-monitoring
description: >-
  Guides Qdrant monitoring and observability setup. Use when someone asks 'how to monitor Qdrant',
  'what metrics to track', 'is Qdrant healthy', 'optimizer stuck', 'why is memory growing', 'requests
  are slow', 'set up alerts', 'cluster health check', or needs to set up Prometheus, Grafana, health
  checks, or log centralization. Also use when debugging production issues that require metric
  analysis.
allowed-tools:
  - Read
  - Grep
  - Glob
source: "https://github.com/qdrant/skills"
attribution: "qdrant/skills by Qdrant"
license: Apache-2.0
---

> **Attribution:** Sourced from [qdrant/skills](https://github.com/qdrant/skills) by [Qdrant](https://qdrant.tech).

# Qdrant Monitoring

Qdrant monitoring allows tracking performance and health of your deployment, and identifying issues before they become outages. First determine whether you need to set up monitoring or diagnose an active issue.

- Understand available metrics [Monitoring docs](https://search.qdrant.tech/md/documentation/ops-monitoring/monitoring/)


## Monitoring Setup

Prometheus scraping, health probes, Hybrid Cloud specifics, alerting, and log centralization. [Monitoring Setup](setup/SKILL.md)


## Debugging with Metrics

Optimizer stuck, memory growth, slow requests. Using metrics to diagnose active production issues. [Debugging with Metrics](debugging/SKILL.md)
