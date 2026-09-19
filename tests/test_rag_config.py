import math

import pytest

from rag_config import AnswerConfig, ChunkConfig


def test_chunk_config_accepts_valid_values():
    config = ChunkConfig(chunk_size=800, overlap=120)
    assert config.validate() is config


def test_chunk_config_rejects_non_positive_size():
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        ChunkConfig(chunk_size=0).validate()


def test_chunk_config_rejects_overlap_at_size():
    with pytest.raises(ValueError, match="smaller than chunk_size"):
        ChunkConfig(chunk_size=100, overlap=100).validate()


def test_answer_config_accepts_zero_threshold():
    config = AnswerConfig(threshold=0.0)
    assert config.validate() is config


def test_answer_config_rejects_non_finite_threshold():
    with pytest.raises(ValueError, match="finite"):
        AnswerConfig(threshold=math.inf).validate()


def test_answer_config_rejects_negative_threshold():
    with pytest.raises(ValueError, match="non-negative"):
        AnswerConfig(threshold=-0.01).validate()
