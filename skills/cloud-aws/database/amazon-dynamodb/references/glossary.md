# DynamoDB axioms: glossary

Moved verbatim from SKILL.md so the entry file stays small. Citations such as "Mechanics #18" or "Data modeling #14" refer to the numbered axioms in `axioms-mechanics.md` and `axioms-data-modeling.md` in this folder.

## Glossary

- **Access pattern** — a request the application makes against the data layer, described by its key conditions, items returned, frequency, and consistency requirement. The atomic unit of DynamoDB design.
- **Aggregate** — a cluster of entities that are read or written together. A single item, an item collection, or a set of items under different keys can each be an aggregate; the choice is the subject of Mechanics #1.
- **Item collection** — the set of items sharing a single partition-key value. Queries against an item collection are constant-partition and cheap; cross-partition reads are not.
- **Identifying relationship** — a data model in which a child entity is keyed by its parent's identifier plus its own. The child has no independent existence outside the parent.
- **Overloaded key** — a partition or sort key whose value encodes a type prefix (e.g. `USER#42`, `ORDER#42`) so that one physical key holds multiple logical entity types.
- **Sparse GSI** — a GSI whose indexed attribute is present on only a subset of base-table items, so the index projects only those items. Useful when an access pattern would otherwise filter out most items at read time.
- **GSI write amplification** — the property that every write to a base-table item with projected GSI attributes produces one write per matching GSI, each billed in WCU.
- **LWW** (last-writer-wins) — the conflict resolution strategy used by standard Global Tables: the write with the newest timestamp wins; earlier writes are silently discarded.
- **MRSC** (Multi-Region Strong Consistency) — an opt-in Global Tables mode that provides strong consistency across replicas via consensus, at higher write latency and cost.
- **Hot partition** — a partition receiving traffic beyond the per-partition throughput ceiling (Mechanics #3), causing throttling even when table-level capacity is available.
- **Poison pill** — a record that a stream consumer cannot process successfully, which blocks forward progress on its shard until it is discarded, retried to exhaustion, or routed to an on-failure destination.
- **RCU / WCU** — read and write capacity units; the provisioned-mode spelling of the per-operation throughput unit. The formulas in Mechanics #18 are written in RCU/WCU and apply identically to on-demand.
- **RRU / WRU** — read and write *request* units: the on-demand (PAY_PER_REQUEST) spelling of the same per-operation unit, billed per request rather than per provisioned capacity-second. One RRU = one RCU of work and one WRU = one WCU of work — the consumption math in Mechanics #18 is identical; only the billing dimension differs. The cost references (`cost-model-schema.md`) use RRU/WRU because the calculator prices on-demand; the axioms and the performance report use RCU/WCU. They are the same quantity — do not treat a model's RRU/WRU figure and the report's RCU/WCU figure as different things.
