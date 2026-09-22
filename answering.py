"""Grounded answer assembly and optional generation hooks."""
from __future__ import annotations

import math
from collections.abc import Callable

from agents import run_multi_agent
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
    result = run_multi_agent(question, hits, threshold, llm)
    citations = citations_for(hits) if result.grounded else []
    return {"answer": result.answer, "grounded": result.grounded, "mode": result.mode,
            "citations": citations, "top_score": round(top, 3),
            "agents": [{"name": d.name, "status": d.status, "details": d.details} for d in result.decisions]}
