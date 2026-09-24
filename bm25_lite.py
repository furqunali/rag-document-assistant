"""A compact, dependency-free BM25 ranking function over tokenised documents.

Dense embedding retrieval is strong on paraphrase and meaning, but it can miss
exact-term matches — a rare product code, an error string, a surname — that a
classic lexical scorer catches immediately. BM25 (Robertson & Walker, "Okapi",
1994) is the workhorse lexical ranker: it rewards a document for containing the
query terms, tempers the reward as a term repeats (saturation), and discounts
terms that are common across the corpus (inverse document frequency), while
normalising for document length so long documents do not win by sheer size.

The score of document ``d`` for query ``q`` is::

    score(d, q) = sum over t in q of
        idf(t) * f(t, d) * (k1 + 1)
        ---------------------------------------------------
        f(t, d) + k1 * (1 - b + b * |d| / avgdl)

where ``f(t, d)`` is the frequency of term ``t`` in ``d``, ``|d|`` its length,
``avgdl`` the mean document length, and ``idf(t)`` the smoothed inverse document
frequency::

    idf(t) = ln( 1 + (N - n(t) + 0.5) / (n(t) + 0.5) )

with ``N`` documents and ``n(t)`` the number containing ``t``. This "plus-one"
form is always non-negative, so no term can ever push a score below zero.

The module is deterministic and pure: it works on plain lists of string tokens
that the caller has already produced. There is no tokeniser, no I/O, and no
randomness. Build a :class:`BM25Index` once over a corpus, then call
:meth:`BM25Index.rank` for each query.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BM25Result:
    """One scored document.

    Attributes:
        index: position of the document in the corpus passed to the index.
        score: BM25 score, ``>= 0``, rounded to 6 decimals. Higher is better.
    """

    index: int
    score: float


def _validate_tokens(tokens: Sequence[str], label: str) -> list[str]:
    if isinstance(tokens, (str, bytes)) or not isinstance(tokens, Sequence):
        raise TypeError(f"{label} must be a sequence of string tokens")
    listed = list(tokens)
    if any(not isinstance(token, str) for token in listed):
        raise TypeError(f"{label} tokens must be strings")
    return listed


class BM25Index:
    """An immutable BM25 index over a fixed corpus of tokenised documents.

    Args:
        corpus: the documents to index, each a sequence of string tokens.
            May be empty; an empty corpus ranks nothing.
        k1: term-frequency saturation control (``>= 0``). Larger values let a
            repeated term keep adding weight for longer; ``1.5`` is typical.
        b: length-normalisation strength in ``[0, 1]``. ``0`` ignores document
            length entirely; ``1`` fully normalises; ``0.75`` is typical.

    Raises:
        TypeError: if the corpus or any document is not a sequence of strings.
        ValueError: if ``k1`` is negative or ``b`` is outside ``[0, 1]``.
    """

    def __init__(
        self,
        corpus: Sequence[Sequence[str]],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if isinstance(corpus, (str, bytes)) or not isinstance(corpus, Sequence):
            raise TypeError("corpus must be a sequence of tokenised documents")
        k1 = float(k1)
        b = float(b)
        if k1 < 0.0:
            raise ValueError("k1 must be non-negative")
        if not 0.0 <= b <= 1.0:
            raise ValueError("b must be within [0, 1]")

        self._k1 = k1
        self._b = b
        self._docs: list[list[str]] = [
            _validate_tokens(doc, "document") for doc in corpus
        ]
        self._doc_len = [len(doc) for doc in self._docs]
        self._term_freqs = [Counter(doc) for doc in self._docs]
        self._avgdl = (sum(self._doc_len) / len(self._docs)) if self._docs else 0.0

        # Document frequency and smoothed idf per term across the corpus.
        doc_freq: Counter[str] = Counter()
        for freqs in self._term_freqs:
            doc_freq.update(freqs.keys())
        n = len(self._docs)
        self._idf: dict[str, float] = {
            term: math.log(1.0 + (n - df + 0.5) / (df + 0.5))
            for term, df in doc_freq.items()
        }

    @property
    def corpus_size(self) -> int:
        """Number of documents in the index."""
        return len(self._docs)

    @property
    def average_length(self) -> float:
        """Mean document length in tokens (``0.0`` for an empty corpus)."""
        return self._avgdl

    def score(self, query: Sequence[str], doc_index: int) -> float:
        """Return the BM25 score of a single document for ``query``.

        Args:
            query: the query as a sequence of string tokens.
            doc_index: index of the document within the indexed corpus.

        Returns:
            The document's BM25 score, ``>= 0``, rounded to 6 decimals.

        Raises:
            TypeError: if ``query`` is not a sequence of strings.
            IndexError: if ``doc_index`` is out of range.
        """
        query_tokens = _validate_tokens(query, "query")
        if not 0 <= doc_index < len(self._docs):
            raise IndexError("doc_index out of range")

        freqs = self._term_freqs[doc_index]
        length = self._doc_len[doc_index]
        denom_norm = self._k1 * (
            1.0 - self._b + self._b * (length / self._avgdl if self._avgdl else 0.0)
        )
        total = 0.0
        for term in query_tokens:
            f = freqs.get(term, 0)
            if not f:
                continue
            idf = self._idf.get(term, 0.0)
            total += idf * (f * (self._k1 + 1.0)) / (f + denom_norm)
        return round(total, 6)

    def rank(self, query: Sequence[str], *, top_k: int | None = None) -> list[BM25Result]:
        """Rank every document in the corpus for ``query``, best first.

        Args:
            query: the query as a sequence of string tokens.
            top_k: if given, return at most this many results (must be a
                positive integer). ``None`` returns all documents.

        Returns:
            A list of :class:`BM25Result` ordered by descending score. Ties are
            broken by ascending document index, so the ordering is fully
            deterministic. An empty corpus yields ``[]``.

        Raises:
            TypeError: if ``query`` is not a sequence of strings.
            ValueError: if ``top_k`` is given but not a positive integer.
        """
        query_tokens = _validate_tokens(query, "query")
        if top_k is not None and (not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0):
            raise ValueError("top_k must be a positive integer or None")

        results = [
            BM25Result(i, self.score(query_tokens, i)) for i in range(len(self._docs))
        ]
        results.sort(key=lambda r: (-r.score, r.index))
        return results if top_k is None else results[:top_k]
