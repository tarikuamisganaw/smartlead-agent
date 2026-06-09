from typing import Protocol

from app.config import get_settings


class NotificationProvider(Protocol):
    provider_name: str

    def is_configured(self) -> bool:
        ...

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        ...

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        ...


def get_notification_provider() -> NotificationProvider:
    provider = get_settings().notification_provider.lower().strip()
    if provider == "slack":
        from app.services.integrations.slack_notification_provider import SlackNotificationProvider

        return SlackNotificationProvider()
    if provider == "email":
        from app.services.integrations.email_notification_provider import EmailNotificationProvider

        return EmailNotificationProvider()

    from app.services.integrations.mock_notification_provider import MockNotificationProvider

    return MockNotificationProvider()
