"""Deterministic metadata for local RAG query runs."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class QueryMetadata:
    question: str
    top_k: int
    threshold: float
    chunk_count: int

def build_query_metadata(question: str, top_k: int, threshold: float, chunk_count: int) -> QueryMetadata:
    if not question.strip(): raise ValueError("question must not be empty")
    if top_k < 1: raise ValueError("top_k must be positive")
    if threshold < 0: raise ValueError("threshold must be non-negative")
    if chunk_count < 0: raise ValueError("chunk_count must be non-negative")
    return QueryMetadata(question.strip(), top_k, round(threshold, 6), chunk_count)
