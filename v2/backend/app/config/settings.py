"""
Application settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Acestream Scraper"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./acestream.db"
    ZERONET_URL: str = "http://127.0.0.1:43110"
    SCRAPER_TIMEOUT: int = 10
    SCRAPER_RETRIES: int = 3    ZERONET_TIMEOUT: int = 20
    ZERONET_RETRIES: int = 5
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    FRONTEND_BUILD_PATH: str = os.getenv("FRONTEND_BUILD_PATH", "frontend_build")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """Get application settings"""
    return Settings()


settings = get_settings()
