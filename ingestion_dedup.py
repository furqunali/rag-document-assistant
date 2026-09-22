"""Deduplicate loaded documents before expensive embedding work."""
from __future__ import annotations
from document_loader_expanded import LoadedDocument

def unique_documents(documents: list[LoadedDocument]) -> list[LoadedDocument]:
    """Keep the first document for each checksum while preserving input order."""
    seen: set[str] = set()
    result: list[LoadedDocument] = []
    for document in documents:
        if not document.checksum:
            raise ValueError("document checksum is required")
        if document.checksum in seen:
            continue
        seen.add(document.checksum)
        result.append(document)
    return result

def duplicate_sources(documents: list[LoadedDocument]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for document in documents:
        groups.setdefault(document.checksum, []).append(document.source)
    return {checksum: sources for checksum, sources in groups.items() if len(sources) > 1}
