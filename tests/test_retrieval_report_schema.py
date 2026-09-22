from retrieval_report_schema import validate_retrieval_report

def test_valid_retrieval_schema():
    assert validate_retrieval_report({"results":4,"qualifying":3,"passed":True})

def test_qualifying_cannot_exceed_results():
    assert not validate_retrieval_report({"results":2,"qualifying":3,"passed":True})
