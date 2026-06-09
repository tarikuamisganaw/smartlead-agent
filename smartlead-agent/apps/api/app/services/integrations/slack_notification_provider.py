from app.config import get_settings


class SlackNotificationProvider:
    provider_name = "slack"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.slack_webhook_url)

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        return _skipped(self.provider_name)

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        return _skipped(self.provider_name)


def _skipped(provider: str) -> dict:
    return {
        "status": "skipped",
        "provider": provider,
        "message": "Slack notification provider is reserved for a later phase.",
        "raw": {},
    }
