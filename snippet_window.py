"""Pick the best fixed-length snippet window around a cluster of query terms.

A retrieved chunk is often far longer than the slice worth showing the user (or
handing back to the model as a quotation). The most useful slice is the window
where the query terms are *densest* — where the answer's supporting evidence is
packed together, not scattered.

This module slides a fixed-width window (measured in words) across a passage and
returns the window containing the most query-term hits. Matching is whole-word
and case-insensitive, mirroring :mod:`keyword_highlight`. Among windows tied on
hit count the earliest is chosen, so the result is deterministic and stable.

The module is pure: it takes the passage and terms as plain strings and returns
a :class:`Snippet`. There is no I/O, clock, or randomness. Word splitting is a
simple whitespace split, which keeps the reported word offsets meaningful to the
caller and independent of any external tokeniser.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Snippet:
    """The chosen snippet window.

    Attributes:
        text: the window's words re-joined with single spaces.
        start_word: index of the window's first word within the passage's
            whitespace-split word list (0-based).
        end_word: index just past the window's last word (a Python-style
            half-open bound, so ``words[start_word:end_word]`` is the window).
        hit_count: number of query-term occurrences inside the window.
    """

    text: str
    start_word: int
    end_word: int
    hit_count: int


def _hit_mask(words: list[str], terms: Sequence[str]) -> list[int]:
    """Return a 0/1 list marking which words are query-term hits (whole-word, ci)."""
    wanted = {term.strip().lower() for term in terms if term.strip()}
    return [1 if word.lower() in wanted else 0 for word in words]


def best_snippet(
    passage: str,
    terms: Sequence[str],
    *,
    window_words: int = 40,
) -> Snippet:
    """Return the fixed-width word window with the most query-term hits.

    Args:
        passage: the text to search within.
        terms: query terms whose density defines "best". Blank terms are
            ignored; matching is whole-word and case-insensitive.
        window_words: window width in words (a positive integer). If the passage
            has fewer words than this, the whole passage is the window.

    Returns:
        A :class:`Snippet`. For an empty passage this is an empty snippet at
        offset ``0``. When there are no usable terms (or no hits) the window is
        the passage's leading ``window_words`` words — a sensible default lead.

    Raises:
        TypeError: if ``passage`` is not a string or ``terms`` is not a sequence
            of strings.
        ValueError: if ``window_words`` is not a positive integer.
    """
    if not isinstance(passage, str):
        raise TypeError("passage must be a string")
    if isinstance(terms, (str, bytes)) or not isinstance(terms, Sequence):
        raise TypeError("terms must be a sequence of strings")
    if any(not isinstance(term, str) for term in terms):
        raise TypeError("each term must be a string")
    if not isinstance(window_words, int) or isinstance(window_words, bool) or window_words <= 0:
        raise ValueError("window_words must be a positive integer")

    words = passage.split()
    if not words:
        return Snippet("", 0, 0, 0)

    width = min(window_words, len(words))
    mask = _hit_mask(words, terms)

    # Prefix sums let each window's hit count be read in O(1); slide left-to-right
    # and keep the first window that achieves the maximum (deterministic ties).
    prefix = [0]
    for value in mask:
        prefix.append(prefix[-1] + value)

    best_start = 0
    best_hits = prefix[width] - prefix[0]
    for start in range(1, len(words) - width + 1):
        hits = prefix[start + width] - prefix[start]
        if hits > best_hits:
            best_hits = hits
            best_start = start

    end = best_start + width
    return Snippet(" ".join(words[best_start:end]), best_start, end, best_hits)
