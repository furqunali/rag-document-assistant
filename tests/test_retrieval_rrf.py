"""Tests for Reciprocal Rank Fusion (retrieval_rrf)."""
from __future__ import annotations

import pytest

from models import Chunk
from retrieval import Retrieved
from retrieval_rrf import rrf_fuse


def _item(text: str, index: int, source: str = "doc.md", score: float = 0.0) -> Retrieved:
    return Retrieved(Chunk(text=text, source=source, index=index), score)


def test_agreement_at_top_wins():
    # "a" is rank 0 in both lists; nothing else appears twice, so "a" fuses highest.
    list1 = [_item("a", 0), _item("b", 1), _item("c", 2)]
    list2 = [_item("a", 0), _item("d", 3), _item("e", 4)]
    fused = rrf_fuse([list1, list2], k=5)
    assert fused[0].chunk.text == "a"
    # "a" scored 2/(rrf_k+0); every other item scored once, so it must lead.
    assert fused[0].score == pytest.approx(2.0 / 60.0)


def test_consensus_beats_single_first_place():
    # "x" is first in list1 only. "y" is second in both lists.
    # Two rank-1 hits (2/61) outweigh one rank-0 hit (1/60).
    list1 = [_item("x", 0), _item("y", 1)]
    list2 = [_item("z", 2), _item("y", 1)]
    fused = rrf_fuse([list1, list2], k=3)
    assert fused[0].chunk.text == "y"
    assert fused[0].score == pytest.approx(2.0 / 61.0)


def test_rrf_k_changes_ranking():
    # A very small rrf_k sharpens the reward for the single top rank, letting a
    # lone first-place item overtake a doubly-second-place item.
    list1 = [_item("x", 0), _item("y", 1)]
    list2 = [_item("z", 2), _item("y", 1)]
    fused = rrf_fuse([list1, list2], k=3, rrf_k=0.5)
    # x: 1/0.5 = 2.0 ; y: 2/1.5 = 1.33 -> x now wins.
    assert fused[0].chunk.text == "x"


def test_score_is_sum_of_reciprocal_ranks():
    fused = rrf_fuse([[_item("a", 0), _item("b", 1)]], k=2, rrf_k=10.0)
    assert fused[0].score == pytest.approx(1.0 / 10.0)
    assert fused[1].score == pytest.approx(1.0 / 11.0)


def test_dedup_across_lists_returns_unique_chunks():
    dup = [_item("same", 0), _item("same", 0)]  # same chunk appears twice in one list
    fused = rrf_fuse([dup, [_item("same", 0)]], k=5)
    texts = [r.chunk.text for r in fused]
    assert texts.count("same") == 1  # collapsed to a single fused entry


def test_same_text_different_source_kept_separate():
    a = [_item("shared", 0, source="doc_a.md")]
    b = [_item("shared", 0, source="doc_b.md")]
    fused = rrf_fuse([a, b], k=5)
    assert len(fused) == 2
    assert {r.chunk.source for r in fused} == {"doc_a.md", "doc_b.md"}


def test_respects_k_limit():
    lst = [_item(t, i) for i, t in enumerate("abcdef")]
    assert len(rrf_fuse([lst], k=3)) == 3


def test_tie_break_is_deterministic_by_index():
    # Each item is rank 0 of its own list, so their fused scores are equal;
    # the lower chunk.index must then come first.
    fused = rrf_fuse([[_item("second", 5)], [_item("first", 2)]], k=2)
    assert fused[0].score == pytest.approx(fused[1].score)
    assert [r.chunk.index for r in fused] == [2, 5]


def test_empty_outer_returns_empty():
    assert rrf_fuse([], k=3) == []


def test_all_empty_lists_return_empty():
    assert rrf_fuse([[], []], k=3) == []


def test_returns_new_retrieved_objects():
    original = _item("a", 0, score=0.99)
    fused = rrf_fuse([[original]], k=1)
    assert fused[0] is not original          # a fresh Retrieved
    assert fused[0].chunk is original.chunk  # but reuses the underlying chunk
    assert fused[0].score != 0.99            # score is the RRF score, not the input


@pytest.mark.parametrize(
    "kwargs",
    [
        {"k": 0},                 # non-positive k
        {"k": -1},                # negative k
        {"k": True},              # bool is not a valid k
        {"k": 1.0},               # float is not a valid k
        {"rrf_k": 0.0},           # must be positive
        {"rrf_k": -5.0},          # must be positive
        {"rrf_k": float("inf")},  # must be finite
        {"rrf_k": float("nan")},  # must be a real number
    ],
)
def test_input_validation(kwargs):
    base = {"ranked_lists": [[_item("a", 0)]], "k": 2, "rrf_k": 60.0}
    base.update(kwargs)
    with pytest.raises(ValueError):
        rrf_fuse(**base)


def test_non_sequence_outer_rejected():
    with pytest.raises(ValueError):
        rrf_fuse(42, k=2)  # type: ignore[arg-type]


def test_string_outer_rejected():
    # A bare string is technically a sequence but never a list of rankings.
    with pytest.raises(ValueError):
        rrf_fuse("abc", k=2)  # type: ignore[arg-type]


def test_inner_not_sequence_rejected():
    with pytest.raises(ValueError):
        rrf_fuse([123], k=2)  # type: ignore[list-item]


def test_non_retrieved_item_rejected():
    with pytest.raises(ValueError):
        rrf_fuse([["not-a-retrieved"]], k=2)  # type: ignore[list-item]
