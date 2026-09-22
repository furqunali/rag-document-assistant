"""Nearest-neighbour retrieval primitives."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from models import Chunk

Vector = np.ndarray
EmbedFn = Callable[[list[str]], np.ndarray]


def cosine_scores(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Return row-wise cosine scores with explicit shape and finite-value validation."""
    matrix = np.asarray(matrix)
    vector = np.asarray(vector)
    if matrix.ndim != 2:
        raise ValueError("matrix must be a 2D array")
    if vector.ndim != 1:
        raise ValueError("vector must be a 1D array")
    if matrix.shape[1] != vector.shape[0]:
        raise ValueError("matrix and vector dimensions must match")
    if not np.isfinite(matrix).all() or not np.isfinite(vector).all():
        raise ValueError("matrix and vector must contain only finite values")
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
        if question is None:
            question = ""
        elif not isinstance(question, str):
            raise ValueError("question must be a string")
        question = question.strip()
        if not isinstance(k, int) or isinstance(k, bool):
            raise ValueError("k must be an integer")
        if not question or k <= 0 or not self.chunks:
            return []
        if self.embed is None:
            raise ValueError("embed function is required when chunks are present")
        if self.matrix is None:
            matrix = np.asarray(self.embed([c.text for c in self.chunks]))
            if matrix.ndim != 2:
                raise ValueError("embedding matrix must be 2D")
            if matrix.shape[0] != len(self.chunks):
                raise ValueError("embedding matrix row count must match chunks")
            if not np.isfinite(matrix).all():
                raise ValueError("embedding matrix must contain only finite values")
            self.matrix = matrix
        query_embeddings = np.asarray(self.embed([question]))
        if query_embeddings.ndim != 2 or query_embeddings.shape[0] != 1:
            raise ValueError("query embedding must contain exactly one vector")
        vector = query_embeddings[0]
        scores = cosine_scores(self.matrix, vector)
        limit = min(k, len(self.chunks))
        order = sorted(
            range(len(self.chunks)),
            key=lambda i: (-float(scores[i]), self.chunks[i].index),
        )
        return [Retrieved(self.chunks[i], float(scores[i])) for i in order[:limit]]
