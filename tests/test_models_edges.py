from dataclasses import asdict, is_dataclass

from models import Chunk


def test_chunk_is_dataclass():
    assert is_dataclass(Chunk)

def test_chunk_fields_are_serializable():
    chunk = Chunk("text", "source", 3)
    assert asdict(chunk) == {"text": "text", "source": "source", "index": 3}

def test_chunk_equality_uses_all_fields():
    assert Chunk("text", "source", 1) == Chunk("text", "source", 1)
    assert Chunk("text", "source", 1) != Chunk("other", "source", 1)

def test_chunk_index_accepts_zero():
    assert Chunk("text", "source", 0).index == 0
