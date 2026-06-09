from app.config import get_settings


class EmailNotificationProvider:
    provider_name = "email"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.resend_api_key and self.settings.owner_email and self.settings.from_email)

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        return _skipped(self.provider_name)

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        return _skipped(self.provider_name)


def _skipped(provider: str) -> dict:
    return {
        "status": "skipped",
        "provider": provider,
        "message": "Email notification provider is reserved for a later phase.",
        "raw": {},
    }
