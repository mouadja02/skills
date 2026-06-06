---
name: multimodal-rag-architecture
description: Use when designing or auditing RAG over PDFs, images, tables, charts, equations, video frames, or heterogeneous documents where text-only chunking loses important evidence.
source: "https://arxiv.org/abs/2510.12323"
attribution: "Synthesized from RAG-Anything, VimRAG, and multimodal RAG research."
---

# Multimodal RAG Architecture

Use this skill when a knowledge base contains more than plain text. Treat images, tables, equations, layout, captions, and cross-page structure as first-class evidence instead of stripping everything into text chunks.

## When Text-Only RAG Fails

Switch to multimodal RAG when:

- Important answers live in tables, charts, screenshots, diagrams, figures, or equations
- PDFs have layout-dependent meaning such as forms, invoices, manuals, or scientific papers
- The same concept appears across text, image, and table regions
- Long documents cause retrieval to miss sparse visual evidence
- Users ask for answers that require comparing visual and textual context

## Architecture

1. **Parse by modality**
   - Text blocks
   - Tables
   - Figures and images
   - Equations
   - Captions
   - Page and section layout

2. **Create multimodal evidence nodes**
   - Preserve source document, page, bounding box, modality, caption, extracted text, and raw asset pointer.
   - Attach normalized text summaries for retrieval.
   - Keep original media accessible for answer verification.

3. **Build relationships**
   - Figure-to-caption
   - Table-to-section
   - Equation-to-explanation
   - Cross-page continuation
   - Visual element-to-text mention

4. **Retrieve in stages**
   - Query rewrite into text, table, and visual intents.
   - Hybrid lexical/vector retrieval over summaries and extracted text.
   - Graph traversal to pull adjacent evidence.
   - Optional visual reranking for image-heavy answers.

5. **Generate with provenance**
   - Cite document, page, modality, and region.
   - Distinguish extracted facts from model interpretation.
   - Re-open raw assets when the answer depends on visual detail.

## Design Rules

- Do not OCR everything and discard layout.
- Do not embed raw image summaries without retaining the image.
- Do not answer from captions alone when the figure itself matters.
- Prefer smaller modality-specific indexes over one overloaded index.
- Keep chunk boundaries aligned to document structure, not fixed token counts.
- Record extraction confidence for OCR, table parsing, and visual descriptions.

## Helper Script

Use [rag_modality_audit.py](./scripts/rag_modality_audit.py) to scan a folder and estimate whether a corpus needs multimodal handling:

```bash
python scripts/rag_modality_audit.py ./docs
```

## References

Read [architecture-checklist.md](./references/architecture-checklist.md) when implementing or reviewing a multimodal RAG pipeline.

External grounding:

- [RAG-Anything arXiv paper](https://arxiv.org/abs/2510.12323)
- [RAG-Anything GitHub repository](https://github.com/HKUDS/RAG-Anything)
- [VimRAG HuggingFace paper page](https://huggingface.co/papers/2602.12735)
- [Alibaba-NLP/VRAG GitHub repository](https://github.com/Alibaba-NLP/VRAG)
- [HM-RAG arXiv paper](https://arxiv.org/abs/2504.12330)

