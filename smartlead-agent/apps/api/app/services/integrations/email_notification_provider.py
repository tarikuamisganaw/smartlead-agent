import httpx

from app.config import get_settings


class EmailNotificationProvider:
    provider_name = "email"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.resend_api_key and self.settings.owner_email and self.settings.from_email)

    def notify_owner_new_lead(self, lead: dict, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _skipped()
        subject = f"New SmartLead lead: {lead.get('lead_quality') or 'new'} lead for {lead.get('service_interest') or 'unknown service'}"
        body = "\n".join(
            [
                f"Hello {self.settings.owner_name},",
                "",
                "A new lead was captured by SmartLead Agent.",
                "",
                f"Name: {lead.get('name') or 'Unknown'}",
                f"Email: {lead.get('email') or 'Unknown'}",
                f"Phone: {lead.get('phone') or 'Unknown'}",
                f"Business type: {lead.get('business_type') or 'Unknown'}",
                f"Service interest: {lead.get('service_interest') or 'Unknown'}",
                f"Budget: {_money(lead.get('budget'))}",
                f"Timeline: {lead.get('timeline') or 'Unknown'}",
                f"Lead score: {lead.get('lead_score') if lead.get('lead_score') is not None else 'Unknown'}",
                f"Lead quality: {lead.get('lead_quality') or 'Unknown'}",
                f"Conversation ID: {lead.get('conversation_id') or 'Unknown'}",
                f"External sync: {lead.get('external_sync_status') or 'Not synced yet'}",
                "",
                "Review this lead in the SmartLead dashboard.",
            ]
        )
        return self._send(subject, body)

    def notify_approval_required(self, approval: dict, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _skipped()
        subject = f"SmartLead approval required: {approval.get('action_type') or 'review_request'}"
        body = "\n".join(
            [
                f"Hello {self.settings.owner_name},",
                "",
                "SmartLead Agent created a human approval request.",
                "",
                f"Action type: {approval.get('action_type') or 'Unknown'}",
                f"Reason: {approval.get('reason') or 'Human review required.'}",
                f"Draft response: {approval.get('draft_response') or 'None'}",
                f"Agent run ID: {approval.get('agent_run_id') or 'Unknown'}",
                "",
                "Review this request in the SmartLead dashboard.",
            ]
        )
        return self._send(subject, body)

    def notify_lead_sync_failure(self, lead: dict, error: str, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _skipped()
        provider = (context or {}).get("lead_sync_provider") or lead.get("external_sync_provider") or "unknown"
        subject = "SmartLead lead sync failed"
        body = "\n".join(
            [
                f"Hello {self.settings.owner_name},",
                "",
                "A SmartLead external lead sync attempt failed.",
                "",
                f"Lead ID: {lead.get('id') or 'Unknown'}",
                f"Provider: {provider}",
                f"Error: {_safe_error(error)}",
                "",
                "Review this lead in the SmartLead dashboard.",
            ]
        )
        return self._send(subject, body)

    def notify_owner(self, message: str, lead: dict | None = None, context: dict | None = None) -> dict:
        if not self.is_configured():
            return _skipped()
        return self._send("SmartLead notification", message)

    def _send(self, subject: str, text: str) -> dict:
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.settings.from_email,
                    "to": [self.settings.owner_email],
                    "subject": subject,
                    "text": text,
                },
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            return {
                "status": "sent",
                "provider": self.provider_name,
                "message": "Owner email notification sent.",
                "external_id": payload.get("id"),
                "raw": {"id": payload.get("id")},
            }
        except Exception as exc:  # pragma: no cover - external service behavior.
            return _failed(f"Email notification failed: {_safe_error(exc)}")


def _failed(message: str) -> dict:
    return {
        "status": "failed",
        "provider": "email",
        "message": message,
        "external_id": None,
        "raw": {},
    }


def _skipped() -> dict:
    return {
        "status": "skipped",
        "provider": "email",
        "message": "Email provider is not configured. Skipping email notification.",
        "external_id": None,
        "raw": {},
    }


def _safe_error(error: object) -> str:
    return str(error).replace("\n", " ")[:300]


def _money(value: int | None) -> str:
    if value is None:
        return "Unknown"
    return f"${value}"
