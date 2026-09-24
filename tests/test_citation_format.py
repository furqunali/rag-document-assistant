"""Tests for numbered citation formatting (citation_format)."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from citation_format import (
    Citation,
    build_citations,
    format_citations,
    format_reference_list,
)


@dataclass
class _Chunk:
    source: str
    text: str


def test_build_from_pairs_numbers_in_order():
    chunks = [("a.md", "first"), ("b.md", "second")]
    cites = build_citations(chunks)
    assert [(c.number, c.source, c.marker) for c in cites] == [
        (1, "a.md", "[1]"),
        (2, "b.md", "[2]"),
    ]


def test_dedupe_by_source_collapses_numbers():
    chunks = [("a.md", "one"), ("a.md", "two"), ("b.md", "three")]
    cites = build_citations(chunks, dedupe_by_source=True)
    assert len(cites) == 2
    assert cites[0].source == "a.md" and cites[0].text == "one"  # first text kept
    assert cites[1].number == 2 and cites[1].source == "b.md"


def test_no_dedupe_gives_every_chunk_a_number():
    chunks = [("a.md", "one"), ("a.md", "two")]
    cites = build_citations(chunks, dedupe_by_source=False)
    assert [c.number for c in cites] == [1, 2]


def test_build_from_mapping():
    chunks = [{"source": "s1", "text": "t1"}]
    cites = build_citations(chunks)
    assert cites[0].source == "s1" and cites[0].text == "t1"


def test_build_from_attribute_objects():
    chunks = [_Chunk("doc", "body")]
    cites = build_citations(chunks)
    assert cites[0].source == "doc" and cites[0].text == "body"


def test_custom_marker_template():
    cites = build_citations([("a", "x")], marker_template="({n})")
    assert cites[0].marker == "(1)"


def test_reference_list_rendering():
    cites = build_citations([("a.md", "hello"), ("b.md", "world")])
    block = format_reference_list(cites)
    assert block == "[1] a.md — hello\n[2] b.md — world"


def test_reference_list_truncates_text():
    cites = build_citations([("a.md", "abcdefghij")])
    block = format_reference_list(cites, max_text_chars=4)
    assert block == "[1] a.md — abcd…"


def test_empty_chunks_yield_no_citations_and_empty_block():
    cites = build_citations([])
    assert cites == []
    assert format_reference_list(cites) == ""


def test_format_citations_returns_pair():
    cites, block = format_citations([("a.md", "text one")])
    assert isinstance(cites, list) and isinstance(block, str)
    assert cites[0].marker == "[1]"
    assert block == "[1] a.md — text one"


def test_citations_are_frozen_records():
    cite = build_citations([("a", "b")])[0]
    assert isinstance(cite, Citation)
    with pytest.raises(Exception):
        cite.number = 99  # frozen dataclass


def test_bad_chunks_type_raises():
    with pytest.raises(TypeError):
        build_citations("not a list")


def test_bad_pair_shape_raises():
    with pytest.raises(ValueError):
        build_citations([("only-one-element",)])


def test_mapping_missing_keys_raises():
    with pytest.raises(ValueError):
        build_citations([{"source": "s"}])


def test_non_string_source_raises():
    with pytest.raises(TypeError):
        build_citations([(1, "text")])


def test_item_without_source_or_text_raises():
    with pytest.raises(TypeError):
        build_citations([object()])


def test_marker_template_without_placeholder_raises():
    with pytest.raises(ValueError):
        build_citations([("a", "b")], marker_template="[x]")


def test_bad_max_text_chars_raises():
    cites = build_citations([("a", "b")])
    with pytest.raises(ValueError):
        format_reference_list(cites, max_text_chars=0)
