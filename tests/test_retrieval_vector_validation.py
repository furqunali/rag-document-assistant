import numpy as np
import pytest

from retrieval import cosine_scores


def test_cosine_scores_rejects_non_2d_matrix():
    with pytest.raises(ValueError, match="2D"):
        cosine_scores(np.array([1.0, 2.0]), np.array([1.0, 2.0]))


def test_cosine_scores_rejects_non_1d_vector():
    with pytest.raises(ValueError, match="1D"):
        cosine_scores(np.eye(2), np.array([[1.0, 0.0]]))


def test_cosine_scores_rejects_dimension_mismatch():
    with pytest.raises(ValueError, match="dimensions"):
        cosine_scores(np.eye(2), np.array([1.0, 2.0, 3.0]))


def test_cosine_scores_keeps_valid_shape():
    scores = cosine_scores(np.eye(2), np.array([1.0, 0.0]))
    assert np.allclose(scores, [1.0, 0.0], atol=1e-8)


def test_query_rejects_non_string_question():
    r = _retriever()
    with pytest.raises(ValueError, match="question must be a string"):
        r.query(123)  # type: ignore[arg-type]
