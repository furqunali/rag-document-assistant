import pytest

from retrieval_diagnostics import has_relevant_result, score_summary


def test_score_summary_reports_distribution():
    results = [{"score": 0.2}, {"score": 0.8}, {"score": 0.5}]
    assert score_summary(results) == {
        "count": 3.0,
        "max": 0.8,
        "mean": 0.5,
        "min": 0.2,
    }


def test_score_summary_handles_empty_results():
    assert score_summary([]) == {"count": 0.0, "max": 0.0, "mean": 0.0, "min": 0.0}


def test_has_relevant_result_checks_threshold():
    results = [{"score": 0.1}, {"score": 0.72}]
    assert has_relevant_result(results, 0.7)
    assert not has_relevant_result(results, 0.8)


def test_has_relevant_result_rejects_negative_threshold():
    with pytest.raises(ValueError, match="non-negative"):
        has_relevant_result([], -0.1)
