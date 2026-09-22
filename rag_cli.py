"""CLI for deterministic, local RAG queries."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from answering import answer
from chunking import chunk_text
from embeddings import TfidfEmbedder
from retrieval import Retriever


def build_parser():
    p=argparse.ArgumentParser(description="Query local documents with deterministic RAG")
    p.add_argument("question"); p.add_argument("paths",nargs="+",type=Path)
    p.add_argument("--top-k",type=int,default=4); p.add_argument("--threshold",type=float,default=0.15)
    return p

def load_chunks(paths):
    chunks=[]
    for path in sorted(paths):
        candidates=sorted(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in {".txt",".md"}:
                try:
                    content = candidate.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    raise ValueError(f"unable to read document: {candidate}") from exc
                chunks.extend(chunk_text(content, candidate.as_posix()))
    return chunks

def main():
    a=build_parser().parse_args()
    if a.top_k<=0: raise SystemExit("--top-k must be positive")
    if not math.isfinite(a.threshold) or not 0 <= a.threshold <= 1:
        raise SystemExit("--threshold must be a finite value between 0 and 1")
    try:
        chunks=load_chunks(a.paths)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not chunks: raise SystemExit("No .txt or .md documents found.")
    embedder=TfidfEmbedder().fit([c.text for c in chunks])
    hits=Retriever(chunks,embedder).query(a.question,k=a.top_k)
    print(json.dumps(answer(a.question,hits,threshold=a.threshold),indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
