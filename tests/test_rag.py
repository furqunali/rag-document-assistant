"""RAG logic tests — run without downloading any model (TF-IDF path)."""
from pathlib import Path

import rag

DOC = (Path(__file__).resolve().parents[1] / "sample_docs" / "company_handbook.md")


def _retriever():
    text = DOC.read_text(encoding="utf-8")
    chunks = rag.chunk_text(text, source="handbook.md", chunk_size=400, overlap=80)
    embedder = rag.TfidfEmbedder().fit([c.text for c in chunks])
    return rag.Retriever(chunks, embedder)


def test_chunking_overlaps_and_covers():
    chunks = rag.chunk_text("A. B. C. D. E. F.", source="x", chunk_size=8, overlap=3)
    assert len(chunks) >= 2
    assert all(c.source == "x" for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [
        (0, 0, "chunk_size"),
        (10, -1, "overlap"),
        (10, 10, "overlap"),
    ],
)
def test_chunking_rejects_invalid_window_configuration(chunk_size, overlap, message):
    with pytest.raises(ValueError, match=message):
        rag.chunk_text("A. B.", source="x", chunk_size=chunk_size, overlap=overlap)


def test_retrieval_finds_relevant_chunk():
    r = _retriever()
    hits = r.query("How long do I have to get a refund?", k=3)
    assert hits and hits[0].score > 0
    assert "refund" in hits[0].chunk.text.lower() or "30 days" in hits[0].chunk.text.lower()


def test_answer_is_grounded_with_citations():
    r = _retriever()
    hits = r.query("What are the support hours?", k=3)
    res = rag.answer("What are the support hours?", hits, threshold=0.05)
    assert res["grounded"] is True
    assert res["citations"] and res["citations"][0]["source"] == "handbook.md"
    assert "9:00" in res["answer"] or "support" in res["answer"].lower()


@pytest.mark.parametrize("threshold", [-0.1, float("inf"), float("nan")])
def test_answer_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="finite, non-negative"):
        rag.answer("refund", [], threshold=threshold)


def test_says_i_dont_know_when_off_topic():
    r = _retriever()
    hits = r.query("What is the airspeed velocity of an unladen swallow?", k=3)
    res = rag.answer("...", hits, threshold=0.9)  # force high bar -> refuse
    assert res["grounded"] is False
    assert "don't" in res["answer"].lower() or "enough information" in res["answer"].lower()


def test_empty_index_is_safe():
    r = rag.Retriever([], rag.TfidfEmbedder().fit(["x"]))
    assert r.query("anything") == []
    res = rag.answer("anything", [])
    assert res["grounded"] is False


def test_query_with_zero_k_returns_no_results():
    r = _retriever()
    assert r.query("refund", k=0) == []


def test_query_never_returns_more_than_available_chunks():
    r = _retriever()
    assert len(r.query("refund", k=999)) == len(r.chunks)
