"""Shared API dependency providers for service wiring."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.config_service import ConfigService
from app.services.scraper_service import ScraperService
from app.services.stats_service import StatsService
from app.services.url_service import URLService


def get_url_service(db: Session = Depends(get_db)) -> URLService:
    return URLService(db)


def get_scraper_service(db: Session = Depends(get_db)) -> ScraperService:
    return ScraperService(db)


def get_config_service(db: Session = Depends(get_db)) -> ConfigService:
    settings_repo = SettingsRepository(db)
    return ConfigService(settings_repo)


def get_stats_service(db: Session = Depends(get_db)) -> StatsService:
    return StatsService(db)
