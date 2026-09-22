from models import Chunk
from retrieval import Retrieved


def test_build_gemini_llm_uses_shared_provider(monkeypatch):
    calls = {}

    class FakeService:
        def __init__(self, model):
            calls["model"] = model

        async def generate(self, prompt):
            calls["prompt"] = prompt
            return "grounded answer"

    monkeypatch.setattr("gemini_adapter.get_api_key", lambda: "secret")
    monkeypatch.setattr("gemini_adapter.get_model_name", lambda: "gemini-test")
    monkeypatch.setattr(
        "gemini_adapter.build_model",
        lambda api_key, model_name: calls.update(
            api_key=api_key, model_name=model_name
        ) or ("model", model_name),
    )
    monkeypatch.setattr("gemini_adapter.ChatService", FakeService)

    import gemini_adapter

    llm = gemini_adapter.build_gemini_llm()
    result = llm(
        "What is the policy?",
        [Retrieved(Chunk("Refunds are allowed for 30 days.", "handbook.md", 0), 0.9)],
    )

    assert result == "grounded answer"
    assert calls["api_key"] == "secret"
    assert calls["model_name"] == "gemini-test"
    assert calls["model"] == ("model", "gemini-test")
    assert "[handbook.md #0]" in calls["prompt"]
