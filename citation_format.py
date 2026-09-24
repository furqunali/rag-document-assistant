"""Turn retrieved chunks into numbered citations with inline reference markers.

A grounded RAG answer should point at its evidence. This module takes the
chunks a retriever returned — each carrying a ``source`` and its ``text`` — and
assigns them stable citation numbers, produces the inline markers (``[1]``,
``[2]`` …) an answer can splice in next to a claim, and renders the numbered
reference block that goes at the foot of the answer.

By default chunks that share a ``source`` collapse onto a single citation
number, which is what a reader expects from a bibliography; set
``dedupe_by_source=False`` to give every chunk its own number instead. Numbering
follows first appearance, so the output is deterministic.

The module is self-contained and pure: it reads only ``source``/``text`` off
each item (which may be a ``(source, text)`` pair, a mapping with those keys, or
any object exposing them as attributes), and it performs no I/O, clock reads, or
randomness.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    """A single numbered citation.

    Attributes:
        number: 1-based citation number.
        source: the source identifier the citation points at.
        text: representative text for the citation (the first chunk's text when
            several chunks share a source).
        marker: the rendered inline marker, e.g. ``"[1]"``.
    """

    number: int
    source: str
    text: str
    marker: str


def _extract(item: object) -> tuple[str, str]:
    """Pull ``(source, text)`` out of a pair, mapping, or attribute-bearing object."""
    if isinstance(item, Mapping):
        if "source" not in item or "text" not in item:
            raise ValueError("mapping items must have 'source' and 'text' keys")
        source, text = item["source"], item["text"]
    elif isinstance(item, (tuple, list)):
        if len(item) != 2:
            raise ValueError("pair items must be exactly (source, text)")
        source, text = item[0], item[1]
    elif hasattr(item, "source") and hasattr(item, "text"):
        source, text = item.source, item.text
    else:
        raise TypeError("each chunk must be a (source, text) pair, mapping, or have .source/.text")
    if not isinstance(source, str) or not isinstance(text, str):
        raise TypeError("source and text must be strings")
    return source, text


def build_citations(
    chunks: Sequence[object],
    *,
    dedupe_by_source: bool = True,
    marker_template: str = "[{n}]",
) -> list[Citation]:
    """Assign citation numbers to ``chunks`` in order of first appearance.

    Args:
        chunks: retrieved items, each yielding a ``source`` and ``text`` (see
            module docstring for accepted shapes).
        dedupe_by_source: when ``True`` (default) chunks sharing a ``source`` get
            the same number; when ``False`` every chunk gets its own number.
        marker_template: format string for the inline marker; must contain the
            ``{n}`` placeholder (e.g. ``"[{n}]"`` or ``"({n})"``).

    Returns:
        One :class:`Citation` per distinct citation, ordered by number.

    Raises:
        TypeError: if ``chunks`` is not a (non-string) sequence, or an item's
            ``source``/``text`` are not strings.
        ValueError: if an item has the wrong shape or ``marker_template`` lacks
            a working ``{n}`` placeholder.
    """
    if isinstance(chunks, (str, bytes)) or not isinstance(chunks, Sequence):
        raise TypeError("chunks must be a sequence of retrieved items")
    if not isinstance(marker_template, str):
        raise TypeError("marker_template must be a string")
    try:
        probe = marker_template.format(n=1)
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError("marker_template must contain a '{n}' placeholder") from exc
    if probe == marker_template:
        raise ValueError("marker_template must contain a '{n}' placeholder")

    citations: list[Citation] = []
    source_to_number: dict[str, int] = {}
    for item in chunks:
        source, text = _extract(item)
        if dedupe_by_source and source in source_to_number:
            continue
        number = len(citations) + 1
        source_to_number[source] = number
        citations.append(
            Citation(number, source, text, marker_template.format(n=number))
        )
    return citations


def format_reference_list(
    citations: Sequence[Citation],
    *,
    max_text_chars: int | None = None,
) -> str:
    """Render citations as a numbered reference block, one per line.

    Each line looks like ``"[1] source — text"``. Lines are ordered by the
    citations' numbers.

    Args:
        citations: citations to render (typically from :func:`build_citations`).
        max_text_chars: if given (a positive integer), truncate each citation's
            text to this many characters, appending an ellipsis when trimmed.

    Returns:
        The reference block as a single string (``""`` when there are no
        citations).

    Raises:
        TypeError: if ``citations`` contains a non-:class:`Citation`.
        ValueError: if ``max_text_chars`` is given but not a positive integer.
    """
    if isinstance(citations, (str, bytes)) or not isinstance(citations, Sequence):
        raise TypeError("citations must be a sequence of Citation")
    if max_text_chars is not None and (
        not isinstance(max_text_chars, int)
        or isinstance(max_text_chars, bool)
        or max_text_chars <= 0
    ):
        raise ValueError("max_text_chars must be a positive integer or None")

    lines: list[str] = []
    for citation in sorted(citations, key=lambda c: c.number):
        if not isinstance(citation, Citation):
            raise TypeError("citations must be a sequence of Citation")
        text = citation.text
        if max_text_chars is not None and len(text) > max_text_chars:
            text = text[:max_text_chars].rstrip() + "…"
        lines.append(f"{citation.marker} {citation.source} — {text}")
    return "\n".join(lines)


def format_citations(
    chunks: Sequence[object],
    *,
    dedupe_by_source: bool = True,
    marker_template: str = "[{n}]",
    max_text_chars: int | None = None,
) -> tuple[list[Citation], str]:
    """Build citations and their reference block in one call.

    A convenience wrapper combining :func:`build_citations` and
    :func:`format_reference_list`.

    Returns:
        A ``(citations, reference_block)`` tuple.
    """
    citations = build_citations(
        chunks, dedupe_by_source=dedupe_by_source, marker_template=marker_template
    )
    block = format_reference_list(citations, max_text_chars=max_text_chars)
    return citations, block
