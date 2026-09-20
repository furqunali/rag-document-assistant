import pytest
from retrieval import Retriever

def test_query_rejects_empty_question():
    retriever = Retriever([])
    with pytest.raises(ValueError):
        retriever.query("", k=1)

def test_query_rejects_non_positive_k():
    retriever = Retriever([])
    with pytest.raises(ValueError):
        retriever.query("question", k=0)

def test_query_returns_empty_for_no_chunks():
    retriever = Retriever([])
    assert retriever.query("question", k=2) == []
