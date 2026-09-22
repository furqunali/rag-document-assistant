"""Deterministic quality profile for a retrieved evidence set."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from retrieval import Retrieved

@dataclass(frozen=True)
class RetrievalQuality:
    count: int
    distinct_sources: int
    minimum_score: float
    maximum_score: float
    mean_score: float
    threshold_hits: int

def profile_retrieval_quality(results: Iterable[Retrieved], *, threshold: float = 0.5) -> RetrievalQuality:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    items=list(results)
    if not items: return RetrievalQuality(0,0,0.0,0.0,0.0,0)
    scores=[float(x.score) for x in items]
    return RetrievalQuality(len(items),len({x.chunk.source for x in items}),
        round(min(scores),6),round(max(scores),6),round(sum(scores)/len(scores),6),
        sum(x >= threshold for x in scores))
