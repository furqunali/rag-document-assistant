"""Lightweight health checks for the RAG pipeline components."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ComponentHealth:
    name: str
    ready: bool
    detail: str = ""

def check_component(name: str, component: Any) -> ComponentHealth:
    """Check that a required component exists and exposes a callable interface."""
    if not name.strip():
        raise ValueError("component name must not be empty")
    if component is None:
        return ComponentHealth(name=name, ready=False, detail="component is missing")
    if callable(component):
        return ComponentHealth(name=name, ready=True, detail="callable component")
    return ComponentHealth(name=name, ready=True, detail="configured component")

def summarize_health(*checks: ComponentHealth) -> dict[str, object]:
    """Build a stable, serializable health summary."""
    return {
        "ready": all(check.ready for check in checks),
        "components": [
            {"name": check.name, "ready": check.ready, "detail": check.detail}
            for check in checks
        ],
    }
