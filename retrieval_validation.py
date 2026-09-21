"""Integrity checks for retrieval results before answer generation."""
from __future__ import annotations

from math import isfinite
from typing import Iterable

from retrieval import Retrieved

def validate_results(results: Iterable[Retrieved]) -> tuple[str, ...]:
    issues: list[str] = []
    seen: set[tuple[str, int]] = set()
    for position, result in enumerate(results):
        if not isinstance(result.score, (int, float)) or not isfinite(float(result.score)):
            issues.append(f"result {position} has non-finite score")
        if not result.chunk.text.strip():
            issues.append(f"result {position} has empty chunk text")
        key = (result.chunk.source, result.chunk.index)
        if key in seen:
            issues.append(f"result {position} duplicates chunk identity")
        seen.add(key)
    return tuple(dict.fromkeys(issues))

def is_valid_results(results: Iterable[Retrieved]) -> bool:
    return not validate_results(results)
