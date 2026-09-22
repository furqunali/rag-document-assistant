"""Gemini generation adapter backed by the reusable chatbot service."""
from __future__ import annotations

import asyncio
from typing import Any

try:  # optional gemini-chatbot integration package
    from chatbot_config import get_api_key, get_model_name
    from chatbot_service import ChatService
    from gemini_provider import build_model
except ImportError:  # pragma: no cover - integration is optional
    get_api_key = get_model_name = ChatService = build_model = None


def _prompt(question: str, hits: list[Any]) -> str:
    context = "\n\n".join(
        f"[{hit.chunk.source} #{hit.chunk.index}] {hit.chunk.text}" for hit in hits
    )
    return (
        "Answer the question using ONLY the context below. "
        "If the context is insufficient, say you don't know. "
        "Cite sources like [source #n].\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


def build_gemini_llm() -> Any | None:
    """Build a synchronous RAG-compatible callable over ChatService."""
    try:
        model = build_model(get_api_key(), get_model_name())
        service = ChatService(model)

        def generate(question: str, hits: list[Any]) -> str:
            return asyncio.run(service.generate(_prompt(question, hits)))

        return generate
    except Exception:
        return None
