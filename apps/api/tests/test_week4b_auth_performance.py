import sys

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app
from app.services.document_service import default_demo_data_dir, ingest_documents
from app.database import SessionLocal
from app.services import rag_service


async def register(client: AsyncClient, email: str, *, as_owner: bool = False) -> str:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
            "as_owner": as_owner,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_chat_latency_mock_mode() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "How much does SEO cost?"})

    body = response.json()

    assert response.status_code == 200
    assert body["total_latency_ms"] is not None
    assert body["total_latency_ms"] < 5000
    assert body["total_model_calls"] <= 2


def test_rag_index_cached() -> None:
    db = SessionLocal()
    try:
        ingest_documents(db, default_demo_data_dir(), clear_existing=True)
        rag_service.invalidate_rag_index()
        rag_service.search_docs(db, "How much does SEO cost?")
        first_index = rag_service._CACHED_INDEX
        rag_service.search_docs(db, "Do you build websites?")
        second_index = rag_service._CACHED_INDEX
    finally:
        db.close()
        rag_service.invalidate_rag_index()

    assert first_index is not None
    assert first_index is second_index


@pytest.mark.anyio
async def test_guest_chat_creates_anonymous_session(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "How much does SEO cost?"})
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["anonymous_session_token"]
    assert response.json()["trace"] == []


@pytest.mark.anyio
async def test_guest_cannot_access_admin_when_auth_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/leads")
        rag_response = await client.post("/rag/search", json={"query": "How much does SEO cost?"})
    get_settings.cache_clear()

    assert response.status_code == 401
    assert rag_response.status_code == 401


@pytest.mark.anyio
async def test_register_login_me(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "owner@example.com", as_owner=True)
        login = await client.post("/auth/login", json={"email": "owner@example.com", "password": "password123"})
        me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    get_settings.cache_clear()

    assert login.status_code == 200
    assert me.status_code == 200
    assert me.json()["memberships"][0]["role"] == "owner"


@pytest.mark.anyio
async def test_owner_can_access_dashboard(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "admin@example.com", as_owner=True)
        response = await client.get("/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    get_settings.cache_clear()

    assert response.status_code == 200


@pytest.mark.anyio
async def test_non_owner_cannot_access_owner_dashboard(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "regular-user@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        dashboard = await client.get("/dashboard/summary", headers=headers)
        leads = await client.get("/leads", headers=headers)
        rag_search = await client.post("/rag/search", json={"query": "How much does SEO cost?"}, headers=headers)
    get_settings.cache_clear()

    assert dashboard.status_code == 403
    assert leads.status_code == 403
    assert rag_search.status_code == 403


@pytest.mark.anyio
async def test_user_can_see_own_conversations(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "user@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        chat = await client.post("/chat", json={"message": "How much does SEO cost?"}, headers=headers)
        conversations = await client.get("/my/conversations", headers=headers)
    get_settings.cache_clear()

    assert chat.status_code == 200
    assert any(item["id"] == chat.json()["conversation_id"] for item in conversations.json()["conversations"])


@pytest.mark.anyio
async def test_non_owner_chat_response_hides_internal_agent_data(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "private-user@example.com")
        response = await client.post(
            "/chat",
            json={"message": "My name is Sara and my email is sara@example.com. I need SEO."},
            headers={"Authorization": f"Bearer {token}"},
        )
    get_settings.cache_clear()

    body = response.json()

    assert response.status_code == 200
    assert body["lead_info"] == {}
    assert body["trace"] == []
    assert body["total_latency_ms"] is None
    assert body["total_model_calls"] is None
    assert body["model_provider"] is None


@pytest.mark.anyio
async def test_user_cannot_see_other_user_conversation(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token_a = await register(client, "a@example.com")
        token_b = await register(client, "b@example.com")
        chat = await client.post("/chat", json={"message": "How much does SEO cost?"}, headers={"Authorization": f"Bearer {token_a}"})
        response = await client.get(
            f"/my/conversations/{chat.json()['conversation_id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
    get_settings.cache_clear()

    assert response.status_code == 404


@pytest.mark.anyio
async def test_admin_trace_access(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await register(client, "trace-owner@example.com", as_owner=True)
        headers = {"Authorization": f"Bearer {token}"}
        chat = await client.post("/chat", json={"message": "How much does SEO cost?"}, headers=headers)
        response = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace", headers=headers)
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["trace"]


@pytest.mark.anyio
async def test_guest_trace_blocked_when_auth_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("ALLOW_DEV_ADMIN_BYPASS", "false")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post("/chat", json={"message": "How much does SEO cost?"})
        response = await client.get(f"/agent-runs/{chat.json()['agent_run_id']}/trace")
    get_settings.cache_clear()

    assert response.status_code == 401


@pytest.mark.anyio
async def test_claim_anonymous_session(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        guest_chat = await client.post("/chat", json={"message": "How much does SEO cost?"})
        token = await register(client, "claim@example.com")
        claim = await client.post(
            "/auth/claim-anonymous-session",
            json={"session_token": guest_chat.json()["anonymous_session_token"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        conversations = await client.get("/my/conversations", headers={"Authorization": f"Bearer {token}"})
    get_settings.cache_clear()

    assert claim.status_code == 200
    assert claim.json()["claimed_conversations"] == 1
    assert conversations.json()["conversations"]


def test_reset_dev_db_refuses_production(monkeypatch) -> None:
    from app.scripts import reset_dev_db

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(sys, "argv", ["reset_dev_db.py", "--yes"])
    get_settings.cache_clear()

    with pytest.raises(SystemExit, match="production"):
        reset_dev_db.main()

    get_settings.cache_clear()


def test_reset_dev_db_requires_yes(monkeypatch) -> None:
    from app.scripts import reset_dev_db

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(sys, "argv", ["reset_dev_db.py"])
    get_settings.cache_clear()

    with pytest.raises(SystemExit, match="--yes"):
        reset_dev_db.main()

    get_settings.cache_clear()


def test_database_url_not_hardcoded_to_sqlite(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/test")
    get_settings.cache_clear()
    try:
        assert get_settings().database_url == "postgresql://example/test"
    finally:
        get_settings.cache_clear()
