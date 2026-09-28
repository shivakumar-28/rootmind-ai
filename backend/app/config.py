from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    hindsight_api_key: str = ""
    hindsight_base_url: str = ""
    hindsight_bank_id: str = "devmemory-ai"
    groq_model: str = "openai/gpt-oss-120b"
    frontend_origins: str = "http://localhost:5173"
    database_path: str = "./data/devmemory.db"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
