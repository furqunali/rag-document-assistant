"""Nearest-neighbour retrieval primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from models import Chunk
Vector = np.ndarray
EmbedFn = Callable[[list[str]], np.ndarray]

def cosine_scores(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    denominator = (np.linalg.norm(matrix, axis=1) * np.linalg.norm(vector)) + 1e-9
    return (matrix @ vector) / denominator

@dataclass
class Retrieved:
    chunk: Chunk
    score: float

class Retriever:
    """Pre-computes document vectors and returns deterministic top-k matches."""
    def __init__(self, chunks: list[Chunk], embed: EmbedFn) -> None:
        self.chunks = chunks
        self.embed = embed
        self.matrix = embed([c.text for c in chunks]) if chunks else np.zeros((0, 1))

    def query(self, question: str, k: int = 4) -> list[Retrieved]:
        question = (question or "").strip()
        if not question or not self.chunks or k <= 0:
            return []
        vector = self.embed([question])[0]
        scores = cosine_scores(self.matrix, vector)
        limit = min(k, len(self.chunks))
        order = sorted(range(len(self.chunks)), key=lambda i: (-float(scores[i]), self.chunks[i].index))
        return [Retrieved(self.chunks[i], float(scores[i])) for i in order[:limit]]
