"""Deterministic multi-agent orchestration for grounded RAG answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from retrieval import Retrieved


@dataclass(frozen=True)
class AgentDecision:
    name: str
    status: str
    details: str


@dataclass(frozen=True)
class MultiAgentResult:
    answer: str
    grounded: bool
    mode: str
    citations: list[dict]
    decisions: list[AgentDecision]


def retrieval_agent(hits: list[Retrieved], threshold: float) -> AgentDecision:
    score = hits[0].score if hits else 0.0
    status = "pass" if hits and score >= threshold else "abstain"
    return AgentDecision("retrieval_agent", status, f"top_score={score:.3f}")


def citation_agent(hits: list[Retrieved]) -> AgentDecision:
    valid = bool(hits) and all(
        isinstance(h.chunk.source, str) and h.chunk.source.strip()
        and isinstance(h.chunk.index, int)
        for h in hits
    )
    return AgentDecision("citation_agent", "pass" if valid else "abstain",
                         f"citations={len(hits) if valid else 0}")


def synthesis_agent(
    question: str,
    hits: list[Retrieved],
    llm: Callable[[str, list[Retrieved]], str] | None,
) -> tuple[str, str]:
    if llm is None:
        return hits[0].chunk.text, "extractive"
    try:
        generated = llm(question, hits)
    except Exception:
        return hits[0].chunk.text, "extractive (generation unavailable)"
    if not generated or not generated.strip():
        return hits[0].chunk.text, "extractive"
    return generated.strip(), "generative"


def run_multi_agent(
    question: str,
    hits: list[Retrieved],
    threshold: float,
    llm: Callable[[str, list[Retrieved]], str] | None = None,
) -> MultiAgentResult:
    retrieval = retrieval_agent(hits, threshold)
    if retrieval.status != "pass":
        return MultiAgentResult(
            answer="I don't have enough information in the provided documents to answer that. "
                   "Try rephrasing, or upload a document that covers this topic.",
            grounded=False, mode="abstain", citations=[], decisions=[retrieval],
        )

    citation = citation_agent(hits)
    if citation.status != "pass":
        return MultiAgentResult(
            answer="I could not verify a safe source citation for this answer.",
            grounded=False, mode="abstain", citations=[], decisions=[retrieval, citation],
        )

    body, mode = synthesis_agent(question, hits, llm)
    citations = [
        {"source": h.chunk.source, "chunk": h.chunk.index,
         "score": round(h.score, 3)}
        for h in hits
    ]
    return MultiAgentResult(
        answer=body, grounded=True, mode=mode, citations=citations,
        decisions=[retrieval, citation,
                   AgentDecision("synthesis_agent", "pass", f"mode={mode}")],
    )
