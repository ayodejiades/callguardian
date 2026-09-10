"""api/settings.py — pydantic-settings validated environment. Fails loudly at boot."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    demo_mode: bool = False
    deploy_url: str = "http://localhost:8000"

    calle_api_key: str = ""
    calle_base_url: str = "https://api.heycall-e.com"
    calle_account_email: str = ""
    session_secret: str = "dev-only-secret-change-me"


settings = Settings()
