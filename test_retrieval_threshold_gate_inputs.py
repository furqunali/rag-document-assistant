from retrieval_threshold_gate import evaluate_retrieval_gate


def test_gate_rejects_invalid_result_type():
    try:
        evaluate_retrieval_gate([object()])
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")
