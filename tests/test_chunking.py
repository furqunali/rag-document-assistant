from chunking import chunk_text, normalize_text


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  one\n\n two  ") == "one two"


def test_chunk_text_returns_empty_for_blank_input():
    assert chunk_text("   ", chunk_size=20) == []


def test_chunk_text_preserves_short_text():
    assert chunk_text("robotics basics", chunk_size=100) == ["robotics basics"]


def test_chunk_text_never_returns_empty_chunks():
    chunks = chunk_text("alpha beta gamma delta", chunk_size=10)
    assert chunks
    assert all(chunk.strip() for chunk in chunks)
