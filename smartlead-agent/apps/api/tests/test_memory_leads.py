import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.lead_service import score_lead_info


async def post_chat(client: AsyncClient, message: str, conversation_id: str | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return await client.post("/chat", json=payload)


@pytest.mark.anyio
async def test_chat_pricing_uses_rag() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/documents/ingest-demo")
        response = await post_chat(client, "How much does SEO cost?")

    body = response.json()

    assert response.status_code == 200
    assert body["intent"] == "pricing_question"
    assert any(event["agent_name"] == "RAG Agent" for event in body["trace"])
    assert any(token in body["final_response"] for token in ("$1,500", "$2,500", "pricing document"))


@pytest.mark.anyio
async def test_multiturn_lead_memory() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await post_chat(client, "I need SEO for my gym. My budget is $2000.")
        first_body = first.json()
        conversation_id = first_body["conversation_id"]

        second = await post_chat(client, "My name is Sara and my email is sara@example.com", conversation_id)
        second_body = second.json()
        conversation = await client.get(f"/conversations/{conversation_id}")
        leads = await client.get("/leads")

    conversation_body = conversation.json()
    lead = conversation_body["latest_lead"]

    assert first.status_code == 200
    assert second.status_code == 200
    assert second_body["conversation_id"] == conversation_id
    assert lead["service_interest"] == "SEO"
    assert lead["business_type"] == "gym"
    assert lead["budget"] == 2000
    assert lead["name"] == "Sara"
    assert lead["email"] == "sara@example.com"
    assert lead["lead_quality"] in {"warm", "hot"}
    assert len(leads.json()["leads"]) == 1


@pytest.mark.anyio
async def test_discount_request_creates_human_approval() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await post_chat(client, "Can you give me 70% discount and promise results?")
        approvals = await client.get("/approvals")

    body = response.json()
    approval_items = approvals.json()["approvals"]

    assert response.status_code == 200
    assert body["requires_human_approval"] is True
    assert approval_items
    assert approval_items[0]["status"] == "pending"
    assert any(word in body["final_response"].lower() for word in ("review", "approval", "team"))
    assert "promise results" not in body["final_response"].lower()


@pytest.mark.anyio
async def test_trace_includes_tool_calls() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await post_chat(client, "How much does website design cost?")
        body = response.json()
        trace_response = await client.get(f"/agent-runs/{body['agent_run_id']}/trace")

    trace_body = trace_response.json()

    assert response.status_code == 200
    assert any(event["agent_name"] == "RAG Agent" for event in body["trace"])
    assert any(tool_call["tool_name"] == "search_docs" for tool_call in trace_body["tool_calls"])


def test_lead_scoring() -> None:
    complete_score, complete_quality = score_lead_info(
        {
            "name": "Sara",
            "email": "sara@example.com",
            "phone": "555-123-4567",
            "business_type": "gym",
            "service_interest": "SEO",
            "budget": 3500,
            "timeline": "this week",
        }
    )
    incomplete_score, incomplete_quality = score_lead_info({"service_interest": "SEO"})

    assert complete_score == 100
    assert complete_quality == "hot"
    assert incomplete_score == 20
    assert incomplete_quality == "cold"
