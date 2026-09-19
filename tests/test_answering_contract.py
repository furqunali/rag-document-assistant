from models import Chunk
from retrieval import Retrieved
from answering import IDK, answer, citations_for, validate_threshold
import pytest


def hit(text="answer", source="doc", index=1, score=0.8):
    return Retrieved(Chunk(text, source, index), score)


def test_validate_threshold_accepts_zero():
    assert validate_threshold(0.0) == 0.0


def test_validate_threshold_rejects_negative():
    with pytest.raises(ValueError, match="non-negative"):
        validate_threshold(-0.1)


def test_answer_returns_idk_without_relevant_hits():
    result = answer("question", [hit(score=0.1)], threshold=0.5)
    assert result["answer"] == IDK
    assert result["grounded"] is False
    assert result["citations"] == []


def test_answer_uses_top_hit_and_citations():
    result = answer("question", [hit("useful text", "chapter", 2, 0.91)])
    assert result["answer"] == "useful text"
    assert result["grounded"] is True
    assert result["citations"][0]["source"] == "chapter"
    assert result["top_score"] == 0.91


def test_answer_uses_non_empty_llm_output():
    result = answer("question", [hit()], llm=lambda q, h: "  generated  ")
    assert result["answer"] == "generated"
    assert result["mode"] == "generative"


def test_citations_preview_is_bounded():
    result = citations_for([hit("x" * 205)])[0]
    assert len(result["preview"]) == 201
