"""Tests for the compact BM25 ranker (bm25_lite)."""
from __future__ import annotations

import pytest

from bm25_lite import BM25Index, BM25Result


def _corpus():
    return [
        ["the", "cat", "sat", "on", "the", "mat"],
        ["the", "dog", "chased", "the", "cat"],
        ["birds", "fly", "in", "the", "sky"],
    ]


def test_ranks_document_with_query_term_first():
    index = BM25Index(_corpus())
    ranked = index.rank(["cat"])
    assert ranked[0].index in (0, 1)  # both mention "cat"
    assert ranked[-1].index == 2      # doc 2 has no "cat" -> last


def test_document_without_any_term_scores_zero():
    index = BM25Index(_corpus())
    assert index.score(["cat"], 2) == 0.0


def test_scores_are_non_negative():
    index = BM25Index(_corpus())
    ranked = index.rank(["the", "cat", "dog"])
    assert all(r.score >= 0.0 for r in ranked)


def test_term_frequency_saturates():
    # Repeating a term adds less each time (diminishing returns).
    index = BM25Index([["x"], ["x", "x"], ["x", "x", "x", "x"]])
    s1 = index.score(["x"], 0)
    s2 = index.score(["x"], 1)
    s4 = index.score(["x"], 2)
    assert s2 > s1
    assert s4 > s2
    # The jump from 1->2 occurrences exceeds the jump from 2->4 per extra token.
    assert (s2 - s1) > (s4 - s2) / 2


def test_idf_prefers_rarer_term():
    # "rare" appears in one doc; "common" appears in all -> rare scores higher.
    corpus = [
        ["common", "rare"],
        ["common", "filler"],
        ["common", "filler"],
    ]
    index = BM25Index(corpus)
    assert index.score(["rare"], 0) > index.score(["common"], 0)


def test_top_k_limits_results():
    index = BM25Index(_corpus())
    assert len(index.rank(["the"], top_k=2)) == 2


def test_rank_is_sorted_and_tie_broken_by_index():
    # Two identical docs must appear in ascending index order.
    index = BM25Index([["a", "b"], ["a", "b"], ["c"]])
    ranked = index.rank(["a"])
    top_two = [r.index for r in ranked[:2]]
    assert top_two == [0, 1]
    assert ranked[0].score == ranked[1].score


def test_empty_corpus_ranks_nothing():
    index = BM25Index([])
    assert index.rank(["anything"]) == []
    assert index.corpus_size == 0
    assert index.average_length == 0.0


def test_empty_query_scores_zero_but_returns_all():
    index = BM25Index(_corpus())
    ranked = index.rank([])
    assert len(ranked) == 3
    assert all(r.score == 0.0 for r in ranked)


def test_results_are_bm25_result_instances():
    index = BM25Index(_corpus())
    assert all(isinstance(r, BM25Result) for r in index.rank(["cat"]))


def test_b_zero_ignores_length():
    # With b=0 there is no length normalisation, so a longer doc with the same
    # single occurrence scores the same as a short one.
    corpus = [["x"], ["x", "filler", "filler", "filler"]]
    index = BM25Index(corpus, b=0.0)
    assert index.score(["x"], 0) == index.score(["x"], 1)


def test_metadata_properties():
    index = BM25Index([["a", "b"], ["c", "d", "e", "f"]])
    assert index.corpus_size == 2
    assert index.average_length == pytest.approx(3.0)


def test_bad_corpus_type_raises():
    with pytest.raises(TypeError):
        BM25Index("not a corpus")


def test_bad_document_token_raises():
    with pytest.raises(TypeError):
        BM25Index([["ok"], [1, 2]])


@pytest.mark.parametrize("kwargs", [{"k1": -1.0}, {"b": 1.5}, {"b": -0.1}])
def test_bad_parameters_raise_value_error(kwargs):
    with pytest.raises(ValueError):
        BM25Index(_corpus(), **kwargs)


def test_bad_top_k_raises():
    index = BM25Index(_corpus())
    with pytest.raises(ValueError):
        index.rank(["cat"], top_k=0)
    with pytest.raises(ValueError):
        index.rank(["cat"], top_k=True)


def test_score_out_of_range_raises():
    index = BM25Index(_corpus())
    with pytest.raises(IndexError):
        index.score(["cat"], 99)


def test_non_sequence_query_raises():
    index = BM25Index(_corpus())
    with pytest.raises(TypeError):
        index.rank("cat")
