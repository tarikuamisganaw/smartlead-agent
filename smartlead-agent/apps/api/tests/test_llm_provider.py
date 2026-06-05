import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app
from app.services.llm_service import classify_intent, extract_lead_info, get_llm_provider


def test_llm_provider_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    get_settings.cache_clear()

    provider = get_llm_provider()
    pricing = classify_intent("How much does SEO cost?")
    lead_info = extract_lead_info("I need SEO for my gym. My budget is $2000.")

    assert provider.provider_name == "mock"
    assert pricing.intent == "pricing_question"
    assert lead_info.service_interest == "SEO"
    assert lead_info.business_type == "gym"
    assert lead_info.budget == 2000


@pytest.mark.anyio
async def test_chat_uses_mock_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "How much does SEO cost?"})

    body = response.json()

    assert response.status_code == 200
    assert body["intent"] == "pricing_question"
    assert any("provider=mock" in event["output_summary"] for event in body["trace"] if event["output_summary"])
