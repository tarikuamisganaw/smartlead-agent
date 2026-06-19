import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.services.integrations.email_notification_provider import EmailNotificationProvider
from app.services.integrations.slack_notification_provider import SlackNotificationProvider
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
    assert body["email_optional"] is True
    assert body["notification_configured"]["email"] is False


@pytest.mark.anyio
async def test_app_runs_without_email_env(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "slack")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
    assert any(tool["tool_name"] == "notify_sync_failure_mock" and tool["status"] == "success" for tool in tool_calls)


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


@pytest.mark.anyio
async def test_mock_notification_default() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={
                "message": (
                    "My name is Sara and my email is sara@example.com. "
                    "I need SEO for my gym. My budget is $3000 and I want to start next week."
                )
            },
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert any(tool["tool_name"] == "notify_owner_mock" and tool["status"] == "success" for tool in tool_calls)


@pytest.mark.anyio
async def test_slack_provider_missing_config_fails_safely(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "slack")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "I need SEO for my gym. My email is hot@example.com. My budget is $3000."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    tool_calls = trace.json()["tool_calls"]
    notification_tool = next(tool for tool in tool_calls if tool["tool_name"] == "notify_owner_slack")

    assert chat.status_code == 200
    assert notification_tool["status"] == "failed"
    assert "not configured" in notification_tool["tool_output"]["message"].lower()
    assert "http" not in str(notification_tool["tool_output"]).lower()


@pytest.mark.anyio
async def test_email_provider_missing_config_fails_safely(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "email")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "I need website design. My email is hot@example.com. My budget is $3000."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    tool_calls = trace.json()["tool_calls"]
    notification_tool = next(tool for tool in tool_calls if tool["tool_name"] == "notify_owner_email")

    assert chat.status_code == 200
    assert notification_tool["status"] == "skipped"
    assert "skipping email notification" in notification_tool["tool_output"]["message"].lower()


@pytest.mark.anyio
async def test_chat_works_without_email_env(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "mock")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "I need SEO for my gym. My email is noemailenv@example.com. My budget is $3000."},
        )
        leads = await client.get("/leads")
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    assert chat.status_code == 200
    assert leads.json()["leads"]
    assert any(tool["tool_name"] == "notify_owner_mock" for tool in trace.json()["tool_calls"])


@pytest.mark.anyio
async def test_email_not_required_when_slack_selected(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "slack")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.test/slack")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    monkeypatch.setattr(
        SlackNotificationProvider,
        "_post",
        lambda self, text: {
            "status": "sent",
            "provider": "slack",
            "message": "Slack notification sent.",
            "external_id": None,
            "raw": {},
        },
    )
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "I need SEO for my gym. My email is slackonly@example.com. My budget is $3000."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert any(tool["tool_name"] == "notify_owner_slack" and tool["status"] == "success" for tool in tool_calls)
    assert not any(tool["tool_name"] == "notify_owner_email" for tool in tool_calls)


@pytest.mark.anyio
async def test_slack_email_combo_email_failure_does_not_block_slack(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "slack,email")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.test/slack")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    monkeypatch.setattr(
        SlackNotificationProvider,
        "_post",
        lambda self, text: {
            "status": "sent",
            "provider": "slack",
            "message": "Slack notification sent.",
            "external_id": None,
            "raw": {},
        },
    )
    get_settings.cache_clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "I need website design. My email is combo@example.com. My budget is $3000."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert any(tool["tool_name"] == "notify_owner_slack" and tool["status"] == "success" for tool in tool_calls)
    assert any(tool["tool_name"] == "notify_owner_email" and tool["status"] == "skipped" for tool in tool_calls)


@pytest.mark.anyio
async def test_approval_notification_created() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post("/chat", json={"message": "Can you give me 70% discount and promise results?"})
        approvals = await client.get("/approvals")
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert approvals.json()["approvals"]
    assert any(tool["tool_name"] == "notify_approval_mock" and tool["status"] == "success" for tool in tool_calls)


@pytest.mark.anyio
async def test_integrations_status_includes_notifications() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/integrations/status")

    body = response.json()

    assert response.status_code == 200
    assert body["notification_providers"] == ["mock"]
    assert body["notification_configured"]["mock"] is True
    assert body["send_customer_followup_emails"] is False
    assert "SLACK_WEBHOOK_URL" not in str(body)
    assert "RESEND_API_KEY" not in str(body)


@pytest.mark.anyio
async def test_customer_followup_disabled_by_default() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            "/chat",
            json={"message": "My email is customer@example.com. I need SEO and my budget is $3000."},
        )
        trace = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")

    tool_calls = trace.json()["tool_calls"]

    assert chat.status_code == 200
    assert not any("customer" in tool["tool_name"] for tool in tool_calls)
    assert any(tool["tool_name"].startswith("notify_owner_") for tool in tool_calls)


def test_slack_notification_skipped_without_env(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
    get_settings.cache_clear()

    provider = SlackNotificationProvider()

    assert provider.is_configured() is False
    pytest.skip("Real Slack notification test skipped because SLACK_WEBHOOK_URL is not configured.")


def test_slack_notification_if_env_exists(monkeypatch) -> None:
    webhook_url = os.environ.get("SMARTLEAD_TEST_SLACK_WEBHOOK_URL")
    if not webhook_url:
        pytest.skip("Set SMARTLEAD_TEST_SLACK_WEBHOOK_URL to run the real Slack notification test.")

    monkeypatch.setenv("SLACK_WEBHOOK_URL", webhook_url)
    get_settings.cache_clear()
    provider = SlackNotificationProvider()
    result = provider.notify_owner_new_lead(
        {
            "name": "Test Lead",
            "email": "test@example.com",
            "service_interest": "SEO",
            "budget": 3000,
            "timeline": "next week",
            "lead_score": 90,
            "lead_quality": "hot",
        }
    )
    get_settings.cache_clear()

    assert result["status"] == "sent"


def test_email_notification_skipped_without_env(monkeypatch) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    get_settings.cache_clear()

    provider = EmailNotificationProvider()

    assert provider.is_configured() is False
    pytest.skip("Real email notification test skipped because Resend env vars are not configured.")


def test_email_notification_if_env_exists(monkeypatch) -> None:
    api_key = os.environ.get("SMARTLEAD_TEST_RESEND_API_KEY")
    owner_email = os.environ.get("SMARTLEAD_TEST_OWNER_EMAIL")
    from_email = os.environ.get("SMARTLEAD_TEST_FROM_EMAIL")
    if not (api_key and owner_email and from_email):
        pytest.skip(
            "Set SMARTLEAD_TEST_RESEND_API_KEY, SMARTLEAD_TEST_OWNER_EMAIL, and SMARTLEAD_TEST_FROM_EMAIL "
            "to run the real email notification test."
        )

    monkeypatch.setenv("RESEND_API_KEY", api_key)
    monkeypatch.setenv("OWNER_EMAIL", owner_email)
    monkeypatch.setenv("FROM_EMAIL", from_email)
    get_settings.cache_clear()
    provider = EmailNotificationProvider()
    result = provider.notify_owner_new_lead(
        {
            "name": "Test Lead",
            "email": "test@example.com",
            "service_interest": "SEO",
            "budget": 3000,
            "timeline": "next week",
            "lead_score": 90,
            "lead_quality": "hot",
            "conversation_id": "test",
        }
    )
    get_settings.cache_clear()

    assert result["status"] == "sent"
