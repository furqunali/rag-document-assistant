"""Tests for adjacent-chunk overlap analysis (chunk_overlap)."""
from __future__ import annotations

import pytest

from chunk_overlap import OverlapReport, analyze_overlap, flag_overlaps


def test_clean_suffix_prefix_overlap_is_measured():
    chunks = [
        ["a", "b", "c", "d"],
        ["c", "d", "e", "f"],
    ]
    report = analyze_overlap(chunks)[0]
    assert report.overlap_tokens == 2
    assert report.ratio == pytest.approx(0.5)


def test_no_overlap_flagged_too_little():
    chunks = [["a", "b", "c"], ["x", "y", "z"]]
    report = analyze_overlap(chunks)[0]
    assert report.overlap_tokens == 0
    assert report.ratio == 0.0
    assert report.status == "too_little"


def test_full_overlap_flagged_too_much():
    chunks = [["a", "b", "c"], ["a", "b", "c"]]
    report = analyze_overlap(chunks)[0]
    assert report.overlap_tokens == 3
    assert report.ratio == pytest.approx(1.0)
    assert report.status == "too_much"


def test_ratio_uses_shorter_chunk():
    # Overlap run is 2 tokens; shorter chunk has 2 tokens -> ratio 1.0.
    chunks = [["p", "q", "r", "s"], ["r", "s"]]
    report = analyze_overlap(chunks)[0]
    assert report.overlap_tokens == 2
    assert report.ratio == pytest.approx(1.0)


def test_status_ok_within_band():
    # 1 shared token out of shorter length 10 -> ratio 0.1, inside [0.05, 0.5].
    left = [str(i) for i in range(9)] + ["X"]
    right = ["X"] + [chr(97 + i) for i in range(9)]
    report = analyze_overlap([left, right])[0]
    assert report.ratio == pytest.approx(0.1)
    assert report.status == "ok"


def test_indices_and_ordering_for_three_chunks():
    chunks = [["a", "b"], ["b", "c"], ["c", "d"]]
    reports = analyze_overlap(chunks)
    assert [(r.left_index, r.right_index) for r in reports] == [(0, 1), (1, 2)]
    assert all(isinstance(r, OverlapReport) for r in reports)


def test_fewer_than_two_chunks_is_empty():
    assert analyze_overlap([]) == []
    assert analyze_overlap([["only", "one"]]) == []


def test_empty_chunk_gives_zero_ratio():
    report = analyze_overlap([["a", "b"], []])[0]
    assert report.overlap_tokens == 0
    assert report.ratio == 0.0
    assert report.status == "too_little"


def test_maximal_overlap_is_chosen():
    # A longer suffix/prefix run must win over a shorter incidental one.
    chunks = [["x", "a", "b", "c"], ["a", "b", "c", "x"]]
    report = analyze_overlap(chunks)[0]
    assert report.overlap_tokens == 3


def test_flag_overlaps_returns_only_problems():
    chunks = [
        ["a", "b", "c", "d", "e", "f", "g", "h", "i", "X"],  # -> next: 1/10 ok
        ["X", "b1", "c1", "d1", "e1", "f1", "g1", "h1", "i1", "j1"],
        ["z1", "z2", "z3"],  # no overlap with previous -> too_little
    ]
    flagged = flag_overlaps(chunks)
    assert all(r.status != "ok" for r in flagged)
    assert any(r.status == "too_little" for r in flagged)


def test_custom_band():
    chunks = [["a", "b", "c", "d"], ["c", "d", "e", "f"]]  # ratio 0.5
    # Tighten the ceiling so 0.5 is now "too_much".
    report = analyze_overlap(chunks, max_ratio=0.4)[0]
    assert report.status == "too_much"


def test_non_sequence_chunks_raises_type_error():
    with pytest.raises(TypeError):
        analyze_overlap("not a chunk list")


def test_string_chunk_raises_type_error():
    with pytest.raises(TypeError):
        analyze_overlap([["a", "b"], "bc"])


def test_non_string_token_raises_type_error():
    with pytest.raises(TypeError):
        analyze_overlap([["a", 1], ["a", "b"]])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_ratio": -0.1},
        {"max_ratio": 1.5},
        {"min_ratio": 0.8, "max_ratio": 0.2},
    ],
)
def test_bad_ratio_bounds_raise_value_error(kwargs):
    with pytest.raises(ValueError):
        analyze_overlap([["a", "b"], ["b", "c"]], **kwargs)
