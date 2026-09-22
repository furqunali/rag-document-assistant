"""Tests for MMR diversity re-ranking (retrieval_mmr)."""
from __future__ import annotations

import numpy as np
import pytest

from models import Chunk
from retrieval import Retrieved
from retrieval_mmr import mmr_rerank


def _candidate(text: str, index: int) -> Retrieved:
    return Retrieved(Chunk(text=text, source="doc.md", index=index), 0.0)


def test_pure_relevance_orders_by_query_similarity():
    # lambda=1.0 ignores diversity, so order is by relevance to the query.
    query = np.array([1.0, 0.0])
    vectors = np.array([[0.2, 1.0], [0.9, 0.1], [0.6, 0.5]])
    candidates = [_candidate("a", 0), _candidate("b", 1), _candidate("c", 2)]
    result = mmr_rerank(query, vectors, candidates, k=3, lambda_mult=1.0)
    assert [r.chunk.text for r in result] == ["b", "c", "a"]


def test_diversity_avoids_near_duplicate():
    # Two candidates are near-identical; a diversity-biased rerank should not
    # pick both before the distinct third one.
    query = np.array([1.0, 0.0])
    vectors = np.array([[1.0, 0.0], [0.99, 0.01], [0.0, 1.0]])
    candidates = [_candidate("dup1", 0), _candidate("dup2", 1), _candidate("other", 2)]
    picked = [r.chunk.text for r in mmr_rerank(query, vectors, candidates, k=2, lambda_mult=0.3)]
    assert picked[0] == "dup1"          # most relevant first
    assert picked[1] == "other"          # then the novel one, not the duplicate


def test_returns_min_k_and_len():
    query = np.array([1.0, 0.0])
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    candidates = [_candidate("a", 0), _candidate("b", 1)]
    assert len(mmr_rerank(query, vectors, candidates, k=10)) == 2


def test_empty_candidates_returns_empty():
    assert mmr_rerank(np.array([1.0, 0.0]), np.empty((0, 2)), [], k=3) == []


def test_scores_are_query_relevance():
    query = np.array([1.0, 0.0])
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    candidates = [_candidate("a", 0), _candidate("b", 1)]
    top = mmr_rerank(query, vectors, candidates, k=1, lambda_mult=1.0)[0]
    assert top.chunk.text == "a"
    assert top.score == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query_vector": np.zeros((2, 2))},                 # query not 1D
        {"candidate_vectors": np.zeros(2)},                 # candidates not 2D
        {"k": 0},                                            # non-positive k
        {"k": True},                                         # bool is not a valid k
        {"lambda_mult": 1.5},                                # out of range
        {"lambda_mult": -0.1},                               # out of range
    ],
)
def test_input_validation(kwargs):
    base = {
        "query_vector": np.array([1.0, 0.0]),
        "candidate_vectors": np.array([[1.0, 0.0], [0.0, 1.0]]),
        "candidates": [_candidate("a", 0), _candidate("b", 1)],
        "k": 2,
        "lambda_mult": 0.5,
    }
    base.update(kwargs)
    with pytest.raises(ValueError):
        mmr_rerank(**base)


def test_misaligned_candidates_raise():
    with pytest.raises(ValueError):
        mmr_rerank(
            np.array([1.0, 0.0]),
            np.array([[1.0, 0.0], [0.0, 1.0]]),
            [_candidate("only-one", 0)],
            k=1,
        )


def test_non_finite_rejected():
    with pytest.raises(ValueError):
        mmr_rerank(
            np.array([1.0, 0.0]),
            np.array([[np.inf, 0.0], [0.0, 1.0]]),
            [_candidate("a", 0), _candidate("b", 1)],
            k=2,
        )
