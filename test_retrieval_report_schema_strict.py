from retrieval_report_schema import validate_retrieval_report


def _valid_report() -> dict:
    return {"results": 5, "qualifying": 2, "passed": True}


def test_schema_rejects_bool_as_count():
    payload = _valid_report()
    payload["results"] = True
    assert not validate_retrieval_report(payload)


def test_schema_rejects_qualifying_above_results():
    payload = _valid_report()
    payload["qualifying"] = 6
    assert not validate_retrieval_report(payload)
