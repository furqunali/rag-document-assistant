"""Schema validation for exported retrieval gate reports."""
from __future__ import annotations

REQUIRED_FIELDS = frozenset({"results", "qualifying", "passed"})


def validate_retrieval_report(payload: dict) -> bool:
    if not isinstance(payload, dict) or set(payload) != REQUIRED_FIELDS:
        return False
    if not isinstance(payload["passed"], bool):
        return False
    return (
        all(type(payload[name]) is int and payload[name] >= 0 for name in ("results", "qualifying"))
        and payload["qualifying"] <= payload["results"]
    )
