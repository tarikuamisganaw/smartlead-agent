from functools import lru_cache

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "smartlead-agent-api"
    environment: str = "development"
    database_url: str = "sqlite:///./smartlead.db"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    model_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    chat_request_timeout_seconds: int = 45
    llm_node_timeout_seconds: int = 20
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 1
    agent_fast_mode: bool = True
    rag_cache_enabled: bool = True
    rag_provider: str = "local"
    rag_vector_dimension: int = 768
    rag_fallback_to_local: bool = True
    embedding_provider: str = "gemini"
    gemini_embedding_model: str = "text-embedding-004"
    local_embedding_model: str = "local-hash-embedding-v1"
    max_llm_calls_per_chat: int = 2
    estimated_input_cost_per_1m_tokens: float = 0
    estimated_output_cost_per_1m_tokens: float = 0
    auth_enabled: bool = True
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    default_organization_name: str = "BrightPath Marketing Agency"
    allow_dev_admin_bypass: bool = False
    reset_db_allowed: bool = False
    demo_owner_email: str | None = None
    demo_owner_password: str | None = None
    lead_sync_provider: str = "mock"
    google_sheets_credentials_json: str | None = None
    google_sheets_spreadsheet_id: str | None = None
    google_sheets_worksheet_name: str = "Leads"
    notification_providers: str | None = None
    notification_provider: str = "mock"
    slack_webhook_url: str | None = None
    resend_api_key: str | None = None
    owner_email: str | None = None
    from_email: str | None = None
    owner_name: str = "Business Owner"
    send_owner_notifications: bool = True
    send_approval_notifications: bool = True
    send_lead_sync_failure_notifications: bool = True
    send_customer_followup_emails: bool = False
    sync_leads_automatically: bool = True
    sync_only_complete_leads: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator(
        "agent_fast_mode",
        "rag_cache_enabled",
        "rag_fallback_to_local",
        "auth_enabled",
        "allow_dev_admin_bypass",
        "reset_db_allowed",
        "send_owner_notifications",
        "send_approval_notifications",
        "send_lead_sync_failure_notifications",
        "send_customer_followup_emails",
        "sync_leads_automatically",
        "sync_only_complete_leads",
        mode="before",
    )
    @classmethod
    def blank_bool_uses_default(cls, value, info: ValidationInfo):
        if value == "":
            return cls.model_fields[info.field_name].default
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
