import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def post_chat(message: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/chat", json={"message": message})


@pytest.mark.anyio
async def test_lead_inquiry_workflow() -> None:
    response = await post_chat("I need SEO for my gym. My budget is $2000 and I want to start next month.")

    body = response.json()

    assert response.status_code == 200
    assert body["intent"] == "lead_inquiry"
    assert body["lead_info"]["budget"] == 2000
    assert body["lead_info"]["lead_quality"] in {"warm", "hot"}
    assert len(body["trace"]) > 0


@pytest.mark.anyio
async def test_pricing_question_workflow() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "How much does SEO cost?"})
        body = response.json()
        trace_response = await client.get(f"/agent-runs/{body['agent_run_id']}/trace")

    trace_events = body["trace"] or trace_response.json()["trace"]

    assert response.status_code == 200
    assert body["intent"] == "pricing_question"
    assert any(event["node_name"] == "rag_node" and event["status"] == "success" for event in trace_events)
    assert body["final_response"]


@pytest.mark.anyio
async def test_discount_request_requires_human_approval() -> None:
    response = await post_chat("Can you give me 70% discount and promise results?")

    body = response.json()

    assert response.status_code == 200
    assert body["requires_human_approval"] is True
    assert any(word in body["final_response"].lower() for word in ("review", "approval", "team"))
