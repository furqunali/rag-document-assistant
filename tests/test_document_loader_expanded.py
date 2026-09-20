from document_loader_expanded import DocumentLoader, normalize_text

def test_loader_normalizes_and_extracts_metadata(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("# Guide\n\nOne paragraph.", encoding="utf-8")
    doc = DocumentLoader().load_text(path)
    assert doc.metadata["title"] == "Guide"
    assert doc.metadata["words"] == "3"
    assert doc.checksum

def test_loader_rejects_invalid_utf8(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff\xfe")
    try:
        DocumentLoader().load_text(path)
    except ValueError as exc:
        assert "UTF-8" in str(exc)
    else:
        raise AssertionError("invalid UTF-8 must be rejected")

def test_normalize_text_collapses_blank_lines():
    assert normalize_text("a\r\n\r\n\r\nb") == "a\n\nb"
