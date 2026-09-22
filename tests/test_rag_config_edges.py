import math

import pytest

from rag_config import AnswerConfig, ChunkConfig


def test_chunk_config_accepts_zero_overlap():
    assert ChunkConfig(chunk_size=100, overlap=0).validate().overlap == 0

def test_chunk_config_rejects_non_positive_size():
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=0, overlap=0).validate()

def test_answer_config_accepts_zero_threshold():
    assert AnswerConfig(threshold=0.0).validate().threshold == 0.0

def test_answer_config_rejects_non_finite_threshold():
    with pytest.raises(ValueError):
        AnswerConfig(threshold=math.inf).validate()

def test_answer_config_rejects_negative_threshold():
    with pytest.raises(ValueError):
        AnswerConfig(threshold=-0.01).validate()
