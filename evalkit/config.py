"""Typed settings (Pydantic v2)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    eval_target: str = "mock"  # mock | http | gemini
    agent_base_url: str = "http://localhost:8000"

    google_api_key: str = ""
    model_name: str = "gemini-2.5-flash"

    pass_threshold: float = 1.0

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    @property
    def gemini_ready(self) -> bool:
        return bool(self.google_api_key)

    @property
    def langfuse_ready(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


settings = Settings()
