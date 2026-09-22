"""Policy findings derived from deterministic ingestion health."""
from __future__ import annotations

from dataclasses import dataclass

from ingestion_health import IngestionHealth


@dataclass(frozen=True)
class IngestionFinding:
    code: str
    severity: str
    message: str

def evaluate_ingestion(health: IngestionHealth) -> tuple[IngestionFinding, ...]:
    findings: list[IngestionFinding] = []
    if health.documents == 0:
        findings.append(IngestionFinding("EMPTY_INGESTION", "warning", "no documents were ingested"))
    if health.duplicate_documents:
        findings.append(IngestionFinding("DUPLICATES", "error", f"{health.duplicate_documents} duplicate documents detected"))
    if health.healthy and health.documents:
        findings.append(IngestionFinding("HEALTHY", "info", "ingestion passed all health checks"))
    return tuple(findings)
