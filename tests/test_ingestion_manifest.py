from rag_core.ingestion_manifest import IngestionRecord, build_manifest, manifest_json


def test_manifest_sorts_records_deterministically():
    records = [
        IngestionRecord("b.md", "2", 20),
        IngestionRecord("a.md", "3", 30),
        IngestionRecord("a.md", "1", 10),
    ]
    assert [item["source"] for item in build_manifest(records)] == ["a.md", "a.md", "b.md"]
    assert build_manifest(records)[0]["checksum"] == "1"


def test_manifest_json_is_deterministic():
    records = [IngestionRecord("b.md", "2", 20), IngestionRecord("a.md", "1", 10)]
    assert manifest_json(records) == '[{"checksum":"1","size_bytes":10,"source":"a.md"},{"checksum":"2","size_bytes":20,"source":"b.md"}]'
