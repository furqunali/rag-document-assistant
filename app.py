"""Production-Style RAG Document Assistant — Gradio demo for Hugging Face Spaces.

Upload your documents, then ask questions and get answers grounded in *your*
text — with citations to the exact source chunks, and an honest "I don't know"
when the documents don't cover it. Runs key-free (extractive) on free CPU; an
optional LLM key upgrades it to grounded generative answers.

Author: Furqan Ali · https://github.com/furqunali
"""
from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

import rag

SAMPLE_DIR = Path(__file__).parent / "sample_docs"
LLM = rag.maybe_llm()  # None unless a key is configured via HF Secrets


# --------------------------------------------------------------------------- #
# Ingestion
# --------------------------------------------------------------------------- #
def _read_file(path: str) -> str:
    p = Path(path)
    suf = p.suffix.lower()
    if suf in (".txt", ".md"):
        return p.read_text(encoding="utf-8", errors="ignore")
    if suf == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        except Exception as exc:
            raise ValueError(f"unable to read PDF: {exc}") from exc
    return ""


def _index_from_texts(named_texts: list[tuple[str, str]]):
    chunks: list[rag.Chunk] = []
    for name, text in named_texts:
        chunks.extend(rag.chunk_text(text, source=name))
    if not chunks:
        return None, "No readable text found. Upload .txt, .md or .pdf files with content."
    embedder = rag.build_embedder([c.text for c in chunks])
    retriever = rag.Retriever(chunks, embedder)
    gen = "on (grounded generation)" if LLM else "off (extractive, key-free)"
    status = (f"✅ Indexed **{len(chunks)} chunks** from **{len(named_texts)} document(s)**.  \n"
              f"Embedder: `{getattr(embedder, 'name', 'unknown')}` · Generation: {gen}")
    return retriever, status


def ingest_uploads(files):
    if not files:
        return None, "Upload one or more documents, or click **Load sample docs**."
    named = []
    errors = []
    for f in files:
        try:
            txt = _read_file(f)
        except ValueError as exc:
            errors.append(f"{Path(f).name}: {exc}")
            continue
        if txt.strip():
            named.append((Path(f).name, txt))
    retriever, status = _index_from_texts(named)
    if errors:
        status += "\\n\\n⚠️ Skipped unreadable file(s): " + "; ".join(errors)
    return retriever, status


def load_samples():
    named = [(p.name, p.read_text(encoding="utf-8", errors="ignore"))
             for p in sorted(SAMPLE_DIR.glob("*")) if p.suffix.lower() in (".txt", ".md")]
    if not named:
        return None, "No sample docs bundled."
    return _index_from_texts(named)


# --------------------------------------------------------------------------- #
# Ask
# --------------------------------------------------------------------------- #
def ask(question: str, retriever):
    question = (question or "").strip()
    if not question:
        return "Type a question about your documents.", ""
    if retriever is None:
        return "⚠️ Build an index first — upload docs or load the samples.", ""

    hits = retriever.query(question, k=4)
    result = rag.answer(question, hits, llm=LLM)

    ans = f"### Answer\n\n{result['answer']}"
    if result["grounded"]:
        ans += f"\n\n*Mode: {result.get('mode')} · top similarity: {result['top_score']}*"
    else:
        ans += f"\n\n*(no confident match · top similarity: {result['top_score']})*"

    if result["citations"]:
        cites = "### Sources\n\n" + "\n".join(
            f"**{c['source']}** · chunk {c['chunk']} · sim {c['score']}\n\n> {c['preview']}"
            for c in result["citations"])
    else:
        cites = ""
    return ans, cites


INTRO = """
# 📄 Production-Style RAG Document Assistant
**Ask questions about your own documents — answers are grounded in your text, cited to the source, and it says "I don't know" instead of guessing.**

1. Upload `.txt` / `.md` / `.pdf` (or load the samples) → 2. Build the index → 3. Ask.
"""

with gr.Blocks(title="RAG Document Assistant",
               theme=gr.themes.Soft(primary_hue="teal", secondary_hue="slate")) as demo:
    gr.Markdown(INTRO)
    state = gr.State(value=None)

    with gr.Row():
        with gr.Column(scale=1):
            files = gr.File(label="Upload documents", file_count="multiple",
                            file_types=[".txt", ".md", ".pdf"])
            with gr.Row():
                build_btn = gr.Button("Build index from uploads", variant="primary")
                sample_btn = gr.Button("Load sample docs")
            status = gr.Markdown()
        with gr.Column(scale=1):
            question = gr.Textbox(label="Your question",
                                  placeholder="e.g. What is the refund window?")
            ask_btn = gr.Button("Ask", variant="primary")
            answer_md = gr.Markdown()
            sources_md = gr.Markdown()

    gr.Examples(
        examples=["What is the refund window?",
                  "How do I reset my password?",
                  "What are the support hours?",
                  "Who is eligible for the loyalty program?"],
        inputs=question, label="Example questions (work with the sample docs)")

    with gr.Accordion("ℹ️ How RAG works here, limits & data", open=False):
        gr.Markdown(
            "- **Chunking**: documents are split into overlapping windows so context "
            "isn't cut at boundaries.\n"
            "- **Embeddings**: neural embeddings via `sentence-transformers` when "
            "available, with a transparent **TF-IDF fallback** so the Space always runs.\n"
            "- **Retrieval**: cosine similarity over chunk vectors returns the top matches.\n"
            "- **Grounding**: answers are built *only* from retrieved chunks and cited. "
            "Below a similarity threshold the assistant returns **\"I don't know\"** "
            "rather than hallucinating.\n"
            "- **Generation**: key-free by default (extractive — returns the exact "
            "relevant passage). Adding a `GEMINI_API_KEY` or `OPENAI_API_KEY` via "
            "**HF Secrets** upgrades it to grounded generative answers.\n\n"
            "Sample docs are a fictional company handbook. Uploaded files are processed "
            "in-memory and not stored. No secrets or private data are included.")

    build_btn.click(ingest_uploads, files, [state, status])
    sample_btn.click(load_samples, None, [state, status])
    ask_btn.click(ask, [question, state], [answer_md, sources_md])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
