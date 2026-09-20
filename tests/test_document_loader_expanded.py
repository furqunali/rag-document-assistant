from pathlib import Path

import pytest

from document_loader_expanded import DocumentLoader, checksum, duplicate_checksum, split_sentences


def test_load_normalizes_text_and_collects_metadata(tmp_path: Path):
    path = tmp_path / "guide.md"
    path.write_bytes(b"# Guide\r\n\r\nFirst paragraph.\r\n\r\nSecond paragraph.")
    document = DocumentLoader().load(path)
    assert document.text == "# Guide\n\nFirst paragraph.\n\nSecond paragraph."
    assert document.metadata["title"] == "Guide"
    assert document.metadata["paragraphs"] == "3"


def test_loader_rejects_oversized_and_invalid_utf8(tmp_path: Path):
    oversized = tmp_path / "large.txt"
    oversized.write_bytes(b"x" * 10)
    with pytest.raises(ValueError, match="size"):
        DocumentLoader(max_bytes=5).load(oversized)

    invalid = tmp_path / "bad.txt"
    invalid.write_bytes(b"\xff\xfe")
    with pytest.raises(ValueError, match="UTF-8"):
        DocumentLoader().load(invalid)


def test_sentence_split_and_checksum_are_stable():
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]
    assert checksum("hello") == checksum(b"hello")


def test_duplicate_checksum_finds_repeated_documents(tmp_path: Path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")
    documents = [DocumentLoader().load(first), DocumentLoader().load(second)]
    assert duplicate_checksum(documents) == {checksum("same")}
