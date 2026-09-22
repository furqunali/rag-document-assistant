"""Deterministic summary statistics for retrieved relevance scores."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from retrieval import Retrieved


@dataclass(frozen=True)
class ScoreProfile:
    count: int
    minimum: float
    maximum: float
    mean: float
    above_threshold: int

def profile_scores(results: Iterable[Retrieved], *, threshold: float | None = None) -> ScoreProfile:
    scores = [float(result.score) for result in results]
    if threshold is not None and not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if not scores:
        return ScoreProfile(0, 0.0, 0.0, 0.0, 0)
    above = sum(score >= threshold for score in scores) if threshold is not None else 0
    return ScoreProfile(len(scores), round(min(scores), 6), round(max(scores), 6), round(sum(scores) / len(scores), 6), above)
