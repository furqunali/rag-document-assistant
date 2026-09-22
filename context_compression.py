"""Budget-aware context compression for retrieved chunks.

A language model's context window is finite, so the passages returned by
retrieval (:class:`retrieval.Retrieved`) frequently add up to more text than a
prompt can afford. Naively concatenating everything overflows the budget;
naively dropping the tail throws away partially-useful passages.

This module packs retrieved chunks into a fixed size *budget* while honouring
one rule: **the highest-relevance passages are kept whole**. Working through the
hits in priority order (retrievers already return them best-first), it admits
each chunk whole for as long as the running total fits. The first chunk that
would overflow becomes the *boundary* chunk: instead of being dropped outright
it is truncated to fill whatever budget remains, so no space is wasted, and
packing then stops. Everything admitted before it is untouched.

The one unavoidable exception is a single top chunk that is larger than the whole
budget: it is truncated in place, because there is nothing more relevant to keep.

The budget is measured in characters by default, but any monotonic size function
(``size_fn``) — for example a tokenizer's token count — can be supplied, in which
case both the fit test and the truncation cut are computed in that unit. The
module consumes and returns :class:`retrieval.Retrieved` items so it drops
straight into the pipeline alongside :mod:`retrieval_mmr` and :mod:`retrieval_rrf`.
"""
from __future__ import annotations

from collections.abc import Callable

from models import Chunk
from retrieval import Retrieved

SizeFn = Callable[[str], int]


def _validate_size_fn(size_fn: SizeFn | None) -> SizeFn:
    if size_fn is None:
        return len
    if not callable(size_fn):
        raise ValueError("size_fn must be callable or None")  # noqa: TRY004
    return size_fn


def context_size(hits: list[Retrieved], size_fn: SizeFn | None = None) -> int:
    """Return the total size of every chunk's text in ``hits``.

    Useful for deciding whether compression is needed before calling
    :func:`compress_context`.

    Args:
        hits: retrieved items whose chunk text is measured.
        size_fn: measures one string; defaults to :func:`len` (characters).

    Raises:
        ValueError: if ``hits`` is not a list of :class:`retrieval.Retrieved`,
            or ``size_fn`` is not callable.
    """
    if not isinstance(hits, list):
        raise ValueError("hits must be a list of Retrieved")  # noqa: TRY004
    measure = _validate_size_fn(size_fn)
    total = 0
    for hit in hits:
        if not isinstance(hit, Retrieved):
            raise ValueError("hits must contain Retrieved items")  # noqa: TRY004
        total += measure(hit.chunk.text)
    return total


def _truncate_to_budget(
    text: str,
    budget: int,
    marker: str,
    measure: SizeFn,
    min_body_chars: int,
) -> str | None:
    """Return the longest ``prefix + marker`` of ``text`` measuring ``<= budget``.

    The cut point is found by binary search over the character length of the
    prefix, relying on ``measure`` being monotonic non-decreasing in prefix
    length (true for character counts and standard tokenizers). Trailing
    whitespace is stripped from the prefix so the marker does not dangle after a
    space. Returns ``None`` when no prefix leaves at least ``min_body_chars`` of
    real content within ``budget``.
    """
    if measure(marker) >= budget:
        return None  # not even the marker fits, let alone any content

    # Largest prefix length L (in characters) with measure(text[:L] + marker) <= budget.
    lo, hi, best = 1, len(text), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if measure(text[:mid] + marker) <= budget:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best == 0:
        return None

    prefix = text[:best].rstrip()
    if len(prefix) < min_body_chars:
        return None
    candidate = prefix + marker
    # rstrip only shrinks the string, so the budget still holds; guard anyway.
    if measure(candidate) > budget:
        return None
    return candidate


def compress_context(
    hits: list[Retrieved],
    max_chars: int,
    *,
    truncation_marker: str = "…",
    min_trim_chars: int = 1,
    size_fn: SizeFn | None = None,
) -> list[Retrieved]:
    """Pack ``hits`` into ``max_chars`` of budget, keeping top passages whole.

    Args:
        hits: retrieved items ordered most-important-first (as produced by
            :mod:`retrieval`, :mod:`retrieval_mmr` or :mod:`retrieval_rrf`).
        max_chars: the size budget. Characters by default, or the unit of
            ``size_fn`` when one is given. Must be a positive integer.
        truncation_marker: appended to the boundary chunk when it is trimmed to
            signal elision. Counts toward the budget.
        min_trim_chars: the boundary chunk is only included when at least this
            many characters of real content survive the trim; otherwise it is
            dropped. Must be a positive integer.
        size_fn: measures one string; defaults to :func:`len` (characters). Must
            be monotonic non-decreasing in prefix length for the cut to be exact.

    Returns:
        A new list of :class:`retrieval.Retrieved` whose total measured text is
        ``<= max_chars``. Whole chunks reuse their original :class:`models.Chunk`;
        a truncated boundary chunk is a fresh :class:`models.Chunk` carrying the
        same ``source`` and ``index`` and the original relevance ``score``.

    Raises:
        ValueError: if ``hits`` is not a list of :class:`retrieval.Retrieved`,
            ``max_chars`` or ``min_trim_chars`` is not a positive integer,
            ``truncation_marker`` is not a string, or ``size_fn`` is not callable.
    """
    if not isinstance(hits, list):
        raise ValueError("hits must be a list of Retrieved")  # noqa: TRY004
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")
    if not isinstance(truncation_marker, str):
        raise ValueError("truncation_marker must be a string")  # noqa: TRY004
    if not isinstance(min_trim_chars, int) or isinstance(min_trim_chars, bool) or min_trim_chars <= 0:
        raise ValueError("min_trim_chars must be a positive integer")
    measure = _validate_size_fn(size_fn)

    for hit in hits:
        if not isinstance(hit, Retrieved):
            raise ValueError("hits must contain Retrieved items")  # noqa: TRY004
    if not hits:
        return []

    result: list[Retrieved] = []
    used = 0
    for hit in hits:
        remaining = max_chars - used
        if remaining <= 0:
            break
        size = measure(hit.chunk.text)
        if size <= remaining:
            result.append(Retrieved(hit.chunk, hit.score))
            used += size
            continue
        # Boundary chunk: trim it to fill the remaining budget, then stop so that
        # no lower-priority chunk can jump ahead of this partially-included one.
        truncated = _truncate_to_budget(
            hit.chunk.text, remaining, truncation_marker, measure, min_trim_chars
        )
        if truncated is not None:
            trimmed_chunk = Chunk(text=truncated, source=hit.chunk.source, index=hit.chunk.index)
            result.append(Retrieved(trimmed_chunk, hit.score))
        break

    return result
