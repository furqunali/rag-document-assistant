"""Stable JSON export for retrieval threshold evaluations."""
from __future__ import annotations
import json
from dataclasses import asdict
from retrieval_threshold_gate import RetrievalGate
from retrieval_report_schema import validate_retrieval_report

def retrieval_report_dict(result: RetrievalGate) -> dict:
    if not isinstance(result, RetrievalGate):
        raise TypeError("result must be a RetrievalGate")
    payload = asdict(result)
    if not validate_retrieval_report(payload):
        raise ValueError("retrieval report failed schema validation")
    return payload

def retrieval_report_json(result: RetrievalGate) -> str:
    return json.dumps(retrieval_report_dict(result), sort_keys=True)
