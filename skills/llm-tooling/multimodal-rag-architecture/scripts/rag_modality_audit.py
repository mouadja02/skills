#!/usr/bin/env python3
"""Scan a corpus path and report likely multimodal RAG requirements."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path


MODALITY_EXTENSIONS = {
    "pdf": {".pdf"},
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"},
    "table": {".csv", ".tsv", ".xlsx", ".xls", ".parquet"},
    "video": {".mp4", ".mov", ".webm", ".mkv"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg"},
    "text": {".txt", ".md", ".rst", ".html", ".json", ".xml", ".yaml", ".yml"},
}


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    for modality, extensions in MODALITY_EXTENSIONS.items():
        if suffix in extensions:
            return modality
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Corpus directory or file")
    args = parser.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
    counts = Counter(classify(path) for path in files)

    print("# RAG Modality Audit\n")
    print(f"Files scanned: {len(files)}\n")
    print("## Modalities")
    for modality, count in counts.most_common():
        print(f"- {modality}: {count}")

    multimodal = sum(counts[m] for m in ("pdf", "image", "table", "video", "audio"))
    print("\n## Recommendation")
    if multimodal == 0:
        print("- Text-first RAG is likely sufficient, but preserve document metadata and provenance.")
    else:
        print("- Use multimodal parsing and preserve raw assets for answer verification.")
        if counts["pdf"]:
            print("- Parse PDF layout into page, block, table, figure, caption, and equation nodes.")
        if counts["image"] or counts["video"]:
            print("- Add visual summaries and keep image or frame references for reinspection.")
        if counts["table"]:
            print("- Index tables separately and preserve row, column, and source-sheet coordinates.")

    print("\n## Minimum Metadata")
    print("- document_id, page_or_time, modality, region, extracted_text, summary, asset_path, confidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

