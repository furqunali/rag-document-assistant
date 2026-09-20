import pytest

from document_loader_expanded import checksum, load_document, normalize_source, normalize_text


def test_normalize_text_is_stable():
    assert normalize_text("a\r\nb\t  c") == "a\nb c"


def test_normalize_source_stabilizes_separators():
    assert normalize_source("  docs\\\\guide.md  ") == "docs/guide.md"


def test_checksum_is_deterministic():
    assert checksum("same\ntext") == checksum("same\r\ntext")


def test_load_document_populates_checksum_and_metadata():
    document = load_document("notes.md", "hello\nworld", {"kind": "markdown"})
    assert document.text == "hello\nworld"
    assert document.checksum == checksum(document.text)
    assert document.metadata == {"kind": "markdown"}


def test_empty_documents_are_rejected():
    with pytest.raises(ValueError):
        load_document("empty.md", "   ")
