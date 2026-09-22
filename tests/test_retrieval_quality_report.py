from retrieval_threshold_gate import RetrievalGate
from retrieval_quality_report import retrieval_report_dict, retrieval_report_json

def test_retrieval_export_is_deterministic():
    result = RetrievalGate(4, 3, True)
    assert retrieval_report_dict(result) == {"results": 4, "qualifying": 3, "passed": True}
    assert retrieval_report_json(result) == '{"passed": true, "qualifying": 3, "results": 4}'


def test_retrieval_export_rejects_wrong_type():
    try:
        retrieval_report_dict([])
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")


def test_export_enforces_schema():
    assert retrieval_report_dict(RetrievalGate(1, 1, True))["results"] == 1
