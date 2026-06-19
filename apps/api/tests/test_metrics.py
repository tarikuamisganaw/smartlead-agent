import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app
from app.services.cost_service import estimate_llm_cost


@pytest.mark.anyio
async def test_agent_run_latency_recorded() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post("/chat", json={"message": "How much does SEO cost?"})
        agent_runs = await client.get("/agent-runs")

    body = chat.json()
    run = next(item for item in agent_runs.json()["agent_runs"] if item["id"] == body["agent_run_id"])

    assert chat.status_code == 200
    assert run["total_latency_ms"] is not None
    assert run["total_model_calls"] >= 1
    assert run["estimated_cost"] == 0
    assert run["model_provider"] == "mock"
    assert run["model_name"] == "mock-rules-v1"


@pytest.mark.anyio
async def test_trace_latency_recorded() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post("/chat", json={"message": "I need SEO for my gym. My budget is $2000."})
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    events = trace.json()["trace"]

    assert trace.status_code == 200
    assert events
    assert any(event["latency_ms"] is not None for event in events)


def test_cost_estimation_for_configured_provider(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "gemini")
    monkeypatch.setenv("ESTIMATED_INPUT_COST_PER_1M_TOKENS", "1")
    monkeypatch.setenv("ESTIMATED_OUTPUT_COST_PER_1M_TOKENS", "2")
    get_settings.cache_clear()

    try:
        cost = estimate_llm_cost(model_provider="gemini", input_tokens=1_000_000, output_tokens=500_000)
    finally:
        get_settings.cache_clear()

    assert cost == 2.0
