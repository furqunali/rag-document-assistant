"""Deterministic summary statistics for retrieved relevance scores."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from retrieval import Retrieved

@dataclass(frozen=True)
class ScoreProfile:
    count: int
    minimum: float
    maximum: float
    mean: float

def profile_scores(results: Iterable[Retrieved]) -> ScoreProfile:
    scores = [float(result.score) for result in results]
    if not scores:
        return ScoreProfile(0, 0.0, 0.0, 0.0)
    return ScoreProfile(len(scores), round(min(scores), 6), round(max(scores), 6), round(sum(scores) / len(scores), 6))
