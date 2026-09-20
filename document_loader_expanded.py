"""Document loading and normalization primitives for the RAG pipeline."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

@dataclass(frozen=True)
class LoadedDocument:
    source: str
    text: str
    metadata: dict[str, str]
    checksum: str

class DocumentLoader:
    def __init__(self, max_bytes: int = 2_000_000) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes

    def load_text(self, path: str | Path) -> LoadedDocument:
        file = Path(path)
        data = file.read_bytes()
        if len(data) > self.max_bytes:
            raise ValueError("document exceeds size limit")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("document must be UTF-8 text") from exc
        text = normalize_text(text)
        if not text:
            raise ValueError("document is empty")
        return LoadedDocument(str(file), text, extract_metadata(text), checksum(text))

def normalize_text(text: str) -> str:
    value = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", normalize_text(text)) if p.strip()]

def split_sentences(text: str) -> list[str]:
    value = normalize_text(text)
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", value) if p.strip()]

def checksum(text: str) -> str:
    return sha256(normalize_text(text).encode("utf-8")).hexdigest()

def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))

def extract_title(text: str) -> str:
    for line in (text or "").splitlines():
        value = line.strip()
        if value.startswith("#"):
            return value.lstrip("# ").strip()
    return next((x.strip() for x in (text or "").splitlines() if x.strip()), "")

def extract_metadata(text: str) -> dict[str, str]:
    return {"title": extract_title(text), "words": str(word_count(text)),
            "paragraphs": str(len(split_paragraphs(text)))}

def chunk_paragraphs(text: str, max_chars: int = 1200) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    chunks, current = [], ""
    for paragraph in split_paragraphs(text):
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = ""
        current = (current + "\n\n" + paragraph).strip()
    if current:
        chunks.append(current)
    return chunks

def duplicate_checksum(documents: list[LoadedDocument]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for document in documents:
        groups.setdefault(document.checksum, []).append(document.source)
    return {key: value for key, value in groups.items() if len(value) > 1}
