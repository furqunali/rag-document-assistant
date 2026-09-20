from models import Chunk

def test_chunk_preserves_text_and_source():
    chunk = Chunk("content", "manual.pdf", 4)
    assert chunk.text == "content"
    assert chunk.source == "manual.pdf"

def test_chunk_preserves_index_order():
    first = Chunk("one", "doc", 0)
    second = Chunk("two", "doc", 1)
    assert first.index < second.index

def test_chunk_equality_distinguishes_index():
    assert Chunk("same", "doc", 0) != Chunk("same", "doc", 1)
