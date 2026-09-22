"""Stable JSON contract for ingestion policy findings."""
from __future__ import annotations

import json
from dataclasses import asdict

from ingestion_policy import IngestionFinding


def to_json(findings: tuple[IngestionFinding, ...]) -> str:
    return json.dumps([asdict(finding) for finding in findings], sort_keys=True, separators=(",", ":"))
