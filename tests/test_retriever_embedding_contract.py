import numpy as np
import pytest

from retrieval import Retriever
from models import Chunk


def test_retriever_rejects_embedding_row_count_mismatch():
    chunks = [Chunk("alpha", "a", 0), Chunk("beta", "b", 1)]

    def embed(texts):
        if len(texts) == 2:
            return np.array([[1.0, 0.0]])
        return np.array([[1.0, 0.0]])

    with pytest.raises(ValueError, match="row count"):
        Retriever(chunks, embed=embed).query("alpha")
