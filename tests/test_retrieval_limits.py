import numpy as np

import rag


def constant_embed(texts):
    return np.ones((len(texts), 2))


def test_negative_k_returns_no_results():
    chunks = [rag.Chunk("refund policy", "policy.md", 0)]
    retriever = rag.Retriever(chunks, constant_embed)

    assert retriever.query("refund", k=-1) == []


def test_large_k_is_bounded_by_chunk_count():
    chunks = [
        rag.Chunk("refund policy", "policy.md", 0),
        rag.Chunk("support hours", "support.md", 1),
    ]
    retriever = rag.Retriever(chunks, constant_embed)

    assert len(retriever.query("anything", k=100)) == 2
