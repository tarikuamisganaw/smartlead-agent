import json
from typing import Any

from app.config import get_settings


LEAD_HEADERS = [
    "created_at",
    "conversation_id",
    "lead_id",
    "name",
    "email",
    "phone",
    "business_type",
    "service_interest",
    "budget",
    "timeline",
    "lead_score",
    "lead_quality",
    "status",
    "source",
    "external_sync_provider",
]


class GoogleSheetsLeadSyncProvider:
    provider_name = "google_sheets"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.google_sheets_credentials_json and self.settings.google_sheets_spreadsheet_id)

    def sync_lead(self, lead: dict, context: dict | None = None) -> dict:
        if not self.settings.google_sheets_credentials_json:
            return _failed("Google Sheets credentials are not configured.")
        if not self.settings.google_sheets_spreadsheet_id:
            return _failed("Google Sheets spreadsheet ID is not configured.")

        try:
            service = self._build_service()
            spreadsheet_id = self.settings.google_sheets_spreadsheet_id
            worksheet_name = self.settings.google_sheets_worksheet_name or "Leads"
            self._ensure_worksheet(service, spreadsheet_id, worksheet_name)
            self._ensure_header(service, spreadsheet_id, worksheet_name)
<<<<<<< HEAD
            row = _lead_row(lead)
            response = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=f"{worksheet_name}!A:O",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row]},
                )
                .execute()
            )
=======
            if lead.get("external_sync_id"):
                response = (
                    service.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=spreadsheet_id,
                        range=lead["external_sync_id"],
                        valueInputOption="USER_ENTERED",
                        body={"values": [_lead_row(lead)]},
                    )
                    .execute()
                )
            else:
                response = (
                    service.spreadsheets()
                    .values()
                    .append(
                        spreadsheetId=spreadsheet_id,
                        range=f"{worksheet_name}!A:O",
                        valueInputOption="USER_ENTERED",
                        insertDataOption="INSERT_ROWS",
                        body={"values": [_lead_row(lead)]},
                    )
                    .execute()
                )
>>>>>>> eval-bakup
            external_id = response.get("updates", {}).get("updatedRange") or response.get("tableRange")
            return {
                "status": "synced",
                "provider": self.provider_name,
                "external_id": external_id,
                "message": "Lead synced to Google Sheets.",
                "raw": _safe_raw_response(response),
            }
        except Exception as exc:  # pragma: no cover - external API behavior.
            return _failed(f"Google Sheets sync failed: {_safe_error(exc)}")

    def _build_service(self):
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except Exception as exc:
            raise RuntimeError("Google Sheets dependencies are not installed.") from exc

        try:
            credentials_info = json.loads(self.settings.google_sheets_credentials_json or "")
        except json.JSONDecodeError as exc:
            raise RuntimeError("Google Sheets credentials JSON is invalid.") from exc

        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def _ensure_worksheet(self, service, spreadsheet_id: str, worksheet_name: str) -> None:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
<<<<<<< HEAD
        sheets = spreadsheet.get("sheets", [])
        if any(sheet.get("properties", {}).get("title") == worksheet_name for sheet in sheets):
=======
        if any(sheet.get("properties", {}).get("title") == worksheet_name for sheet in spreadsheet.get("sheets", [])):
>>>>>>> eval-bakup
            return
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": worksheet_name}}}]},
        ).execute()

    def _ensure_header(self, service, spreadsheet_id: str, worksheet_name: str) -> None:
        response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=f"{worksheet_name}!A1:O1")
            .execute()
        )
<<<<<<< HEAD
        values = response.get("values", [])
        if values:
=======
        if response.get("values"):
>>>>>>> eval-bakup
            return
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{worksheet_name}!A1:O1",
            valueInputOption="USER_ENTERED",
            body={"values": [LEAD_HEADERS]},
        ).execute()


def _lead_row(lead: dict) -> list[Any]:
    return [
        lead.get("created_at") or "",
        lead.get("conversation_id") or "",
        lead.get("id") or "",
        lead.get("name") or "",
        lead.get("email") or "",
        lead.get("phone") or "",
        lead.get("business_type") or "",
        lead.get("service_interest") or "",
        lead.get("budget") or "",
        lead.get("timeline") or "",
        lead.get("lead_score") or "",
        lead.get("lead_quality") or "",
        lead.get("status") or "",
        "SmartLead Agent",
        "google_sheets",
    ]


def _failed(message: str) -> dict:
    return {
        "status": "failed",
        "provider": "google_sheets",
        "external_id": None,
        "message": message,
        "raw": {},
    }


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:500]


def _safe_raw_response(response: dict) -> dict:
    return {
        "spreadsheetId": response.get("spreadsheetId"),
        "tableRange": response.get("tableRange"),
        "updates": response.get("updates", {}),
    }
