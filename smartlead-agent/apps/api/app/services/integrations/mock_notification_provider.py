class MockNotificationProvider:
    provider_name = "mock"

    def is_configured(self) -> bool:
        return True

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
