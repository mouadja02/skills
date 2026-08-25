# Agent Graph Attributes

This document covers the graph attributes that let Phoenix reconstruct an agent workflow as a
graph rather than a flat span tree.

## Overview

Parent/child span nesting captures *call* structure. It does not capture the *topology* of a
stateful agent workflow — a node revisited on a loop, or a conditional edge taken between two
nodes that are siblings in the trace. Graph attributes add that layer.

| Attribute                | Type   | Description                                          |
| ------------------------ | ------ | ---------------------------------------------------- |
| `graph.node.id`          | String | Stable identifier for this node in the workflow      |
| `graph.node.name`        | String | Human-readable node label shown in the UI            |
| `graph.node.parent_id`   | String | `graph.node.id` of the upstream node                 |

These are typically set on `CHAIN` or `AGENT` spans. Frameworks with an explicit graph runtime
(LangGraph most notably) emit them automatically via auto-instrumentation.

## The Key Distinction

`graph.node.parent_id` refers to another **node id**, not a span id. This is what lets the graph
diverge from the span tree:

- A node executed three times in a loop emits three spans, all with the same `graph.node.id`.
- Two nodes can be siblings in the span tree while being sequential in the graph.

Node ids must therefore be **stable across executions** — derive them from the workflow
definition, not from a per-run UUID.

## Example — A Linear Workflow

```json
{
  "openinference.span.kind": "CHAIN",
  "graph.node.id": "retrieve",
  "graph.node.name": "Retrieve Documents"
}
```

```json
{
  "openinference.span.kind": "LLM",
  "graph.node.id": "generate",
  "graph.node.name": "Generate Answer",
  "graph.node.parent_id": "retrieve"
}
```

Phoenix renders `retrieve → generate`.

## Example — A Loop with a Conditional Edge

An agent that retrieves, grades the result, and retries retrieval when the grade is poor:

```json
{
  "openinference.span.kind": "CHAIN",
  "graph.node.id": "grade",
  "graph.node.name": "Grade Relevance",
  "graph.node.parent_id": "retrieve"
}
```

```json
{
  "openinference.span.kind": "CHAIN",
  "graph.node.id": "retrieve",
  "graph.node.name": "Retrieve Documents",
  "graph.node.parent_id": "grade"
}
```

The second `retrieve` span reuses node id `retrieve`, so Phoenix draws the cycle
`retrieve → grade → retrieve` instead of inventing a second node.

## Guidance

| Practice                                        | Why                                                        |
| ------------------------------------------------ | ----------------------------------------------------------- |
| Derive node ids from the workflow definition      | Keeps the graph stable across runs and comparable over time  |
| Keep `graph.node.name` short                      | It is rendered as a node label                               |
| Omit `graph.node.parent_id` on the entry node     | Marks the graph's root                                       |
| Set them on the span that *is* the node           | Not on every descendant span the node happens to create      |
| Leave them off for straight-line pipelines        | Span nesting already tells that story                        |

## See Also

- `span-agent.md` — AGENT spans for autonomous reasoning blocks
- `span-chain.md` — CHAIN spans for multi-step workflows
- `instrumentation-auto-python.md` — frameworks that emit these attributes for you
- `sessions-python.md` / `sessions-typescript.md` — grouping whole conversations rather than nodes
