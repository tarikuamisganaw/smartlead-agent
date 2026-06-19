from typing import Protocol

from app.config import get_settings


class NotificationProvider(Protocol):
    provider_name: str

    def is_configured(self) -> bool:
        ...

<<<<<<< HEAD
    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
=======
    def notify_owner_new_lead(self, lead: dict, context: dict | None = None) -> dict:
>>>>>>> eval-bakup
        ...

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        ...

<<<<<<< HEAD

def get_notification_provider() -> NotificationProvider:
    settings = get_settings()
    provider = settings.notification_provider.lower().strip()

    if provider == "slack":
        from app.services.integrations.slack_notification_provider import SlackNotificationProvider

        return SlackNotificationProvider()

    if provider == "email":
        from app.services.integrations.email_notification_provider import EmailNotificationProvider

        return EmailNotificationProvider()

    from app.services.integrations.mock_notification_provider import MockNotificationProvider

    return MockNotificationProvider()
=======
    def notify_lead_sync_failure(self, lead: dict, error: str, context: dict | None = None) -> dict:
        ...


def get_notification_providers() -> list[NotificationProvider]:
    provider_names = _configured_provider_names()
    providers: list[NotificationProvider] = []
    for provider_name in provider_names:
        if provider_name == "slack":
            from app.services.integrations.slack_notification_provider import SlackNotificationProvider

            providers.append(SlackNotificationProvider())
        elif provider_name == "email":
            from app.services.integrations.email_notification_provider import EmailNotificationProvider

            providers.append(EmailNotificationProvider())
        elif provider_name == "mock":
            from app.services.integrations.mock_notification_provider import MockNotificationProvider

            providers.append(MockNotificationProvider())

    if providers:
        return providers

    from app.services.integrations.mock_notification_provider import MockNotificationProvider

    return [MockNotificationProvider()]


def get_notification_provider() -> NotificationProvider:
    return get_notification_providers()[0]


def _configured_provider_names() -> list[str]:
    settings = get_settings()
    configured = settings.notification_providers
    if configured is None or not configured.strip():
        configured = settings.notification_provider or "mock"

    allowed = {"mock", "slack", "email"}
    names = []
    for item in configured.split(","):
        name = item.strip().lower()
        if not name or name not in allowed or name in names:
            continue
        names.append(name)

    if not names:
        if settings.slack_webhook_url:
            return ["slack"]
        return ["mock"]
    if "mock" in names and len(names) > 1:
        return ["mock"]
    return names
>>>>>>> eval-bakup
