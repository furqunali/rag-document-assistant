"""Nearest-neighbour retrieval primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from models import Chunk
Vector = np.ndarray
EmbedFn = Callable[[list[str]], np.ndarray]

def cosine_scores(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Return row-wise cosine scores with explicit shape validation."""
    matrix = np.asarray(matrix)
    vector = np.asarray(vector)
    if matrix.ndim != 2:
        raise ValueError("matrix must be a 2D array")
    if vector.ndim != 1:
        raise ValueError("vector must be a 1D array")
    if matrix.shape[1] != vector.shape[0]:
        raise ValueError("matrix and vector dimensions must match")
    denominator = (np.linalg.norm(matrix, axis=1) * np.linalg.norm(vector)) + 1e-9
    return (matrix @ vector) / denominator

@dataclass
class Retrieved:
    chunk: Chunk
    score: float

class Retriever:
    def __init__(self, chunks: list[Chunk], embed: EmbedFn | None = None) -> None:
        self.chunks = chunks
        self.embed = embed
        self.matrix: np.ndarray | None = None

    def query(self, question: str, k: int = 4) -> list[Retrieved]:
        question = (question or "").strip()
        if not question or k <= 0 or not self.chunks:
            return []
        if self.embed is None:
            raise ValueError("embed function is required when chunks are present")
        if self.matrix is None:
            self.matrix = self.embed([c.text for c in self.chunks])
        vector = self.embed([question])[0]
        scores = cosine_scores(self.matrix, vector)
        limit = min(k, len(self.chunks))
        order = sorted(range(len(self.chunks)), key=lambda i: (-float(scores[i]), self.chunks[i].index))
        return [Retrieved(self.chunks[i], float(scores[i])) for i in order[:limit]]
