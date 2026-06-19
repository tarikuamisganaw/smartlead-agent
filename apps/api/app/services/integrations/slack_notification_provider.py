<<<<<<< HEAD
=======
import httpx

>>>>>>> eval-bakup
from app.config import get_settings


class SlackNotificationProvider:
    provider_name = "slack"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.slack_webhook_url)

<<<<<<< HEAD
    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        return self._not_implemented()

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        return self._not_implemented()

    def _not_implemented(self) -> dict:
        return {
            "status": "skipped",
            "provider": self.provider_name,
            "message": "Slack notification provider is reserved for a later phase.",
            "raw": {},
        }
=======
    def notify_owner_new_lead(self, lead: dict, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _failed("Slack webhook URL is not configured.")
        quality = lead.get("lead_quality") or "new"
        score = lead.get("lead_score")
        text = (
            f"New {quality} lead from SmartLead Agent: "
            f"{lead.get('name') or 'Unnamed lead'}, {lead.get('service_interest') or 'unknown service'}, "
            f"budget {_money(lead.get('budget'))}, timeline {lead.get('timeline') or 'unknown'}."
        )
        if score is not None:
            text += f" Score: {score}."
        if lead.get("email"):
            text += f" Email: {lead['email']}."
        if lead.get("business_type"):
            text += f" Business: {lead['business_type']}."
        text += " Review in the SmartLead dashboard."
        return self._post(text)

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _failed("Slack webhook URL is not configured.")
        text = (
            f"Approval required in SmartLead Agent: {approval.get('action_type') or 'review_request'}. "
            f"Reason: {approval.get('reason') or 'Human review required.'} "
            f"Agent run: {approval.get('agent_run_id') or 'unknown'}. "
            "Review in the SmartLead dashboard."
        )
        return self._post(text)

    def notify_lead_sync_failure(self, lead: dict, error: str, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _failed("Slack webhook URL is not configured.")
        provider = (context or {}).get("lead_sync_provider") or lead.get("external_sync_provider") or "unknown"
        text = (
            f"SmartLead lead sync failed. Lead: {lead.get('id') or 'unknown'}. "
            f"Provider: {provider}. Error: {_safe_error(error)}."
        )
        return self._post(text)

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _failed("Slack webhook URL is not configured.")
        return self._post(message)

    def _post(self, text: str) -> dict:
        try:
            response = httpx.post(
                self.settings.slack_webhook_url or "",
                json={"text": text},
                timeout=10,
            )
            response.raise_for_status()
            return {
                "status": "sent",
                "provider": self.provider_name,
                "message": "Slack notification sent.",
                "external_id": None,
                "raw": {"status_code": response.status_code},
            }
        except Exception as exc:  # pragma: no cover - external service behavior.
            return _failed(f"Slack notification failed: {_safe_error(exc)}")


def _failed(message: str) -> dict:
    return {
        "status": "failed",
        "provider": "slack",
        "message": message,
        "external_id": None,
        "raw": {},
    }


def _safe_error(error: object) -> str:
    return str(error).replace("\n", " ")[:300]


def _money(value: int | None) -> str:
    if value is None:
        return "unknown"
    return f"${value}"
>>>>>>> eval-bakup
