from dataclasses import asdict, is_dataclass

from models import Chunk


def test_chunk_is_dataclass_with_expected_fields():
    assert is_dataclass(Chunk)
    chunk = Chunk(text="hello", source="doc.md", index=2)
    assert asdict(chunk) == {"text": "hello", "source": "doc.md", "index": 2}


def test_chunk_preserves_source_metadata():
    chunk = Chunk(text="section", source="chapter-1", index=0)
    assert chunk.text == "section"
    assert chunk.source == "chapter-1"
    assert chunk.index == 0


def test_chunk_equality_uses_all_fields():
    first = Chunk("same", "doc", 1)
    second = Chunk("same", "doc", 1)
    different = Chunk("same", "doc", 2)
    assert first == second
    assert first != different
