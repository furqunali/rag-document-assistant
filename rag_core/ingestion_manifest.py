"""Deterministic manifest for ingested documents."""

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class IngestionRecord:
    source: str
    checksum: str
    size_bytes: int


def build_manifest(records: Iterable[IngestionRecord]) -> list[dict[str, object]]:
    """Return records sorted deterministically by source and checksum."""
    normalized = [asdict(record) for record in records]
    return sorted(normalized, key=lambda item: (str(item["source"]), str(item["checksum"])))


def manifest_json(records: Iterable[IngestionRecord]) -> str:
    """Serialize an ingestion manifest deterministically."""
    return json.dumps(build_manifest(records), sort_keys=True, separators=(",", ":"))
