"""Application settings and cutover env compatibility helpers."""

import os
from functools import lru_cache
from typing import Dict, List, MutableMapping

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LEGACY_ENV_ALIAS_WINDOW = "v2-cutover-r1"
LEGACY_ENV_ALIAS_MAP: Dict[str, str] = {
    "SCRAPER_DB_URL": "DATABASE_URL",
    "LEGACY_DB_URL": "LEGACY_DATABASE_URL",
    "ZERONET_BASE_URL": "ZERONET_URL",
    "CORS_ALLOW_ORIGINS": "CORS_ORIGINS",
    "FRONTEND_STATIC_DIR": "FRONTEND_BUILD_PATH",
    "ACESTREAM_ENGINE_URL": "ACE_ENGINE_URL",
}


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def apply_legacy_env_aliases(
    environ: MutableMapping[str, str] | None = None,
    alias_map: Dict[str, str] | None = None,
    compat_enabled: bool | None = None,
) -> List[Dict[str, str]]:
    """Apply one-release legacy env aliases to canonical env names."""
    target_env = os.environ if environ is None else environ
    mappings = LEGACY_ENV_ALIAS_MAP if alias_map is None else alias_map
    if compat_enabled is None:
        compat_enabled = _is_truthy(target_env.get("ENABLE_LEGACY_ENV_ALIASES", "true"))

    if not compat_enabled:
        return []

    events: List[Dict[str, str]] = []
    for legacy_key, new_key in mappings.items():
        legacy_value = target_env.get(legacy_key)
        if legacy_value is None:
            continue

        new_value = target_env.get(new_key)
        if new_value is None:
            target_env[new_key] = legacy_value
            events.append({
                "kind": "alias_applied",
                "legacy_key": legacy_key,
                "new_key": new_key,
                "window": LEGACY_ENV_ALIAS_WINDOW,
                "selected": "legacy",
            })
            continue

        if new_value != legacy_value:
            events.append({
                "kind": "conflict",
                "legacy_key": legacy_key,
                "new_key": new_key,
                "window": LEGACY_ENV_ALIAS_WINDOW,
                "selected": "new",
            })

    return events


_ENV_COMPAT_EVENTS = apply_legacy_env_aliases()


def get_env_compat_events() -> List[Dict[str, str]]:
    """Get env compatibility events discovered at module load time."""
    return list(_ENV_COMPAT_EVENTS)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "Acestream Scraper"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./config/scraper.db"
    LEGACY_DATABASE_URL: str = "sqlite:///./config/acestream.db"
    # EPG programs that ended more than this many hours ago are dead weight:
    # the hourly `epg_program_cleanup` job deletes them and the v1 -> v2
    # migration skips them. Negative disables both (keep everything).
    EPG_PROGRAM_RETENTION_HOURS: float = 24.0
    ZERONET_URL: str = "http://127.0.0.1:43110"
    SCRAPER_TIMEOUT: int = 10
    SCRAPER_RETRIES: int = 3
    ZERONET_TIMEOUT: int = 20
    ZERONET_RETRIES: int = 5
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    FRONTEND_BUILD_PATH: str = "frontend_build"
    ACE_ENGINE_URL: str = "http://localhost:6878"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return value
            if stripped == "":
                return []
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @property
    def ace_engine_url(self) -> str:
        # Compatibility accessor during the cutover window.
        return self.ACE_ENGINE_URL


@lru_cache()
def get_settings():
    """Get application settings."""
    return Settings()


settings = get_settings()
