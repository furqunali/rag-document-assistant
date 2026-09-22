"""Validated document loading primitives for the ingestion pipeline."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LoadedDocument:
    source: str
    text: str
    checksum: str
    metadata: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not self.checksum:
            raise ValueError("checksum is required")


def normalize_source(source: str) -> str:
    """Normalize source identifiers for stable ingestion identity."""
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    normalized = source.strip().replace("\\", "/")
    normalized = re.sub(r"/+", "/", normalized)
    return normalized


def normalize_text(text: str) -> str:
    """Normalize line endings and collapse repeated whitespace."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def checksum(text: str) -> str:
    """Return a stable SHA-256 checksum for normalized document text."""
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def load_document(source: str, text: str, metadata: dict[str, str] | None = None) -> LoadedDocument:
    """Build a validated document with a content-derived checksum."""
    normalized_source = normalize_source(source)
    if not normalized_source:
        raise ValueError("source is required")
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("document text is empty")
    return LoadedDocument(normalized_source, normalized, checksum(normalized), dict(metadata or {}))
