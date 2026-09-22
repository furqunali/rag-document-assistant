import pytest
from document_loader_expanded import LoadedDocument
from ingestion_dedup import duplicate_sources, unique_documents

def d(checksum, source): return LoadedDocument(source, "text", checksum=checksum)

def test_unique_documents_keeps_first():
    docs=[d("a","one"),d("a","two"),d("b","three")]
    assert [x.source for x in unique_documents(docs)] == ["one","three"]

def test_duplicate_sources_groups_checksums():
    assert duplicate_sources([d("a","one"),d("a","two"),d("b","three")]) == {"a":["one","two"]}

def test_missing_checksum_is_rejected():
    with pytest.raises(ValueError):
        unique_documents([d("","one")])
