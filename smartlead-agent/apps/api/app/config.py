from functools import lru_cache

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
