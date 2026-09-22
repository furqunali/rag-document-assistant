import numpy as np

import rag


def test_blank_question_returns_no_results():
    chunks = [rag.Chunk("refund policy", "policy.md", 0)]
    retriever = rag.Retriever(chunks, lambda texts: np.ones((len(texts), 2)))
    assert retriever.query("   ") == []


def test_none_question_returns_no_results():
    chunks = [rag.Chunk("refund policy", "policy.md", 0)]
    retriever = rag.Retriever(chunks, lambda texts: np.ones((len(texts), 2)))
    assert retriever.query(None) == []


def test_boolean_question_is_rejected():
    chunks = [rag.Chunk("refund policy", "policy.md", 0)]
    retriever = rag.Retriever(chunks, lambda texts: np.ones((len(texts), 2)))
    with pytest.raises(ValueError, match="question must be a string"):
        retriever.query(True)
