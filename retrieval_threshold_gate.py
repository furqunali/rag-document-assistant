"""Deterministic evidence threshold gate for retrieved results."""
from __future__ import annotations
from dataclasses import dataclass
from retrieval import Retrieved

@dataclass(frozen=True)
class RetrievalGate:
    results: int
    qualifying: int
    passed: bool

def evaluate_retrieval_gate(results: list[Retrieved], *, threshold: float = 0.5, minimum_results: int = 1) -> RetrievalGate:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if minimum_results < 0:
        raise ValueError("minimum_results must be non-negative")
    for item in results:
        if not isinstance(item, Retrieved):
            raise TypeError("results must contain Retrieved values")
    qualifying = sum(float(item.score) >= threshold for item in results)
    return RetrievalGate(len(results), qualifying, qualifying >= minimum_results)
