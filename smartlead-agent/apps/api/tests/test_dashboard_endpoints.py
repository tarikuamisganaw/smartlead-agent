import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def post_chat(client: AsyncClient, message: str, conversation_id: str | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return await client.post("/chat", json=payload)


@pytest.mark.anyio
async def test_get_conversations() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat_response = await post_chat(client, "I need SEO for my gym. My budget is $2000.")
        response = await client.get("/conversations")

    body = response.json()

    assert response.status_code == 200
    assert body["conversations"]
    assert body["conversations"][0]["id"] == chat_response.json()["conversation_id"]
    assert body["conversations"][0]["last_message"]


@pytest.mark.anyio
async def test_get_conversation_agent_runs() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat_response = await post_chat(client, "How much does SEO cost?")
        body = chat_response.json()
        response = await client.get(f"/conversations/{body['conversation_id']}/agent-runs")

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["conversation_id"] == body["conversation_id"]
    assert response_body["agent_runs"][0]["id"] == body["agent_run_id"]


@pytest.mark.anyio
async def test_get_agent_runs() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat_response = await post_chat(client, "How much does website design cost?")
        response = await client.get("/agent-runs")

    body = response.json()

    assert response.status_code == 200
    assert body["agent_runs"]
    assert body["agent_runs"][0]["id"] == chat_response.json()["agent_run_id"]


@pytest.mark.anyio
async def test_dashboard_summary() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/documents/ingest-demo")
        await post_chat(client, "I need SEO for my gym. My budget is $2000.")
        await post_chat(client, "Can you give me 70% discount and promise results?")
        response = await client.get("/dashboard/summary")

    body = response.json()

    assert response.status_code == 200
    assert body["total_conversations"] == 2
    assert body["total_leads"] >= 1
    assert body["pending_approvals"] == 1
    assert body["total_documents"] >= 6
    assert body["total_document_chunks"] > 0
    assert body["recent_agent_runs"]


@pytest.mark.anyio
async def test_get_documents_and_approvals() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/documents/ingest-demo")
        await post_chat(client, "Can you give me 70% discount and promise results?")
        documents = await client.get("/documents")
        approvals = await client.get("/approvals")

    assert documents.status_code == 200
    assert documents.json()["documents"]
    assert approvals.status_code == 200
    assert approvals.json()["approvals"][0]["status"] == "pending"
