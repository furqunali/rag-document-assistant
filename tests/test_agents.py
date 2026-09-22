
from agents import citation_agent, retrieval_agent, run_multi_agent
from models import Chunk
from retrieval import Retrieved


def hits(score=0.8):
    return [Retrieved(Chunk("robot text", "docs/robot.md", 2), score)]


def test_retrieval_agent_abstains_below_threshold():
    assert retrieval_agent(hits(0.1), 0.2).status == "abstain"


def test_citation_agent_requires_source():
    assert citation_agent(hits()).status == "pass"
    bad = [Retrieved(Chunk("text", "", 0), 0.9)]
    assert citation_agent(bad).status == "abstain"


def test_multi_agent_returns_trace_and_citations():
    result = run_multi_agent("What?", hits())
    assert result.grounded is True
    assert result.mode == "extractive"
    assert len(result.decisions) == 3
    assert result.citations[0]["source"] == "docs/robot.md"


def test_multi_agent_abstains_before_synthesis():
    called = False

    def llm(question, retrieved):
        nonlocal called
        called = True
        return "unsafe"

    result = run_multi_agent("What?", hits(0.1), 0.2, llm)
    assert result.grounded is False
    assert called is False
