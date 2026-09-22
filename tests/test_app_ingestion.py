import pytest

try:  # app pulls in the optional gradio UI stack; skip cleanly if it is unavailable
    import app
except ImportError as exc:  # pragma: no cover - environment-dependent
    pytest.skip(f"gradio stack unavailable: {exc}", allow_module_level=True)


def test_read_file_surfaces_unreadable_pdf(monkeypatch, tmp_path):
    class BrokenPdfReader:
        def __init__(self, path):
            raise RuntimeError("malformed PDF")

    monkeypatch.setattr("pypdf.PdfReader", BrokenPdfReader, raising=False)
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-broken")

    with pytest.raises(ValueError, match="unable to read PDF: malformed PDF"):
        app._read_file(str(path))


def test_ingest_uploads_reports_unreadable_file(monkeypatch):
    monkeypatch.setattr(app, "_read_file", lambda _: (_ for _ in ()).throw(ValueError("unable to read PDF: malformed PDF")))
    retriever, status = app.ingest_uploads(["broken.pdf"])
    assert retriever is None
    assert "broken.pdf: unable to read PDF: malformed PDF" in status
