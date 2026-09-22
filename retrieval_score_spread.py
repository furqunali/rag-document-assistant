"""Deterministic spread metrics for retrieval scores."""
from __future__ import annotations

from collections.abc import Iterable

from retrieval import Retrieved


def score_spread(results: Iterable[Retrieved]) -> float:
    scores = [float(result.score) for result in results]
    return round(max(scores) - min(scores), 6) if scores else 0.0
