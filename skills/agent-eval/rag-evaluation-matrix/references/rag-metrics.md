# RAG Metrics

## Required Fields

| Field | Meaning |
| --- | --- |
| `pipeline` | Candidate name, for example `basic`, `enhanced-rerank`, `agentic` |
| `question_type` | `answerable`, `unanswerable`, `ambiguous`, `multi-hop`, `adversarial`, or domain label |
| `correct` | Final answer is correct and supported |
| `answerable_correct` | System correctly judged whether the question can be answered from corpus |
| `latency_ms` | End-to-end latency |
| `cost_usd` | Estimated inference and retrieval cost |
| `failure_reason` | `retrieval`, `synthesis`, `citation`, `tool`, `corpus_gap`, `judge_disagreement`, or `other` |

## Minimum Report

- Overall correctness.
- Answerability accuracy.
- Per-question-type correctness.
- Median and p95 latency.
- Cost per successful answer.
- Top failure reasons.
- Ablation conclusion.

## Ship Gate

Ship the simpler pipeline unless the more complex option improves the target segment enough to justify its cost, latency, and maintenance burden.
