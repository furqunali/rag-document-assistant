import numpy as np

from models import Chunk
from retrieval import Retrieved, Retriever, cosine_scores


def embed(texts):
    return np.array([[float(len(text)), 1.0] for text in texts])


def test_cosine_scores_returns_one_for_identical_vectors():
    scores = cosine_scores(np.array([[3.0, 4.0]]), np.array([3.0, 4.0]))
    assert np.isclose(scores[0], 1.0)


def test_retriever_returns_retrieved_objects_in_score_order():
    chunks = [Chunk("a", "doc", 0), Chunk("aaaa", "doc", 1)]
    results = Retriever(chunks, embed).query("aaaa", k=1)
    assert len(results) == 1
    assert isinstance(results[0], Retrieved)
    assert results[0].chunk.index == 1


def test_retriever_handles_empty_question_and_non_positive_k():
    chunks = [Chunk("a", "doc", 0)]
    retriever = Retriever(chunks, embed)
    assert retriever.query("", k=2) == []
    assert retriever.query("a", k=0) == []


def test_retriever_caps_k_at_chunk_count():
    chunks = [Chunk("a", "doc", 0), Chunk("bb", "doc", 1)]
    assert len(Retriever(chunks, embed).query("bb", k=10)) == 2
