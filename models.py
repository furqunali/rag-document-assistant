"""Shared data models for the RAG pipeline."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    index: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Chunk):
            return (self.text, self.source, self.index) == (other.text, other.source, other.index)
        if isinstance(other, str):
            return self.text == other
        return NotImplemented

    def strip(self, chars: str | None = None) -> str:
        return self.text.strip(chars)
