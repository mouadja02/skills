# Evidence and Incident Report Schema

Use this as a semantic contract. Adapt field names to the user's system, but do not drop provenance, mapping confidence, unknowns, or safety gates.

## Normalized evidence

One incident contains ordered `stage_evidence` records:

| Field | Meaning |
|---|---|
| `stage` | `rewrite`, `embedding`, `retrieval`, `reranking`, `context_assembly`, or `generation` |
| `attempt` | Retry/attempt number; do not merge retries silently |
| `input` / `output` | Redacted values, structured summaries, or content digests |
| `source_locator` | Span/call/row/file and JSON path needed to reproduce the observation |
| `mapping_method` | Explicit semantic kind, provider rule, topology, ordering, or inference |
| `mapping_confidence` | Qualitative level plus the reason; not an invented probability |
| `completeness` | Complete, truncated, sampled, redacted, or unknown |
| `contract` | Stage-specific expected behavior |
| `assessment` | `supported_fault`, `no_supported_fault`, `downstream_symptom`, or `insufficient_evidence` |
| `reason` | Evidence-based explanation, including propagated-fault handling |

Keep raw evidence read-only outside the report when it contains sensitive content. The report may hold redacted excerpts and digests.

## Mapping validation

Record:

- expected and observed stage sequence;
- missing, optional, duplicated, retried, batched, and out-of-order records;
- trace/run join keys and parent-child validity;
- clock and timestamp limitations;
- redaction/sampling/truncation effects;
- every ambiguous mapping that could alter the verdict.

Set mapping status to `usable`, `usable_with_caveats`, or `insufficient`. Do not infer completeness merely because a trace ended normally.

## Earliest supported fault

The verdict object should include:

```json
{
  "stage": "retrieval",
  "status": "provisional",
  "violated_contract": "Known-relevant indexed evidence was absent from candidates",
  "evidence_locators": ["trace.jsonl:41 $.attributes.retrieval.documents"],
  "confidence": "moderate",
  "confidence_bound": "Corpus snapshot is pinned, but one retrieval retry was truncated",
  "downstream_effects": ["reranker had no relevant candidate", "generator context lacked evidence"]
}
```

Use `null` if no stage is directly supported. A downstream symptom is not automatically a second fault.

## Replay record

A replay must state:

- hypothesis and competing hypothesis;
- frozen inputs, versions, settings, and snapshot IDs;
- one changed variable;
- expected observations and predeclared decision rule;
- environment and isolation boundary;
- authorization needed for paid calls, capture, certificate changes, mutation, or injection;
- actual command/run ID, result, cost, and artifacts—or `not_executed`.

## Outcome states

- `localized`: direct evidence plus controlled replay support the same earliest stage.
- `provisional`: direct recorded evidence supports a stage; replay is pending or unavailable.
- `inconclusive`: evidence or mapping cannot discriminate material alternatives.
- `not_applicable`: no per-run stage-localization question exists.

## Source-shape notes

### Recorded API calls

Correlate request/response pairs, inbound run boundaries, retries, provider endpoints, timestamps, and redaction. Provider endpoint names may suggest a stage but do not prove semantic role.

### Run tables

Require the original question and answer plus any available rewrite, embedding input, retrieved candidates/scores, reranker order/scores, selected context, settings, and reference. A table row that only has question and answer cannot localize a stage.

### OpenTelemetry/OpenInference

Retain trace ID, span ID, parent span ID, timestamps, `openinference.span.kind`, input/output attributes, document IDs/content/scores, model identifiers, and token/cost attributes. Validate topology: the first LLM span is not always a rewrite, and the last LLM span is not always the final generator in agentic or parallel traces.

## Restricted evidence

Do not copy production traces, credentials, proprietary documents, or separately licensed benchmark logs into a public report or skill package. Record a digest, redacted locator, access boundary, and applicable terms instead.
