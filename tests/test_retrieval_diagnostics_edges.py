from retrieval_diagnostics import has_relevant_result, score_summary


def test_score_summary_accepts_generator():
    result = score_summary({"score": value} for value in [0.1, 0.3])
    assert result["count"] == 2.0
    assert result["max"] == 0.3

def test_score_summary_defaults_missing_score():
    assert score_summary([{}])["max"] == 0.0

def test_has_relevant_result_accepts_generator():
    results = ({"score": value} for value in [0.2, 0.9])
    assert has_relevant_result(results, 0.8)

def test_has_relevant_result_returns_false_for_empty_results():
    assert not has_relevant_result([], 0.0)

def test_has_relevant_result_uses_inclusive_threshold():
    assert has_relevant_result([{"score": 0.5}], 0.5)
