"""Drop near-duplicate passages from a retrieved set by cosine similarity.

Retrievers frequently return several chunks that are near-restatements of one
another (e.g. the same paragraph copied across documents). Feeding all of them
to a model wastes context and biases the answer toward the repeated text. This
filter keeps the first occurrence of each distinct passage and drops any later
candidate whose cosine similarity to an already-kept passage meets/exceeds a
threshold. Unlike MMR re-ranking it preserves the incoming order and never
re-scores — it is a cheap redundancy filter you can run before or after ranking.
"""
from __future__ import annotations

import numpy as np

from retrieval import Retrieved


def dedupe_by_similarity(
    results: list[Retrieved],
    vectors: np.ndarray,
    threshold: float = 0.95,
) -> list[Retrieved]:
    """Return ``results`` with near-duplicate passages removed.

    Args:
        results: retrieved items, in the order they should be considered
            (typically already ranked best-first).
        vectors: 2D array ``(len(results), dim)`` aligned row-for-row.
        threshold: cosine-similarity cutoff in ``[0, 1]``; a candidate is
            dropped when its similarity to any kept item is ``>= threshold``.

    Returns:
        A new list keeping the first item of each near-duplicate group, order
        preserved.

    Raises:
        ValueError: on shape mismatch, non-finite values, or an out-of-range
            threshold.
    """
    vectors = np.asarray(vectors, dtype=float)
    if vectors.ndim != 2:
        raise ValueError("vectors must be a 2D array")
    if len(results) != vectors.shape[0]:
        raise ValueError("results and vectors must be aligned")
    if not np.isfinite(vectors).all():
        raise ValueError("vectors must contain only finite values")
    if not 0.0 <= float(threshold) <= 1.0:
        raise ValueError("threshold must be within [0, 1]")
    if not results:
        return []

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Divide by the true norm (so identical vectors score exactly 1.0); guard
    # only genuine zero-vectors, which stay zero and never count as duplicates.
    safe = np.where(norms == 0.0, 1.0, norms)
    units = vectors / safe

    kept_indices: list[int] = []
    for i in range(len(results)):
        duplicate = False
        for j in kept_indices:
            if float(units[i] @ units[j]) >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept_indices.append(i)
    return [results[i] for i in kept_indices]
