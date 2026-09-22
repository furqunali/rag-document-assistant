from retrieval_diagnostics import has_relevant_result, score_summary


def test_score_summary_handles_single_score():
    assert score_summary([{"score": 0.75}]) == {"count": 1.0, "max": 0.75, "mean": 0.75, "min": 0.75}

def test_score_summary_preserves_negative_scores():
    result = score_summary([{"score": -0.2}, {"score": 0.1}])
    assert result["min"] == -0.2
    assert result["max"] == 0.1

def test_relevance_ignores_missing_scores():
    assert not has_relevant_result([{}], 0.1)

def test_relevance_accepts_exact_match():
    assert has_relevant_result([{"score": 0.42}], 0.42)
