from models import Chunk
from retrieval import Retrieved
from retrieval_threshold_gate import evaluate_retrieval_gate

def r(score):
    return Retrieved(Chunk("text", "src", 0), score)

def test_gate_counts_qualifying_results():
    result = evaluate_retrieval_gate([r(.2), r(.7), r(.9)], threshold=.7, minimum_results=2)
    assert result.passed and result.qualifying == 2

def test_gate_rejects_insufficient_evidence():
    result = evaluate_retrieval_gate([r(.2)], threshold=.5)
    assert not result.passed
