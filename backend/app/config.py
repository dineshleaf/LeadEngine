import os

from pydantic_settings import BaseSettings
from typing import Optional


def _get_database_url() -> str:
    """Build the async database URL from environment variables."""
    # Railway provides DATABASE_URL in postgres:// format
    url = os.environ.get("DATABASE_URL", "")
    if url:
        # Convert postgres:// to postgresql+asyncpg://
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    return "sqlite+aiosqlite:///./leadengine.db"


class Settings(BaseSettings):
    # Database
    database_url: str = _get_database_url()

    # Server
    host: str = "0.0.0.0"
    port: int = int(os.environ.get("PORT", "8000"))
    debug: bool = os.environ.get("RAILWAY_ENVIRONMENT") is None

    # Rate Limiting
    requests_per_second: float = 2.0
    concurrent_analyses: int = 5

    # Optional API Keys
    serpapi_key: Optional[str] = None
    hunter_io_key: Optional[str] = None
    meta_ad_library_token: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Scraper Settings
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    request_timeout: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
