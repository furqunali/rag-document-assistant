from document_loader_expanded import load_document
from ingestion_health import assess_documents


def test_ingestion_health_detects_duplicates():
    first = load_document("a.txt", "same text")
    second = load_document("b.txt", "same text")
    health = assess_documents([first, second])
    assert health.documents == 2
    assert health.unique_checksums == 1
    assert health.duplicate_documents == 1
    assert not health.healthy

def test_ingestion_health_accepts_unique_documents():
    document = load_document("a.txt", "unique")
    health = assess_documents([document])
    assert health.healthy
    assert health.total_words == 1
