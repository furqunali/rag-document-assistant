"""Configuration primitives for the RAG pipeline."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 600
    overlap: int = 100

    def validate(self) -> "ChunkConfig":
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0:
            raise ValueError("overlap must be non-negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        return self


@dataclass(frozen=True)
class AnswerConfig:
    threshold: float = 0.15

    def validate(self) -> "AnswerConfig":
        import math
        if not math.isfinite(self.threshold) or self.threshold < 0:
            raise ValueError("threshold must be a finite, non-negative number")
        return self
