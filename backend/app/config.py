import os
import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database — Railway provides DATABASE_URL in postgres:// format
    # We need to convert it to postgresql+asyncpg:// for SQLAlchemy async
    database_url: str = "sqlite+aiosqlite:///./leadengine.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

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

    @model_validator(mode="after")
    def fix_database_url(self):
        """Convert Railway's postgres:// URL to async-compatible format."""
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Disable debug mode on Railway
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            self.debug = False

        logger.info(f"Database: {'PostgreSQL' if 'postgresql' in self.database_url else 'SQLite'}")
        return self


settings = Settings()
