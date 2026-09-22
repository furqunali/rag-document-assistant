"""Tests for budget-aware context compression (context_compression)."""
from __future__ import annotations

import pytest

from context_compression import compress_context, context_size
from models import Chunk
from retrieval import Retrieved


def _item(text: str, index: int, source: str = "doc.md", score: float = 0.0) -> Retrieved:
    return Retrieved(Chunk(text=text, source=source, index=index), score)


# ---------------------------------------------------------------------------
# context_size
# ---------------------------------------------------------------------------

def test_context_size_sums_characters():
    hits = [_item("abc", 0), _item("de", 1)]
    assert context_size(hits) == 5


def test_context_size_empty_is_zero():
    assert context_size([]) == 0


def test_context_size_custom_size_fn():
    hits = [_item("one two", 0), _item("three", 1)]
    word_count = lambda s: len(s.split())
    assert context_size(hits, size_fn=word_count) == 3


def test_context_size_rejects_non_list():
    with pytest.raises(ValueError):
        context_size("nope")  # type: ignore[arg-type]


def test_context_size_rejects_non_retrieved():
    with pytest.raises(ValueError):
        context_size([_item("a", 0), "b"])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# compress_context: whole-chunk packing
# ---------------------------------------------------------------------------

def test_everything_fits_returns_all_whole():
    hits = [_item("aaa", 0), _item("bbb", 1)]
    out = compress_context(hits, max_chars=100)
    assert [r.chunk.text for r in out] == ["aaa", "bbb"]
    assert context_size(out) == 6


def test_lowest_relevance_dropped_when_over_budget():
    # Budget fits the first two whole (6 chars) but not the third.
    hits = [_item("aaa", 0), _item("bbb", 1), _item("ccc", 2)]
    out = compress_context(hits, max_chars=6)
    assert [r.chunk.text for r in out] == ["aaa", "bbb"]


def test_top_chunks_kept_whole_are_same_object():
    hits = [_item("keep-me-whole", 0)]
    out = compress_context(hits, max_chars=100)
    assert out[0].chunk is hits[0].chunk  # untouched chunks reuse their Chunk
    assert out[0] is not hits[0]          # but a fresh Retrieved is returned


def test_score_is_preserved():
    hits = [_item("aaa", 0, score=0.87)]
    out = compress_context(hits, max_chars=100)
    assert out[0].score == pytest.approx(0.87)


# ---------------------------------------------------------------------------
# compress_context: boundary-chunk truncation
# ---------------------------------------------------------------------------

def test_boundary_chunk_is_truncated_to_fill_budget():
    hits = [_item("aaaa", 0), _item("bbbbbbbbbb", 1)]  # 4 + 10 chars
    out = compress_context(hits, max_chars=8, truncation_marker="~")
    assert len(out) == 2
    assert out[0].chunk.text == "aaaa"          # top passage kept whole
    # remaining budget = 4 chars: 3 body chars + 1 marker.
    assert out[1].chunk.text == "bbb~"
    assert context_size(out) == 8


def test_truncated_chunk_carries_source_and_index():
    hits = [_item("x" * 20, 7, source="report.md", score=0.5)]
    out = compress_context(hits, max_chars=5, truncation_marker="…")
    assert out[0].chunk.source == "report.md"
    assert out[0].chunk.index == 7
    assert out[0].score == pytest.approx(0.5)
    assert out[0].chunk.text.endswith("…")
    assert len(out[0].chunk.text) == 5


def test_sole_top_chunk_larger_than_budget_is_truncated():
    # The single most-relevant chunk exceeds the whole budget: trim in place.
    hits = [_item("abcdefghij", 0)]
    out = compress_context(hits, max_chars=4, truncation_marker="…")
    assert out[0].chunk.text == "abc…"


def test_marker_counts_toward_budget():
    hits = [_item("abcdefgh", 0)]
    out = compress_context(hits, max_chars=6, truncation_marker="[cut]")
    # marker is 5 chars, budget 6 -> only 1 body char survives.
    assert out[0].chunk.text == "a[cut]"
    assert context_size(out) == 6


def test_boundary_dropped_when_marker_cannot_fit():
    # Budget = 3, marker length 3 -> no room for any real content, so the
    # boundary chunk is dropped rather than emitting a marker-only fragment.
    hits = [_item("aa", 0), _item("bbbbb", 1)]
    out = compress_context(hits, max_chars=3, truncation_marker="---")
    assert [r.chunk.text for r in out] == ["aa"]


def test_min_trim_chars_drops_thin_boundary():
    hits = [_item("aaaa", 0), _item("bbbbbb", 1)]
    # remaining budget after "aaaa" = 4: with marker "~" only 3 body chars fit,
    # which is below min_trim_chars=5, so the boundary chunk is dropped.
    out = compress_context(hits, max_chars=8, truncation_marker="~", min_trim_chars=5)
    assert [r.chunk.text for r in out] == ["aaaa"]


def test_trailing_whitespace_stripped_before_marker():
    hits = [_item("ab      cd", 0)]  # spaces at the cut point
    out = compress_context(hits, max_chars=6, truncation_marker="…")
    # prefix "ab    " (6-1=5 chars) rstrips to "ab", then marker appended.
    assert out[0].chunk.text == "ab…"


def test_packing_stops_at_boundary_no_reordering():
    # A large boundary chunk must not be skipped in favour of a small later one:
    # priority order is preserved and packing halts at the boundary.
    hits = [_item("aaa", 0), _item("bbbbbbbb", 1), _item("cc", 2)]
    out = compress_context(hits, max_chars=6, truncation_marker="~")
    texts = [r.chunk.text for r in out]
    assert "cc" not in texts          # the tiny low-priority chunk never jumps ahead
    assert texts[0] == "aaa"
    assert texts[1] == "bb~"          # boundary trimmed to the 3 remaining chars


# ---------------------------------------------------------------------------
# compress_context: custom size function (token-style budgets)
# ---------------------------------------------------------------------------

def test_custom_size_fn_word_budget():
    word_count = lambda s: len(s.split())
    hits = [_item("one two three", 0), _item("four five", 1)]
    # Budget of 3 "words": first chunk (3 words) fits whole, second is boundary.
    out = compress_context(hits, max_chars=3, size_fn=word_count)
    assert out[0].chunk.text == "one two three"
    assert len(out) == 1  # no word budget remains for the second chunk


# ---------------------------------------------------------------------------
# compress_context: empty / no-op
# ---------------------------------------------------------------------------

def test_empty_hits_returns_empty():
    assert compress_context([], max_chars=100) == []


# ---------------------------------------------------------------------------
# compress_context: input validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_chars": 0},                    # non-positive
        {"max_chars": -1},                   # negative
        {"max_chars": True},                 # bool is not a valid int budget
        {"max_chars": 5.0},                  # float is not a valid budget
        {"min_trim_chars": 0},               # must be positive
        {"min_trim_chars": -3},              # must be positive
        {"min_trim_chars": True},            # bool rejected
        {"truncation_marker": 123},          # must be a string
        {"size_fn": 42},                     # must be callable
    ],
)
def test_input_validation(kwargs):
    base = {"hits": [_item("a", 0)], "max_chars": 10}
    base.update(kwargs)
    with pytest.raises(ValueError):
        compress_context(**base)


def test_rejects_non_list_hits():
    with pytest.raises(ValueError):
        compress_context("abc", max_chars=10)  # type: ignore[arg-type]


def test_rejects_non_retrieved_items():
    with pytest.raises(ValueError):
        compress_context([_item("a", 0), "b"], max_chars=10)  # type: ignore[list-item]
