"""Reciprocal Rank Fusion (RRF) for combining several ranked result lists.

A RAG pipeline often produces more than one ranking of the same corpus — for
example a dense cosine ranking from :mod:`retrieval`, an MMR-diversified ranking
from :mod:`retrieval_mmr`, and perhaps a keyword/BM25 ranking. Each ordering is
informative but noisy, and their raw scores live on incompatible scales, so they
cannot simply be averaged.

Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, 2009) sidesteps score
calibration entirely: it fuses lists using only the *rank* of each item. An item
that appears near the top of several lists is rewarded, while an item that ranks
highly in just one is not over-trusted. The fused score of a chunk ``c`` is::

    rrf(c) = sum over lists L of  1 / (rrf_k + rank_L(c))

where ``rank_L(c)`` is the 0-based position of ``c`` in list ``L`` (items absent
from a list contribute nothing) and ``rrf_k`` is a smoothing constant that damps
the influence of the very top ranks; the literature default is ``60``.

This module is scale-free and embedding-agnostic. It consumes and returns
:class:`retrieval.Retrieved` items so it drops into the existing pipeline, and it
identifies "the same chunk" across lists by the identity of the underlying
:class:`models.Chunk` (``source``, ``index``, ``text``).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from models import Chunk
from retrieval import Retrieved

ChunkKey = tuple[str, int, str]


def _chunk_key(chunk: Chunk) -> ChunkKey:
    """Return a hashable identity for ``chunk`` (``Chunk`` itself is unhashable)."""
    return (chunk.source, chunk.index, chunk.text)


def rrf_fuse(
    ranked_lists: Sequence[Sequence[Retrieved]],
    k: int = 4,
    rrf_k: float = 60.0,
) -> list[Retrieved]:
    """Fuse several ranked result lists into one ranking via Reciprocal Rank Fusion.

    Args:
        ranked_lists: a sequence of ranked lists, each already ordered
            best-first. Lists may have different lengths and may share chunks.
            An empty outer sequence, or lists that are all empty, yields ``[]``.
        k: maximum number of fused results to return.
        rrf_k: RRF smoothing constant (must be positive). Larger values flatten
            the contribution of rank position; ``60`` is the standard default.

    Returns:
        A new list of :class:`retrieval.Retrieved`, length ``min(k, n_unique)``,
        ordered by descending fused score. Each item's ``score`` is its RRF
        score (a small positive number, not a cosine similarity). Ties are broken
        deterministically by the chunk's ``index`` then ``source``.

    Raises:
        ValueError: if ``ranked_lists`` is not a sequence of sequences, any item
            is not a :class:`retrieval.Retrieved`, ``k`` is not a positive
            integer, or ``rrf_k`` is not positive and finite.
    """
    if isinstance(ranked_lists, (str, bytes)) or not isinstance(ranked_lists, Sequence):
        raise ValueError("ranked_lists must be a sequence of ranked lists")  # noqa: TRY004
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k must be a positive integer")
    rrf_k = float(rrf_k)
    if not math.isfinite(rrf_k) or rrf_k <= 0.0:
        raise ValueError("rrf_k must be a positive, finite number")

    scores: dict[ChunkKey, float] = {}
    representative: dict[ChunkKey, Chunk] = {}
    first_seen: dict[ChunkKey, int] = {}
    order = 0

    for ranked in ranked_lists:
        if isinstance(ranked, (str, bytes)) or not isinstance(ranked, Sequence):
            raise ValueError("each entry of ranked_lists must be a sequence")  # noqa: TRY004
        for rank, item in enumerate(ranked):
            if not isinstance(item, Retrieved):
                raise ValueError("ranked lists must contain Retrieved items")  # noqa: TRY004
            key = _chunk_key(item.chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            if key not in representative:
                representative[key] = item.chunk
                first_seen[key] = order
                order += 1

    if not scores:
        return []

    fused_keys = sorted(
        scores,
        key=lambda key: (
            -scores[key],
            representative[key].index,
            representative[key].source,
            first_seen[key],
        ),
    )
    limit = min(k, len(fused_keys))
    return [Retrieved(representative[key], scores[key]) for key in fused_keys[:limit]]
