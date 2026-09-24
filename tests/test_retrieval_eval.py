"""Tests for offline retrieval-evaluation metrics (retrieval_eval)."""
from __future__ import annotations

import math

import pytest

from models import Chunk
from retrieval import Retrieved
from retrieval_eval import (
    average_precision,
    dcg_at_k,
    evaluate,
    ids_of,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_ids_of_extracts_source_index_keys():
    results = [Retrieved(Chunk("t", "a.md", 0), 0.9), Retrieved(Chunk("u", "b.md", 3), 0.1)]
    assert ids_of(results) == [("a.md", 0), ("b.md", 3)]


def test_precision_and_recall_at_k():
    ranked = ["a", "b", "c", "d"]
    relevant = {"a", "c", "e"}
    assert precision_at_k(ranked, relevant, 2) == pytest.approx(0.5)   # a hit, b miss
    assert precision_at_k(ranked, relevant, 4) == pytest.approx(0.5)   # a,c hit of 4
    assert recall_at_k(ranked, relevant, 4) == pytest.approx(2 / 3)     # found a,c of a,c,e


def test_precision_at_k_beyond_list_uses_available():
    assert precision_at_k(["a"], {"a"}, 5) == pytest.approx(1.0)


def test_reciprocal_rank():
    assert reciprocal_rank(["x", "a", "b"], {"a"}) == pytest.approx(0.5)
    assert reciprocal_rank(["a"], {"a"}) == pytest.approx(1.0)
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_average_precision():
    # relevant at ranks 1 and 3 -> (1/1 + 2/3) / 2
    ap = average_precision(["a", "x", "b"], {"a", "b"})
    assert ap == pytest.approx((1.0 + 2 / 3) / 2)


def test_dcg_and_ndcg():
    ranked = ["a", "x", "b"]
    relevant = {"a", "b"}
    expected_dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)  # ranks 1 and 3
    assert dcg_at_k(ranked, relevant, 3) == pytest.approx(expected_dcg)
    ideal = 1.0 / math.log2(2) + 1.0 / math.log2(3)          # ranks 1 and 2
    assert ndcg_at_k(ranked, relevant, 3) == pytest.approx(expected_dcg / ideal)


def test_ndcg_perfect_is_one():
    assert ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3) == pytest.approx(1.0)


def test_empty_relevant_is_zero_not_error():
    assert recall_at_k(["a"], set(), 3) == 0.0
    assert ndcg_at_k(["a"], set(), 3) == 0.0
    assert average_precision(["a"], set()) == 0.0


def test_evaluate_returns_all_metrics():
    out = evaluate(["a", "b"], {"a"}, k=2)
    assert set(out) == {"precision_at_k", "recall_at_k", "reciprocal_rank", "average_precision", "ndcg_at_k"}
    assert out["reciprocal_rank"] == pytest.approx(1.0)


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_invalid_k_rejected(k):
    with pytest.raises(ValueError):
        precision_at_k(["a"], {"a"}, k)


def test_invalid_types_rejected():
    with pytest.raises(ValueError):
        precision_at_k("not-a-list", {"a"}, 1)
    with pytest.raises(ValueError):
        precision_at_k(["a"], ["not-a-set"], 1)
