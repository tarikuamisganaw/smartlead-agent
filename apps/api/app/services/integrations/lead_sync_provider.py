from typing import Protocol

from app.config import get_settings


class LeadSyncProvider(Protocol):
    provider_name: str

    def is_configured(self) -> bool:
        ...

    def sync_lead(self, lead: dict, context: dict | None = None) -> dict:
        ...


def get_lead_sync_provider() -> LeadSyncProvider:
    provider = get_settings().lead_sync_provider.lower().strip()
    if provider == "google_sheets":
        from app.services.integrations.google_sheets_provider import GoogleSheetsLeadSyncProvider

        return GoogleSheetsLeadSyncProvider()

    from app.services.integrations.mock_lead_sync_provider import MockLeadSyncProvider

    return MockLeadSyncProvider()
