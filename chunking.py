"""Document chunking utilities used by the RAG pipeline."""
from __future__ import annotations
import re
from rag_config import ChunkConfig
from models import Chunk

def normalize_text(text: str) -> str:
    value = (text or "").replace("\\n", " ").replace("\\t", " ")
    value = value.replace("\n", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", value).strip()

def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    return re.split(r"(?<=[.!?])\s+", normalized) if normalized else []

def chunk_text(text: str, source: str = "", chunk_size: int = 600, overlap: int = 0) -> list[Chunk]:
    config = ChunkConfig(chunk_size, overlap).validate()
    chunks: list[Chunk] = []
    buffer = ""
    index = 0
    for sentence in split_sentences(text):
        if len(buffer) + len(sentence) + 1 <= config.chunk_size or not buffer:
            buffer = (buffer + " " + sentence).strip()
            continue
        chunks.append(Chunk(buffer, source, index))
        index += 1
        tail = buffer[-config.overlap:] if config.overlap else ""
        buffer = (tail + " " + sentence).strip()
    if buffer:
        chunks.append(Chunk(buffer, source, index))
    return chunks
