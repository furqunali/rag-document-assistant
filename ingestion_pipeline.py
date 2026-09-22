"""Deterministic ingestion preparation before embedding and indexing."""
from __future__ import annotations
from dataclasses import dataclass
from document_loader_expanded import LoadedDocument
from ingestion_dedup import duplicate_sources, unique_documents

@dataclass(frozen=True)
class IngestionBatch:
    documents: tuple[LoadedDocument, ...]
    duplicates: dict[str, tuple[str, ...]]

    @property
    def unique_count(self) -> int:
        return len(self.documents)

    @property
    def duplicate_count(self) -> int:
        return sum(len(sources) - 1 for sources in self.duplicates.values())

def prepare_ingestion(documents: list[LoadedDocument]) -> IngestionBatch:
    unique = tuple(unique_documents(documents))
    groups = duplicate_sources(documents)
    return IngestionBatch(unique, {key: tuple(value) for key, value in sorted(groups.items())})
