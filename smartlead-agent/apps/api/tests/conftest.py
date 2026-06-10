import os
import tempfile

import pytest

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/smartlead_agent_test.db"
os.environ["MODEL_PROVIDER"] = "mock"
os.environ["AUTH_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_ADMIN_BYPASS"] = "true"
os.environ["LEAD_SYNC_PROVIDER"] = "mock"
os.environ["NOTIFICATION_PROVIDERS"] = "mock"
os.environ["NOTIFICATION_PROVIDER"] = "mock"
os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = ""
os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"] = ""
os.environ["SLACK_WEBHOOK_URL"] = ""
os.environ["RESEND_API_KEY"] = ""
os.environ["OWNER_EMAIL"] = ""
os.environ["FROM_EMAIL"] = ""


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_settings_cache(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ALLOW_DEV_ADMIN_BYPASS", "true")
    monkeypatch.setenv("LEAD_SYNC_PROVIDER", "mock")
    monkeypatch.setenv("NOTIFICATION_PROVIDERS", "mock")
    monkeypatch.setenv("NOTIFICATION_PROVIDER", "mock")
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("OWNER_EMAIL", "")
    monkeypatch.setenv("FROM_EMAIL", "")
    monkeypatch.setenv("SEND_CUSTOMER_FOLLOWUP_EMAILS", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_database():
    from app import models  # noqa: F401
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
