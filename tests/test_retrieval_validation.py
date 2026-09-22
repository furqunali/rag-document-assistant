from models import Chunk
from retrieval import Retrieved
from retrieval_validation import is_valid_results, validate_results


def test_validation_accepts_unique_finite_results():
    results = [Retrieved(Chunk("robot", "a.md", 0), 0.8), Retrieved(Chunk("arm", "b.md", 0), 0.4)]
    assert is_valid_results(results)

def test_validation_rejects_duplicate_chunk_identity():
    chunk = Chunk("robot", "a.md", 0)
    issues = validate_results([Retrieved(chunk, 0.8), Retrieved(chunk, 0.7)])
    assert "result 1 duplicates chunk identity" in issues

def test_validation_rejects_empty_text_and_non_finite_score():
    result = Retrieved(Chunk(" ", "a.md", 0), float("nan"))
    issues = validate_results([result])
    assert "result 0 has non-finite score" in issues
    assert "result 0 has empty chunk text" in issues
