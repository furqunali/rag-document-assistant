"""Grounded answer assembly and optional generation hooks."""
from __future__ import annotations

import math
from typing import Callable

from retrieval import Retrieved

IDK = ("I don't have enough information in the provided documents to answer that. "
       "Try rephrasing, or upload a document that covers this topic.")


def validate_threshold(threshold: float) -> float:
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be a finite, non-negative number")
    return threshold


def citations_for(hits: list[Retrieved]) -> list[dict]:
    return [
        {"source": hit.chunk.source, "chunk": hit.chunk.index,
         "score": round(hit.score, 3),
         "preview": hit.chunk.text[:200] + ("…" if len(hit.chunk.text) > 200 else "")}
        for hit in hits
    ]


def answer(question: str, hits: list[Retrieved], threshold: float = 0.15,
           llm: Callable[[str, list[Retrieved]], str] | None = None) -> dict:
    validate_threshold(threshold)
    top = hits[0].score if hits else 0.0
    if not hits or top < threshold:
        return {"answer": IDK, "grounded": False, "citations": [], "top_score": round(top, 3)}
    citations = citations_for(hits)
    body = hits[0].chunk.text
    mode = "extractive"
    if llm is not None:
        try:
            generated = llm(question, hits)
            if generated and generated.strip():
                body, mode = generated.strip(), "generative"
        except Exception:
            mode = "extractive (generation unavailable)"
    return {"answer": body, "grounded": True, "mode": mode,
            "citations": citations, "top_score": round(top, 3)}
