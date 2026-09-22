import pytest

from chunking import chunk_text, normalize_text, split_sentences


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  one\\n two\\t three  ") == "one two three"


def test_normalize_text_handles_empty_input():
    assert normalize_text("   ") == ""


def test_split_sentences_handles_empty_text():
    assert split_sentences("") == []


def test_chunk_text_handles_empty_text():
    assert chunk_text("", chunk_size=100, overlap=0) == []


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("one two", chunk_size=2, overlap=2)


def test_chunk_text_returns_source_metadata():
    chunks = chunk_text("One. Two.", chunk_size=10, overlap=0, source="notes")
    assert chunks
    assert chunks[0].source == "notes"
