"""Maximal Marginal Relevance (MMR) re-ranking for diverse retrieval.

Plain nearest-neighbour retrieval often returns several near-duplicate chunks
that say the same thing, wasting the limited context window of a language model.
MMR (Carbonell & Goldstein, 1998) re-ranks candidates by balancing *relevance*
to the query against *novelty* relative to the results already chosen, so the
final set covers more of the answer with fewer redundant passages.

The selection rule, applied greedily, is::

    next = argmax_i [ lambda * sim(query, c_i)
                      - (1 - lambda) * max_{j in selected} sim(c_i, c_j) ]

where ``lambda`` (``lambda_mult``) trades off relevance (1.0) against
diversity (0.0). This module is embedding-agnostic: it works with any vectors
produced by :mod:`embeddings`, and reuses :func:`retrieval.cosine_scores` so its
relevance numbers match the rest of the pipeline.
"""
from __future__ import annotations

import numpy as np

from retrieval import Retrieved, cosine_scores


def _unit_rows(matrix: np.ndarray) -> np.ndarray:
    """Return ``matrix`` with each row scaled to unit length (safe for zeros)."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / (norms + 1e-9)


def mmr_rerank(
    query_vector: np.ndarray,
    candidate_vectors: np.ndarray,
    candidates: list[Retrieved],
    k: int = 4,
    lambda_mult: float = 0.5,
) -> list[Retrieved]:
    """Re-rank ``candidates`` with Maximal Marginal Relevance.

    Args:
        query_vector: 1D embedding of the query.
        candidate_vectors: 2D array ``(n_candidates, dim)`` aligned row-for-row
            with ``candidates``.
        candidates: retrieved items to re-rank.
        k: maximum number of results to return.
        lambda_mult: relevance/diversity trade-off in ``[0, 1]`` — ``1.0`` is
            pure relevance, ``0.0`` is pure diversity.

    Returns:
        A new list of :class:`retrieval.Retrieved`, length ``min(k, len(candidates))``,
        in MMR-selected order. Each item's ``score`` is its query relevance.

    Raises:
        ValueError: on shape mismatch, non-finite values, a non-positive integer
            ``k``, or a ``lambda_mult`` outside ``[0, 1]``.
    """
    query_vector = np.asarray(query_vector, dtype=float)
    candidate_vectors = np.asarray(candidate_vectors, dtype=float)
    if query_vector.ndim != 1:
        raise ValueError("query_vector must be a 1D array")
    if candidate_vectors.ndim != 2:
        raise ValueError("candidate_vectors must be a 2D array")
    if len(candidates) != candidate_vectors.shape[0]:
        raise ValueError("candidates and candidate_vectors must be aligned")
    if candidate_vectors.shape[1] != query_vector.shape[0]:
        raise ValueError("candidate and query dimensions must match")
    if not np.isfinite(candidate_vectors).all() or not np.isfinite(query_vector).all():
        raise ValueError("vectors must contain only finite values")
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k must be a positive integer")
    if not 0.0 <= float(lambda_mult) <= 1.0:
        raise ValueError("lambda_mult must be within [0, 1]")
    if not candidates:
        return []

    relevance = cosine_scores(candidate_vectors, query_vector)
    units = _unit_rows(candidate_vectors)
    similarity = units @ units.T  # pairwise cosine similarity between candidates

    limit = min(k, len(candidates))
    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < limit:
        best_idx = remaining[0]
        best_score: float | None = None
        for i in remaining:
            redundancy = max((similarity[i, j] for j in selected), default=0.0)
            score = lambda_mult * float(relevance[i]) - (1.0 - lambda_mult) * float(redundancy)
            # Strict comparison keeps the earliest candidate on ties -> deterministic.
            if best_score is None or score > best_score:
                best_score = score
                best_idx = i
        selected.append(best_idx)
        remaining.remove(best_idx)

    return [Retrieved(candidates[i].chunk, float(relevance[i])) for i in selected]
