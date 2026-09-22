"""Public RAG facade preserving the original API.

The implementation is split into focused modules for chunking, embeddings,
retrieval, answer assembly, and provider adapters.
"""
from __future__ import annotations

import os
from collections.abc import Callable

from agents import run_multi_agent
from answering import IDK, answer
from chunking import chunk_text
from embeddings import TfidfEmbedder, build_embedder
from models import Chunk
from retrieval import Retrieved, Retriever


def maybe_llm() -> Callable[[str, list[Retrieved]], str] | None:
    """Return a grounded LLM callable when a supported API key is configured.

    Gemini is delegated to the reusable async chatbot service. The OpenAI path
    remains as a backward-compatible provider fallback.
    """
    if os.getenv("GEMINI_API_KEY", "").strip():
        try:
            from gemini_adapter import build_gemini_llm
            return build_gemini_llm()
        except Exception:  # noqa: BLE001 - any Gemini import/setup failure means no LLM
            return None

    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

            def context(hits: list[Retrieved]) -> str:
                return "\n\n".join(
                    f"[{h.chunk.source} #{h.chunk.index}] {h.chunk.text}" for h in hits
                )

            def generate(question: str, hits: list[Retrieved]) -> str:
                prompt = (
                    "Answer the question using ONLY the context below. "
                    "If the context is insufficient, say you don't know. "
                    "Cite sources like [source #n].\n\n"
                    f"Context:\n{context(hits)}\n\nQuestion: {question}\nAnswer:"
                )
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                )
                return (response.choices[0].message.content or "").strip()

            return generate
        except Exception:  # noqa: BLE001 - any OpenAI import/setup failure means no LLM
            return None

    return None


__all__ = [
    "IDK", "Chunk", "Retrieved", "Retriever", "TfidfEmbedder",
    "answer", "build_embedder", "chunk_text", "maybe_llm", "run_multi_agent",
]
