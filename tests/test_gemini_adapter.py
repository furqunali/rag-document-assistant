import sys
import types

from models import Chunk
from retrieval import Retrieved


def test_build_gemini_llm_uses_chat_service(monkeypatch):
    calls = {}

    config = types.ModuleType("chatbot_config")
    config.get_api_key = lambda: "secret"
    config.get_model_name = lambda: "gemini-test"

    class FakeService:
        def __init__(self, model):
            calls["model"] = model

        async def generate(self, prompt):
            calls["prompt"] = prompt
            return "grounded answer"

    service = types.ModuleType("chatbot_service")
    service.ChatService = FakeService

    genai = types.ModuleType("google.generativeai")
    genai.configure = lambda api_key: calls.update(api_key=api_key)
    genai.GenerativeModel = lambda name: ("model", name)

    google = types.ModuleType("google")
    google.generativeai = genai

    monkeypatch.setitem(sys.modules, "chatbot_config", config)
    monkeypatch.setitem(sys.modules, "chatbot_service", service)
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.generativeai", genai)

    import gemini_adapter

    llm = gemini_adapter.build_gemini_llm()
    result = llm(
        "What is the policy?",
        [Retrieved(Chunk("Refunds are allowed for 30 days.", "handbook.md", 0), 0.9)],
    )

    assert result == "grounded answer"
    assert calls["api_key"] == "secret"
    assert calls["model"] == ("model", "gemini-test")
    assert "[handbook.md #0]" in calls["prompt"]
