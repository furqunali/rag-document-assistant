"""Gemini generation adapter backed by the reusable chatbot service."""
from __future__ import annotations

import asyncio
from typing import Any

from chatbot_config import get_api_key, get_model_name
from chatbot_service import ChatService


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
    if not get_api_key():
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=get_api_key())
        model = genai.GenerativeModel(get_model_name())
        service = ChatService(model)

        def generate(question: str, hits: list[Any]) -> str:
            return asyncio.run(service.generate(_prompt(question, hits)))

        return generate
    except Exception:
        return None
