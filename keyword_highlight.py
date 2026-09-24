"""Highlight query terms inside a retrieved snippet with configurable markers.

When a RAG answer is shown alongside the passage it was drawn from, it helps the
reader to see *where* the query terms actually landed in that passage. This
module wraps each whole-word occurrence of a query term in a pair of markers —
``**term**`` by default, but any prefix/suffix pair (HTML ``<mark>`` tags, ANSI
colour codes, angle brackets) works.

Matching is case-insensitive but the original casing of the text is preserved:
searching for ``"cat"`` highlights ``Cat`` as ``**Cat**``. Matching is
whole-word, so ``"cat"`` does not light up the ``cat`` inside ``category``;
word boundaries are the usual regex ones, so terms containing hyphens or digits
behave sensibly. Overlapping terms are handled left-to-right without
double-wrapping.

The module is deterministic and pure: it takes the snippet and the terms as
plain strings and returns a new string. There is no tokenisation model, no I/O,
and no randomness.
"""
from __future__ import annotations

import re
from collections.abc import Sequence


def _clean_terms(terms: Sequence[str]) -> list[str]:
    """Validate, de-blank and de-duplicate ``terms`` (case-insensitively).

    Longer terms are ordered first so that, when two terms would match at the
    same spot, the more specific (longer) one wins the alternation.
    """
    if isinstance(terms, (str, bytes)) or not isinstance(terms, Sequence):
        raise TypeError("terms must be a sequence of strings")
    cleaned: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if not isinstance(term, str):
            raise TypeError("each term must be a string")
        stripped = term.strip()
        if not stripped:
            continue
        key = stripped.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(stripped)
    cleaned.sort(key=len, reverse=True)
    return cleaned


def highlight_terms(
    text: str,
    terms: Sequence[str],
    *,
    prefix: str = "**",
    suffix: str = "**",
) -> str:
    """Wrap every whole-word, case-insensitive occurrence of a term in markers.

    Args:
        text: the snippet to highlight.
        terms: query terms to look for. Blank terms are ignored; duplicates
            (case-insensitively) are collapsed.
        prefix: string inserted immediately before each match (e.g. ``"<mark>"``).
        suffix: string inserted immediately after each match (e.g. ``"</mark>"``).

    Returns:
        A new string with matches wrapped. If there are no usable terms or no
        matches, the original ``text`` is returned unchanged.

    Raises:
        TypeError: if ``text``/``prefix``/``suffix`` are not strings, or
            ``terms`` is not a sequence of strings.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(prefix, str) or not isinstance(suffix, str):
        raise TypeError("prefix and suffix must be strings")
    cleaned = _clean_terms(terms)
    if not text or not cleaned:
        return text

    # \b word boundaries give whole-word matching; the alternation is longest
    # first so the most specific term wins at any shared position.
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(term) for term in cleaned) + r")\b",
        re.IGNORECASE,
    )
    return pattern.sub(lambda m: f"{prefix}{m.group(0)}{suffix}", text)


def count_highlights(text: str, terms: Sequence[str]) -> int:
    """Count how many whole-word, case-insensitive term occurrences ``text`` has.

    Uses exactly the same matching rules as :func:`highlight_terms`, so it is a
    faithful preview of how many spans would be wrapped.

    Raises:
        TypeError: on the same conditions as :func:`highlight_terms`.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    cleaned = _clean_terms(terms)
    if not text or not cleaned:
        return 0
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(term) for term in cleaned) + r")\b",
        re.IGNORECASE,
    )
    return len(pattern.findall(text))
