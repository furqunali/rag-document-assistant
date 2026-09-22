from document_loader_expanded import load_document
from ingestion_pipeline import prepare_ingestion

def test_prepare_ingestion_removes_duplicate_embeddings():
    first=load_document("a.md","same")
    second=load_document("b.md","same")
    third=load_document("c.md","different")
    batch=prepare_ingestion([first,second,third])
    assert batch.unique_count == 2
    assert batch.duplicate_count == 1
    assert [doc.source for doc in batch.documents] == ["a.md","c.md"]

def test_empty_batch_is_valid():
    batch=prepare_ingestion([])
    assert batch.documents == ()
    assert batch.duplicates == {}
