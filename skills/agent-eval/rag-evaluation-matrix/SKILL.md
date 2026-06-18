---
name: rag-evaluation-matrix
description: Use when comparing basic, enhanced, GraphRAG, or agentic RAG designs, evaluating domain-specific RAG quality, tuning retrieval components, or deciding whether agentic RAG is worth its cost.
source: "https://arxiv.org/abs/2601.07711"
---

# RAG Evaluation Matrix

Do not choose agentic RAG by fashion. Compare retrieval designs against domain questions, answerability, correctness, cost, latency, and failure reasons.

## Use When

- The user asks whether to use basic RAG, enhanced RAG, GraphRAG, or agentic RAG.
- A RAG system works on demos but fails on domain-specific questions.
- You need to compare embedding models, rerankers, chunking, query rewriting, or tool orchestration.
- LLM-as-judge scores need alignment with human review.

## Evaluation Flow

1. Build a domain question set with answerable, unanswerable, ambiguous, multi-hop, and adversarial cases.
2. For each candidate pipeline, log retrieved evidence, final answer, citations, latency, token usage, and cost.
3. Score answer correctness and answerability separately.
4. Add evidence quality checks: citation support, contradiction handling, source freshness, and missing-source diagnosis.
5. Segment results by question type instead of reporting only one aggregate score.
6. Inspect low-correctness failures and map them to retrieval, synthesis, tool orchestration, or corpus gaps.
7. Pick the simplest design that meets quality, latency, and cost constraints.

## Matrix

| Dimension | Basic RAG | Enhanced RAG | Agentic RAG |
| --- | --- | --- | --- |
| Best for | Stable FAQ and narrow corpora | Noisy corpora, query mismatch, reranking | Multi-step, ambiguous, tool-rich tasks |
| Main risk | Weak recall and unsupported answers | Pipeline complexity | Cost, latency, loops, tool misuse |
| Eval focus | Retrieval recall and citation support | Component ablations | Trajectory, action choice, stopping behavior |
| Ship gate | Correctness and answerability meet threshold | Ablation proves each module helps | Agentic gains justify extra cost |

## Script

Use the helper to combine per-run JSON metrics into a decision table:

```bash
python skills/agent-eval/rag-evaluation-matrix/scripts/rag_eval_matrix.py results/*.json
```

Expected JSON fields: `pipeline`, `question_type`, `correct`, `answerable_correct`, `latency_ms`, `cost_usd`.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Optimizing average score only | Break down by question type and domain |
| Judging unanswerable questions as wrong by default | Score answerability separately |
| Skipping human calibration | Sample judge disagreements and tune rubrics |
| Choosing agentic RAG without ablation | Compare against enhanced RAG at equal budget |
| Ignoring failure reasons | Classify each miss before tuning |

## References

- arXiv: Is Agentic RAG worth it? - https://arxiv.org/abs/2601.07711
- arXiv: RAGalyst - https://arxiv.org/abs/2511.04502
- Hugging Face Papers: RAGalyst - https://huggingface.co/papers/2511.04502
- Hugging Face dataset: RAGalyst QAC - https://huggingface.co/datasets/hoskerelab/ragalyst-qac
