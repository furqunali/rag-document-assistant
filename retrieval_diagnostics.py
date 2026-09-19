"""Diagnostics for retrieval quality and result bounds."""
from __future__ import annotations
from typing import Iterable, Mapping, Any

def score_summary(results: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    """Summarize score distribution without changing retrieval behavior."""
    scores = [float(item.get("score", 0.0)) for item in results]
    if not scores:
        return {"count": 0.0, "max": 0.0, "mean": 0.0, "min": 0.0}
    return {
        "count": float(len(scores)),
        "max": max(scores),
        "mean": sum(scores) / len(scores),
        "min": min(scores),
    }

def has_relevant_result(results: Iterable[Mapping[str, Any]], threshold: float) -> bool:
    """Return whether any retrieval score reaches the configured threshold."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    return any(float(item.get("score", 0.0)) >= threshold for item in results)
