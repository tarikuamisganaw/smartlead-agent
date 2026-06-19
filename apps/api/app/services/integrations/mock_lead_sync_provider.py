class MockLeadSyncProvider:
    provider_name = "mock"

    def is_configured(self) -> bool:
        return True

    def sync_lead(self, lead: dict, context: dict | None = None) -> dict:
        return {
            "status": "mock_synced",
            "provider": self.provider_name,
<<<<<<< HEAD
            "external_id": None,
=======
            "external_id": f"mock:{lead.get('id') or 'lead'}",
>>>>>>> eval-bakup
            "message": "Mock lead sync completed. No external service was called.",
            "raw": {},
        }
