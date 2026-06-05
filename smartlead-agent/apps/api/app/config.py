from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "smartlead-agent-api"
    database_url: str = "sqlite:///./smartlead_agent.db"
    model_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 1
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
