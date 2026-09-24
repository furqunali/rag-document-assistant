"""Tests for query-term highlighting (keyword_highlight)."""
from __future__ import annotations

import pytest

from keyword_highlight import count_highlights, highlight_terms


def test_basic_highlight_default_markers():
    assert highlight_terms("the cat sat", ["cat"]) == "the **cat** sat"


def test_case_insensitive_preserves_original_case():
    assert highlight_terms("The Cat and a CAT", ["cat"]) == "The **Cat** and a **CAT**"


def test_whole_word_only():
    # "cat" must not match inside "category".
    assert highlight_terms("a category of cat", ["cat"]) == "a category of **cat**"


def test_multiple_terms():
    out = highlight_terms("red fox blue fox", ["red", "blue"])
    assert out == "**red** fox **blue** fox"


def test_custom_markers():
    out = highlight_terms("find me", ["me"], prefix="<mark>", suffix="</mark>")
    assert out == "find <mark>me</mark>"


def test_no_match_returns_unchanged():
    assert highlight_terms("nothing here", ["absent"]) == "nothing here"


def test_blank_and_duplicate_terms_ignored():
    out = highlight_terms("cat cat", ["cat", "  ", "CAT"])
    assert out == "**cat** **cat**"


def test_longer_term_wins_at_shared_position():
    # "new york" should be preferred over "york" when both are provided.
    out = highlight_terms("new york city", ["york", "new york"])
    assert out == "**new york** city"


def test_empty_text_returns_empty():
    assert highlight_terms("", ["cat"]) == ""


def test_empty_terms_returns_unchanged():
    assert highlight_terms("some text", []) == "some text"


def test_term_with_regex_metacharacters_is_literal():
    # A term containing regex specials must be escaped, not interpreted.
    assert highlight_terms("a+b and c", ["a+b"]) == "**a+b** and c"


def test_count_highlights_matches_render():
    text = "cat CAT category cat"
    assert count_highlights(text, ["cat"]) == 3


def test_count_zero_when_no_terms():
    assert count_highlights("cat", []) == 0


def test_bad_text_type_raises():
    with pytest.raises(TypeError):
        highlight_terms(123, ["x"])


def test_bad_terms_type_raises():
    with pytest.raises(TypeError):
        highlight_terms("text", "cat")  # str, not a sequence of terms


def test_non_string_term_raises():
    with pytest.raises(TypeError):
        highlight_terms("text", ["ok", 5])


def test_bad_marker_type_raises():
    with pytest.raises(TypeError):
        highlight_terms("text", ["x"], prefix=1)
