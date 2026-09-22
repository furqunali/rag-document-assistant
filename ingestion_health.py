"""Deterministic ingestion health checks for loaded documents."""
from __future__ import annotations

from dataclasses import dataclass

from document_loader_expanded import LoadedDocument


@dataclass(frozen=True)
class IngestionHealth:
    documents: int
    unique_checksums: int
    duplicate_documents: int
    total_words: int
    healthy: bool

def assess_documents(documents: list[LoadedDocument]) -> IngestionHealth:
    checksums = [document.checksum for document in documents]
    unique = len(set(checksums))
    duplicates = len(checksums) - unique
    words = sum(len(document.text.split()) for document in documents)
    return IngestionHealth(
        documents=len(documents),
        unique_checksums=unique,
        duplicate_documents=duplicates,
        total_words=words,
        healthy=duplicates == 0,
    )
