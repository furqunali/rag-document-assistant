"""Safe document loading and normalization primitives for RAG ingestion."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from pathlib import Path


@dataclass(frozen=True)
class LoadedDocument:
    source: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)
    checksum: str = ""

    @property
    def characters(self) -> int:
        return len(self.text)

    @property
    def words(self) -> int:
        return len(self.text.split())


class DocumentLoader:
    def __init__(self, max_bytes: int = 2_000_000) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes

    def load(self, path: str | Path) -> LoadedDocument:
        candidate = Path(path)
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        if candidate.stat().st_size > self.max_bytes:
            raise ValueError("document exceeds configured size limit")
        raw = candidate.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("document must be valid UTF-8") from exc
        normalized = normalize_text(text)
        return LoadedDocument(
            source=candidate.as_posix(),
            text=normalized,
            metadata=extract_metadata(candidate, normalized),
            checksum=checksum(raw),
        )


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]


def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def checksum(data: bytes | str) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return path.stem.replace("_", " ").replace("-", " ").strip()


def extract_metadata(path: Path, text: str) -> dict[str, str]:
    paragraphs = split_paragraphs(text)
    return {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "title": extract_title(path, text),
        "paragraphs": str(len(paragraphs)),
        "words": str(len(text.split())),
    }


def chunk_paragraphs(text: str, max_chars: int = 1200) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for paragraph in split_paragraphs(text):
        extra = len(paragraph) + (2 if current else 0)
        if current and size + extra > max_chars:
            chunks.append("\n\n".join(current))
            current, size = [], 0
        current.append(paragraph)
        size += len(paragraph) + (2 if size else 0)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def duplicate_checksum(documents: list[LoadedDocument]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for document in documents:
        if document.checksum in seen:
            duplicates.add(document.checksum)
        seen.add(document.checksum)
    return duplicates
