from retrieval import Retriever

def test_query_empty_question_returns_no_results():
    assert Retriever([]).query("", k=1) == []

def test_query_non_positive_k_returns_no_results():
    assert Retriever([]).query("question", k=0) == []

def test_query_returns_empty_for_no_chunks():
    assert Retriever([]).query("question", k=2) == []
