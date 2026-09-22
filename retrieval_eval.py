"""Offline evaluation metrics for retrieval quality.

Given a *ranked* list of retrieved item ids and the set of ids that are truly
relevant for a query, these functions report the standard information-retrieval
metrics used to tune a RAG pipeline: precision@k, recall@k, average precision,
reciprocal rank, and (binary-relevance) nDCG@k. They are embedding- and
model-agnostic — you pass in ids, so they work for any retriever.

Ids may be any hashable value. :func:`ids_of` is a convenience for turning a
list of :class:`retrieval.Retrieved` into the ``(source, index)`` identity keys
this module expects.
"""
from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Sequence

from retrieval import Retrieved


def ids_of(results: Iterable[Retrieved]) -> list[tuple[str, int]]:
    """Return stable identity keys ``(source, index)`` for retrieved chunks."""
    return [(r.chunk.source, r.chunk.index) for r in results]


def _validate(ranked: Sequence[Hashable], relevant: set, k: int) -> None:
    if not isinstance(ranked, (list, tuple)):
        raise ValueError("ranked must be a list or tuple")  # noqa: TRY004 - repo uses ValueError for all validation
    if not isinstance(relevant, (set, frozenset)):
        raise ValueError("relevant must be a set")  # noqa: TRY004 - repo uses ValueError for all validation
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k must be a positive integer")


def precision_at_k(ranked: Sequence[Hashable], relevant: set, k: int) -> float:
    """Fraction of the top-``k`` results that are relevant."""
    _validate(ranked, relevant, k)
    top = ranked[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in relevant)
    return hits / len(top)


def recall_at_k(ranked: Sequence[Hashable], relevant: set, k: int) -> float:
    """Fraction of all relevant items found within the top-``k``."""
    _validate(ranked, relevant, k)
    if not relevant:
        return 0.0
    hits = sum(1 for item in ranked[:k] if item in relevant)
    return hits / len(relevant)


def reciprocal_rank(ranked: Sequence[Hashable], relevant: set) -> float:
    """1 / rank of the first relevant result (0.0 if none present)."""
    _validate(ranked, relevant, 1)
    for position, item in enumerate(ranked, start=1):
        if item in relevant:
            return 1.0 / position
    return 0.0


def average_precision(ranked: Sequence[Hashable], relevant: set) -> float:
    """Mean of precision@k taken at each rank where a relevant item appears."""
    _validate(ranked, relevant, 1)
    if not relevant:
        return 0.0
    hits = 0
    running = 0.0
    for position, item in enumerate(ranked, start=1):
        if item in relevant:
            hits += 1
            running += hits / position
    return running / len(relevant)


def dcg_at_k(ranked: Sequence[Hashable], relevant: set, k: int) -> float:
    """Discounted cumulative gain@k with binary relevance."""
    _validate(ranked, relevant, k)
    total = 0.0
    for position, item in enumerate(ranked[:k], start=1):
        if item in relevant:
            total += 1.0 / math.log2(position + 1)
    return total


def ndcg_at_k(ranked: Sequence[Hashable], relevant: set, k: int) -> float:
    """Normalised DCG@k in ``[0, 1]`` (1.0 = ideal ordering)."""
    _validate(ranked, relevant, k)
    ideal_hits = min(len(relevant), k)
    if ideal_hits == 0:
        return 0.0
    ideal = sum(1.0 / math.log2(position + 1) for position in range(1, ideal_hits + 1))
    return dcg_at_k(ranked, relevant, k) / ideal


def evaluate(ranked: Sequence[Hashable], relevant: set, k: int = 5) -> dict[str, float]:
    """Return all metrics at once as a dict, keyed by metric name."""
    _validate(ranked, relevant, k)
    return {
        "precision_at_k": precision_at_k(ranked, relevant, k),
        "recall_at_k": recall_at_k(ranked, relevant, k),
        "reciprocal_rank": reciprocal_rank(ranked, relevant),
        "average_precision": average_precision(ranked, relevant),
        "ndcg_at_k": ndcg_at_k(ranked, relevant, k),
    }
