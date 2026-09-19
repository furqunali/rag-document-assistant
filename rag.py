"""Production-style RAG core — chunk → embed → retrieve → grounded answer."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable

import numpy as np

Vector = np.ndarray
EmbedFn = Callable[[list[str]], np.ndarray]

@dataclass
class Chunk:
    text: str
    source: str
    index: int

def chunk_text(text: str, source: str, chunk_size: int = 600, overlap: int = 100) -> list[Chunk]:
    """Split text into overlapping word windows."""
    if chunk_size <= 0: raise ValueError("chunk_size must be positive")
    if overlap < 0: raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size: raise ValueError("overlap must be smaller than chunk_size")
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text: return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[Chunk] = []
    buf, idx = "", 0
    for sent in sentences:
        if len(buf) + len(sent) + 1 <= chunk_size or not buf: buf = (buf + " " + sent).strip()
        else:
            chunks.append(Chunk(buf, source, idx)); idx += 1
            tail = buf[-overlap:] if overlap else ""
            buf = (tail + " " + sent).strip()
    if buf: chunks.append(Chunk(buf, source, idx))
    return chunks

_TOKEN = re.compile(r"[a-z0-9]+")
def _tokenize(s: str) -> list[str]: return _TOKEN.findall((s or "").lower())

class TfidfEmbedder:
    name = "tfidf (pure-python fallback)"
    def __init__(self) -> None: self.vocab, self.idf = {}, None
    def fit(self, corpus: list[str]) -> "TfidfEmbedder":
        df = {}
        docs_tokens = [set(_tokenize(d)) for d in corpus]
        for toks in docs_tokens:
            for t in toks: df[t] = df.get(t, 0) + 1
        self.vocab = {t: i for i, t in enumerate(sorted(df))}
        n = len(corpus); idf = np.zeros(len(self.vocab), dtype=np.float32)
        for t, i in self.vocab.items(): idf[i] = math.log((1 + n) / (1 + df[t])) + 1.0
        self.idf = idf; return self
    def __call__(self, texts: list[str]) -> np.ndarray:
        assert self.idf is not None, "fit() must be called first"
        out = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for r, text in enumerate(texts):
            counts = {}; toks = _tokenize(text)
            for t in toks:
                j = self.vocab.get(t)
                if j is not None: counts[j] = counts.get(j, 0) + 1
            if toks:
                for j, c in counts.items(): out[r, j] = (c / len(toks)) * self.idf[j]
        return out

class STEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name); self.name = f"sentence-transformers ({model_name.split('/')[-1]})"
    def fit(self, corpus: list[str]) -> "STEmbedder": return self
    def __call__(self, texts: list[str]) -> np.ndarray: return np.asarray(self.model.encode(texts, normalize_embeddings=False), dtype=np.float32)

def build_embedder(corpus: list[str]):
    try: return STEmbedder()
    except Exception: return TfidfEmbedder().fit(corpus)

def _cosine(mat: np.ndarray, vec: np.ndarray) -> np.ndarray:
    denom = (np.linalg.norm(mat, axis=1) * np.linalg.norm(vec)) + 1e-9
    return (mat @ vec) / denom

@dataclass
class Retrieved:
    chunk: Chunk
    score: float

class Retriever:
    def __init__(self, chunks: list[Chunk], embed: EmbedFn) -> None:
        self.chunks, self.embed = chunks, embed
        self.matrix = embed([c.text for c in chunks]) if chunks else np.zeros((0, 1))
    def query(self, question: str, k: int = 4) -> list[Retrieved]:
        question = (question or "").strip()
        if not question or not self.chunks: return []
        q = self.embed([question])[0]
        scores = _cosine(self.matrix, q)
        k = max(0, min(k, len(self.chunks)))
        order = sorted(range(len(self.chunks)), key=lambda i: (-float(scores[i]), self.chunks[i].index))[:k]
        return [Retrieved(self.chunks[i], float(scores[i])) for i in order]

IDK = ("I don't have enough information in the provided documents to answer that. " "Try rephrasing, or upload a document that covers this topic.")
def answer(question: str, hits: list[Retrieved], threshold: float = 0.15, llm: Callable[[str, list[Retrieved]], str] | None = None) -> dict:
    top = hits[0].score if hits else 0.0
    if not hits or top < threshold: return {"answer": IDK, "grounded": False, "citations": [], "top_score": round(top, 3)}
    citations = [{"source": h.chunk.source, "chunk": h.chunk.index, "score": round(h.score, 3), "preview": (h.chunk.text[:200] + ("…" if len(h.chunk.text) > 200 else ""))} for h in hits]
    mode, body = "extractive", hits[0].chunk.text
    if llm is not None:
        try:
            generated = llm(question, hits)
            if generated and generated.strip(): body, mode = generated.strip(), "generative"
        except Exception: mode = "extractive (generation unavailable)"
    return {"answer": body, "grounded": True, "mode": mode, "citations": citations, "top_score": round(top, 3)}

def maybe_llm() -> Callable[[str, list[Retrieved]], str] | None:
    import os
    gem, oai = os.getenv("GEMINI_API_KEY"), os.getenv("OPENAI_API_KEY")
    def _context(hits): return "\n\n".join(f"[{h.chunk.source} #{h.chunk.index}] {h.chunk.text}" for h in hits)
    def _prompt(q, hits): return ("Answer the question using ONLY the context below. If the context is insufficient, say you don't know. Cite sources like [source #n].\n\n" f"Context:\n{_context(hits)}\n\nQuestion: {q}\nAnswer:")
    if gem:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gem); model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
            def _gen(q, hits): return model.generate_content(_prompt(q, hits)).text.strip()
            return _gen
        except Exception: return None
    if oai:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=oai)
            def _gen(q, hits):
                r = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role":"user", "content":_prompt(q, hits)}])
                return r.choices[0].message.content.strip()
            return _gen
        except Exception: return None
    return None
