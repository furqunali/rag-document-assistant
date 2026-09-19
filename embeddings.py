"""Embedding implementations with a deterministic CPU fallback."""
from __future__ import annotations

import math
import re

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


class TfidfEmbedder:
    """Small, deterministic TF-IDF embedder requiring no model download."""
    name = "tfidf (pure-python fallback)"

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}
        self.idf: np.ndarray | None = None

    def fit(self, corpus: list[str]) -> "TfidfEmbedder":
        df: dict[str, int] = {}
        docs = [set(tokenize(doc)) for doc in corpus]
        for tokens in docs:
            for token in tokens:
                df[token] = df.get(token, 0) + 1
        self.vocab = {token: i for i, token in enumerate(sorted(df))}
        n = len(corpus)
        self.idf = np.zeros(len(self.vocab), dtype=np.float32)
        for token, index in self.vocab.items():
            self.idf[index] = math.log((1 + n) / (1 + df[token])) + 1.0
        return self

    def __call__(self, texts: list[str]) -> np.ndarray:
        if self.idf is None:
            raise RuntimeError("fit() must be called before embedding")
        vectors = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = tokenize(text)
            counts: dict[int, int] = {}
            for token in tokens:
                index = self.vocab.get(token)
                if index is not None:
                    counts[index] = counts.get(index, 0) + 1
            for index, count in counts.items():
                vectors[row, index] = (count / len(tokens)) * self.idf[index] if tokens else 0.0
        return vectors


def build_embedder(corpus: list[str]):
    """Prefer sentence-transformers, falling back to deterministic TF-IDF."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        class NeuralEmbedder:
            name = "sentence-transformers (all-MiniLM-L6-v2)"
            def fit(self, _: list[str]): return self
            def __call__(self, texts):
                return np.asarray(model.encode(texts, normalize_embeddings=False), dtype=np.float32)

        return NeuralEmbedder()
    except Exception:
        return TfidfEmbedder().fit(corpus)
