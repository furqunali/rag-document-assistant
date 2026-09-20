"""Aggregate deterministic ingestion policy findings."""
from __future__ import annotations
from dataclasses import dataclass
from ingestion_policy import IngestionFinding

@dataclass(frozen=True)
class IngestionSummary:
    total: int
    errors: int
    warnings: int
    infos: int
    healthy: bool

def summarize_ingestion(findings: tuple[IngestionFinding, ...]) -> IngestionSummary:
    errors = sum(f.severity == "error" for f in findings)
    warnings = sum(f.severity == "warning" for f in findings)
    infos = sum(f.severity == "info" for f in findings)
    return IngestionSummary(len(findings), errors, warnings, infos, errors == 0)
