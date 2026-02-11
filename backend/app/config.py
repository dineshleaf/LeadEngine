from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
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


settings = Settings()
