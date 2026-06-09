import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.services.lead_service import create_or_update_lead, sync_lead_external


async def register(client: AsyncClient, email: str, *, as_owner: bool = False) -> str:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Integration Tester",
            "as_owner": as_owner,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_mock_lead_sync_default() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "My name is Sara and my email is sara@example.com. I need SEO for my gym."},
        )
        leads = await client.get("/leads")
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    lead = leads.json()["leads"][0]
    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert lead["external_sync_status"] == "synced"
    assert lead["external_sync_provider"] == "mock"
    assert any(tool["tool_name"] == "sync_lead_mock" and tool["status"] == "success" for tool in tool_calls)


def test_google_sheets_provider_not_configured_fails_safely(monkeypatch) -> None:
    monkeypatch.setenv("LEAD_SYNC_PROVIDER", "google_sheets")
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    get_settings.cache_clear()

    db = SessionLocal()
    try:
        lead = create_or_update_lead(
            db,
            conversation_id="manual-test-conversation",
            lead_info={"email": "sara@example.com", "service_interest": "SEO"},
            lead_score=60,
            lead_quality="warm",
        )
        result = sync_lead_external(db, lead, force=True)
        db.refresh(lead)
    finally:
        db.close()
        get_settings.cache_clear()

    assert result["status"] == "not_configured"
    assert lead.external_sync_status == "not_configured"
    assert "not configured" in (lead.external_sync_error or "").lower()


@pytest.mark.anyio
async def test_manual_sync_endpoint_mock() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/chat",
            json={"message": "I need website design for my clinic. My email is clinic@example.com."},
        )
        leads = await client.get("/leads")
        lead_id = leads.json()["leads"][0]["id"]
        response = await client.post(f"/leads/{lead_id}/sync")

    body = response.json()

    assert response.status_code == 200
    assert body["lead"]["external_sync_status"] == "synced"
    assert body["sync_result"]["status"] == "mock_synced"


@pytest.mark.anyio
async def test_integrations_status_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/integrations/status")

    body = response.json()

    assert response.status_code == 200
    assert body["lead_sync"]["provider"] == "mock"
    assert body["lead_sync"]["configured"] is True
    assert body["notification"]["provider"] == "mock"


@pytest.mark.anyio
async def test_sync_requires_owner_when_auth_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        owner_token = await register(client, "sync-owner@example.com", as_owner=True)
        headers = {"Authorization": f"Bearer {owner_token}"}
        await client.post(
            "/chat",
            json={"message": "I need SEO for my gym. My email is ownerlead@example.com."},
            headers=headers,
        )
        leads = await client.get("/leads", headers=headers)
        lead_id = leads.json()["leads"][0]["id"]
        blocked = await client.post(f"/leads/{lead_id}/sync")
        allowed = await client.post(f"/leads/{lead_id}/sync", headers=headers)
    get_settings.cache_clear()

    assert blocked.status_code == 401
    assert allowed.status_code == 200


@pytest.mark.anyio
async def test_sync_failure_does_not_fail_chat(monkeypatch) -> None:
    monkeypatch.setenv("LEAD_SYNC_PROVIDER", "google_sheets")
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "My email is sara@example.com and I need paid ads."},
        )
        leads = await client.get("/leads")
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    lead = leads.json()["leads"][0]
    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert chat.json()["final_response"]
    assert lead["external_sync_status"] == "not_configured"
    assert any(tool["tool_name"] == "sync_lead_google_sheets" and tool["status"] == "failed" for tool in tool_calls)


@pytest.mark.anyio
async def test_trace_includes_sync_tool_calls() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "How much does website design cost? My email is web@example.com."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    tool_calls = trace.json()["tool_calls"]

    assert any(tool["tool_name"] == "search_docs" for tool in tool_calls)
    assert any(tool["tool_name"] == "sync_lead_mock" for tool in tool_calls)


@pytest.mark.anyio
async def test_sync_only_complete_leads_can_skip(monkeypatch) -> None:
    monkeypatch.setenv("SYNC_ONLY_COMPLETE_LEADS", "true")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post("/chat", json={"message": "I need SEO for my gym."})
        leads = await client.get("/leads")
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    lead = leads.json()["leads"][0]
    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert lead["external_sync_status"] is None
    assert any(tool["tool_name"] == "sync_lead_mock" and tool["status"] == "skipped" for tool in tool_calls)


def test_google_sheets_provider_if_env_exists(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    get_settings.cache_clear()
    pytest.skip("Real Google Sheets sync is manual: enable with local env values and use /leads/{lead_id}/sync.")
