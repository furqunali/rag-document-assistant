from document_loader_expanded import DocumentLoader
from ingestion_health import assess_documents

def test_ingestion_health_detects_duplicates(tmp_path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("same text", encoding="utf-8")
    second.write_text("same text", encoding="utf-8")
    loader = DocumentLoader()
    health = assess_documents([loader.load(first), loader.load(second)])
    assert health.documents == 2
    assert health.unique_checksums == 1
    assert health.duplicate_documents == 1
    assert not health.healthy

def test_ingestion_health_accepts_unique_documents(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("unique", encoding="utf-8")
    health = assess_documents([DocumentLoader().load(path)])
    assert health.healthy
    assert health.total_words == 1
