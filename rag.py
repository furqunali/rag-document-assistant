"""Public RAG facade preserving the original API.

The implementation is split into focused modules for chunking, embeddings,
retrieval, answer assembly, and shared configuration.
"""
from __future__ import annotations

import os
from typing import Callable

from answering import IDK, answer
from chunking import chunk_text
from embeddings import TfidfEmbedder, build_embedder
from models import Chunk
from retrieval import Retrieved, Retriever


def maybe_llm() -> Callable[[str, list[Retrieved]], str] | None:
    """Return a grounded LLM callable when a supported API key is configured."""
    gem = os.getenv("GEMINI_API_KEY")
    oai = os.getenv("OPENAI_API_KEY")

    def context(hits: list[Retrieved]) -> str:
        return "\\n\\n".join(f"[{h.chunk.source} #{h.chunk.index}] {h.chunk.text}" for h in hits)

    def prompt(question: str, hits: list[Retrieved]) -> str:
        return ("Answer the question using ONLY the context below. If the context is "
                "insufficient, say you don't know. Cite sources like [source #n].\\n\\n"
                f"Context:\\n{context(hits)}\\n\\nQuestion: {question}\\nAnswer:")

    if gem:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gem)
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
            def generate(question, hits):
                return model.generate_content(prompt(question, hits)).text.strip()
            return generate
        except Exception:
            return None
    if oai:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=oai)
            def generate(question, hits):
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt(question, hits)}],
                )
                return response.choices[0].message.content.strip()
            return generate
        except Exception:
            return None
    return None


__all__ = [
    "IDK", "Chunk", "Retrieved", "Retriever", "TfidfEmbedder",
    "answer", "build_embedder", "chunk_text", "maybe_llm",
]
