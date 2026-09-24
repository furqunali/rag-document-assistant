"""Adjacent-chunk token-overlap analysis for the RAG ingestion pipeline.

When a document is split into chunks, a small *overlap* between neighbouring
chunks is deliberate: it stops a fact that straddles a boundary from being torn
in half, so either chunk can answer a question about it. But the overlap has to
be in a healthy band. Too little (or none) and boundary facts fall through the
cracks; too much and the index bloats with near-duplicate text that wastes the
model's context window and skews retrieval toward the repeated material.

This module measures the overlap between each pair of adjacent chunks and flags
the ones that fall outside a configured band. It is deterministic and pure: it
operates on plain lists of already-tokenised chunks (``list[list[str]]``) that
the caller passes in — no tokeniser, embeddings, clock, or randomness is
involved.

Overlap is measured as the length of the longest run of tokens that is both a
*suffix* of the earlier chunk and a *prefix* of the later chunk — exactly the
kind of overlap a sliding-window chunker produces. The reported ``ratio`` is
that run length divided by the token count of the shorter of the two chunks, so
it lands in ``[0, 1]`` regardless of the chunks' absolute sizes.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class OverlapReport:
    """The overlap between one adjacent pair of chunks.

    Attributes:
        left_index: position of the earlier chunk in the input list.
        right_index: position of the later chunk (always ``left_index + 1``).
        overlap_tokens: length of the longest suffix/prefix token run shared by
            the two chunks.
        ratio: ``overlap_tokens`` divided by the length of the shorter chunk,
            rounded to 6 decimals; ``0.0`` when either chunk is empty.
        status: one of ``"ok"``, ``"too_little"`` or ``"too_much"``.
    """

    left_index: int
    right_index: int
    overlap_tokens: int
    ratio: float
    status: str


def _suffix_prefix_overlap(left: Sequence[str], right: Sequence[str]) -> int:
    """Return the longest run that is a suffix of ``left`` and a prefix of ``right``.

    The search is greedy from the longest possible run downward, so the result
    is the *maximal* overlap. Complexity is ``O(min(len)^2)`` in the worst case,
    which is fine for the modest chunk sizes used in practice.
    """
    max_len = min(len(left), len(right))
    for length in range(max_len, 0, -1):
        if list(left[-length:]) == list(right[:length]):
            return length
    return 0


def analyze_overlap(
    chunks: Sequence[Sequence[str]],
    *,
    min_ratio: float = 0.05,
    max_ratio: float = 0.5,
) -> list[OverlapReport]:
    """Report the token overlap for every adjacent pair of chunks.

    Args:
        chunks: an ordered sequence of tokenised chunks. Each chunk is a
            sequence of string tokens (e.g. ``["the", "cat", "sat"]``). Fewer
            than two chunks yields an empty report.
        min_ratio: lower bound of the healthy overlap band, in ``[0, 1]``. A
            pair whose ratio is strictly below this is flagged ``"too_little"``.
        max_ratio: upper bound of the healthy overlap band, in ``[0, 1]`` and
            not less than ``min_ratio``. A pair whose ratio is strictly above
            this is flagged ``"too_much"``.

    Returns:
        One :class:`OverlapReport` per adjacent pair, in document order.

    Raises:
        TypeError: if ``chunks`` is a string/bytes, if any chunk is not a
            sequence, or if any token is not a string.
        ValueError: if the ratio bounds are outside ``[0, 1]`` or inverted.
    """
    if isinstance(chunks, (str, bytes)) or not isinstance(chunks, Sequence):
        raise TypeError("chunks must be a sequence of tokenised chunks")
    min_ratio = float(min_ratio)
    max_ratio = float(max_ratio)
    if not 0.0 <= min_ratio <= 1.0 or not 0.0 <= max_ratio <= 1.0:
        raise ValueError("min_ratio and max_ratio must be within [0, 1]")
    if min_ratio > max_ratio:
        raise ValueError("min_ratio must not exceed max_ratio")

    normalised: list[list[str]] = []
    for chunk in chunks:
        if isinstance(chunk, (str, bytes)) or not isinstance(chunk, Sequence):
            raise TypeError("each chunk must be a sequence of string tokens")
        tokens = list(chunk)
        if any(not isinstance(token, str) for token in tokens):
            raise TypeError("chunk tokens must be strings")
        normalised.append(tokens)

    reports: list[OverlapReport] = []
    for i in range(len(normalised) - 1):
        left, right = normalised[i], normalised[i + 1]
        overlap = _suffix_prefix_overlap(left, right)
        shorter = min(len(left), len(right))
        ratio = round(overlap / shorter, 6) if shorter else 0.0
        if ratio < min_ratio:
            status = "too_little"
        elif ratio > max_ratio:
            status = "too_much"
        else:
            status = "ok"
        reports.append(OverlapReport(i, i + 1, overlap, ratio, status))
    return reports


def flag_overlaps(
    chunks: Sequence[Sequence[str]],
    *,
    min_ratio: float = 0.05,
    max_ratio: float = 0.5,
) -> list[OverlapReport]:
    """Return only the pairs whose overlap falls outside the healthy band.

    A thin convenience wrapper over :func:`analyze_overlap` for callers that
    only care about the problems. Arguments and validation are identical.
    """
    return [
        report
        for report in analyze_overlap(chunks, min_ratio=min_ratio, max_ratio=max_ratio)
        if report.status != "ok"
    ]
