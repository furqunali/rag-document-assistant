import numpy as np
import pytest
from retrieval import Retriever, cosine_scores
from models import Chunk

def test_cosine_scores_rejects_nonfinite_query_vector():
    with pytest.raises(ValueError, match="finite"):
        cosine_scores(np.array([[1.0, 0.0]]), np.array([np.inf, 0.0]))

def test_retriever_rejects_nonfinite_document_embeddings():
    retriever = Retriever([Chunk("policy", "policy.md", 0)], lambda texts: np.array([[np.nan, 0.0]]))
    with pytest.raises(ValueError, match="finite"):
        retriever.query("policy")

def test_retriever_rejects_boolean_question():
    retriever = Retriever([Chunk("policy", "policy.md", 0)], lambda texts: np.ones((len(texts), 2)))
    with pytest.raises(ValueError, match="question must be a string"):
        retriever.query(True)
