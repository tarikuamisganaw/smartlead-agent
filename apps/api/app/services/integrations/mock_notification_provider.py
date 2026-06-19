class MockNotificationProvider:
    provider_name = "mock"

    def is_configured(self) -> bool:
        return True

<<<<<<< HEAD
    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        return {
            "status": "mock_sent",
            "provider": self.provider_name,
            "message": "Mock owner notification completed. No external service was called.",
            "raw": {},
        }

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        return {
            "status": "mock_sent",
            "provider": self.provider_name,
            "message": "Mock approval notification completed. No external service was called.",
            "raw": {},
        }
=======
    def notify_owner_new_lead(self, lead: dict, context: dict | None = None) -> dict:
        return _mock_sent("Mock new lead notification completed. No external service was called.")

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        return _mock_sent("Mock approval notification completed. No external service was called.")

    def notify_lead_sync_failure(self, lead: dict, error: str, context: dict | None = None) -> dict:
        return _mock_sent("Mock lead sync failure notification completed. No external service was called.")

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        return self.notify_owner_new_lead(lead or {}, context)


def _mock_sent(message: str) -> dict:
    return {
        "status": "mock_sent",
        "provider": "mock",
        "message": message,
        "external_id": None,
        "raw": {},
    }
>>>>>>> eval-bakup
