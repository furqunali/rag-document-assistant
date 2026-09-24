"""Tests for best-snippet-window selection (snippet_window)."""
from __future__ import annotations

import pytest

from snippet_window import Snippet, best_snippet


def test_picks_window_around_dense_cluster():
    passage = "alpha beta gamma delta cat cat cat epsilon zeta eta"
    snip = best_snippet(passage, ["cat"], window_words=3)
    assert snip.text == "cat cat cat"
    assert snip.hit_count == 3
    assert snip.start_word == 4
    assert snip.end_word == 7


def test_returns_snippet_instance():
    snip = best_snippet("one two three", ["two"], window_words=2)
    assert isinstance(snip, Snippet)


def test_window_larger_than_passage_returns_whole_passage():
    snip = best_snippet("only three words", ["words"], window_words=50)
    assert snip.text == "only three words"
    assert snip.start_word == 0
    assert snip.end_word == 3
    assert snip.hit_count == 1


def test_case_insensitive_whole_word_hits():
    passage = "Cat category CAT"
    snip = best_snippet(passage, ["cat"], window_words=3)
    # "Cat" and "CAT" count (whole word, case-insensitive); "category" does not.
    assert snip.hit_count == 2


def test_ties_prefer_earliest_window():
    # Two equally dense windows; the earlier one must win.
    passage = "cat a b c cat d e f"
    snip = best_snippet(passage, ["cat"], window_words=1)
    assert snip.start_word == 0
    assert snip.text == "cat"


def test_no_terms_returns_leading_window():
    passage = "a b c d e f"
    snip = best_snippet(passage, [], window_words=3)
    assert snip.text == "a b c"
    assert snip.hit_count == 0


def test_no_hits_returns_leading_window():
    passage = "a b c d e f"
    snip = best_snippet(passage, ["zzz"], window_words=2)
    assert snip.start_word == 0
    assert snip.text == "a b"
    assert snip.hit_count == 0


def test_empty_passage_returns_empty_snippet():
    snip = best_snippet("", ["cat"], window_words=5)
    assert snip.text == ""
    assert snip.start_word == 0
    assert snip.end_word == 0
    assert snip.hit_count == 0


def test_whitespace_only_passage_is_empty():
    snip = best_snippet("   \t \n ", ["cat"], window_words=5)
    assert snip.text == ""
    assert snip.hit_count == 0


def test_multiple_terms_counted():
    passage = "red green blue red green blue"
    snip = best_snippet(passage, ["red", "blue"], window_words=3)
    assert snip.hit_count == 2


def test_window_slides_to_best_position():
    passage = "x x x hit x x hit hit x"
    snip = best_snippet(passage, ["hit"], window_words=3)
    assert snip.text == "x hit hit"
    assert snip.hit_count == 2


def test_bad_passage_type_raises():
    with pytest.raises(TypeError):
        best_snippet(123, ["cat"])


def test_bad_terms_type_raises():
    with pytest.raises(TypeError):
        best_snippet("text here", "cat")


def test_non_string_term_raises():
    with pytest.raises(TypeError):
        best_snippet("text here", ["ok", 3])


@pytest.mark.parametrize("bad", [0, -1, True, 2.5])
def test_bad_window_words_raises(bad):
    with pytest.raises(ValueError):
        best_snippet("some text", ["text"], window_words=bad)
