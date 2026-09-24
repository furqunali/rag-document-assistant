"""Tests for similarity-based de-duplication (retrieval_dedupe)."""
from __future__ import annotations

import numpy as np
import pytest

from models import Chunk
from retrieval import Retrieved
from retrieval_dedupe import dedupe_by_similarity


def _r(text: str, index: int) -> Retrieved:
    return Retrieved(Chunk(text=text, source="doc.md", index=index), 0.0)


def test_drops_near_duplicate_keeps_first():
    results = [_r("a", 0), _r("a-dup", 1), _r("b", 2)]
    vectors = np.array([[1.0, 0.0], [0.999, 0.001], [0.0, 1.0]])
    kept = dedupe_by_similarity(results, vectors, threshold=0.95)
    assert [r.chunk.text for r in kept] == ["a", "b"]  # duplicate of 'a' removed


def test_keeps_all_when_distinct():
    results = [_r("a", 0), _r("b", 1)]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert len(dedupe_by_similarity(results, vectors, threshold=0.9)) == 2


def test_threshold_one_keeps_all_but_exact():
    results = [_r("a", 0), _r("a2", 1)]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])  # identical -> sim 1.0 >= 1.0
    assert [r.chunk.text for r in dedupe_by_similarity(results, vectors, threshold=1.0)] == ["a"]


def test_order_preserved():
    results = [_r("x", 0), _r("y", 1), _r("z", 2)]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
    assert [r.chunk.index for r in dedupe_by_similarity(results, vectors, threshold=0.99)] == [0, 1, 2]


def test_empty_returns_empty():
    assert dedupe_by_similarity([], np.empty((0, 2)), threshold=0.9) == []


@pytest.mark.parametrize(
    "vectors,threshold",
    [
        (np.zeros(2), 0.9),                    # not 2D
        (np.array([[1.0, 0.0]]), 1.5),         # threshold out of range
        (np.array([[1.0, 0.0]]), -0.1),        # threshold out of range
        (np.array([[np.inf, 0.0], [0.0, 1.0]]), 0.9),  # non-finite
    ],
)
def test_validation(vectors, threshold):
    results = [_r("a", 0), _r("b", 1)]
    with pytest.raises(ValueError):
        dedupe_by_similarity(results, vectors, threshold=threshold)


def test_misaligned_raises():
    with pytest.raises(ValueError):
        dedupe_by_similarity([_r("a", 0)], np.array([[1.0, 0.0], [0.0, 1.0]]), threshold=0.9)
