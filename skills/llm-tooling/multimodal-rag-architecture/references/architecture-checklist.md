# Multimodal RAG Architecture Checklist

## Corpus Audit

- What modalities exist: text, tables, images, figures, equations, charts, video, audio?
- Which modalities are answer-critical rather than decorative?
- Are documents long enough that important evidence is sparse?
- Does layout encode relationships?
- Are source assets retained after parsing?

## Index Design

Use separate fields for:

- `document_id`
- `page`
- `section`
- `modality`
- `bbox`
- `text`
- `summary`
- `caption`
- `asset_path`
- `extraction_confidence`
- `neighbors`

## Retrieval Design

Use hybrid retrieval:

1. Lexical lookup for exact terms, identifiers, and table labels.
2. Vector lookup for semantic paraphrases.
3. Modality-specific routing for table, figure, equation, and image requests.
4. Graph expansion to neighboring captions, sections, or related visual nodes.
5. Reranking with source diversity and provenance quality.

## Evaluation

Test with questions that require:

- Reading a value from a table
- Interpreting a chart or figure
- Linking caption text to image content
- Combining text and table evidence
- Finding evidence in a long document
- Rejecting unsupported visual claims

## References

- RAG-Anything: https://arxiv.org/abs/2510.12323
- RAG-Anything code: https://github.com/HKUDS/RAG-Anything
- VimRAG: https://huggingface.co/papers/2602.12735
- VRAG code: https://github.com/Alibaba-NLP/VRAG
- HM-RAG: https://arxiv.org/abs/2504.12330

