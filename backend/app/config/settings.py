"""Canonical application settings."""

import json
import logging
from functools import lru_cache
from typing import List, Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LEGACY_ENV_NAMES = {
    "SCRAPER_DB_URL": "DATABASE_URL", "LEGACY_DB_URL": "LEGACY_DATABASE_URL",
    "ZERONET_BASE_URL": "ZERONET_URL", "CORS_ALLOW_ORIGINS": "CORS_ORIGINS",
    "FRONTEND_STATIC_DIR": "FRONTEND_BUILD_PATH", "ACESTREAM_ENGINE_URL": "ACE_ENGINE_URL",
}

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    configuration_warnings: list[dict[str, str]] = Field(default_factory=list, exclude=True)

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        def compatible_environment():
            data = {**dotenv_settings(), **env_settings()}
            raw = {**dotenv_settings.env_vars, **env_settings.env_vars}
            warnings = []
            for legacy, canonical in LEGACY_ENV_NAMES.items():
                data.pop(legacy, None)
                if raw.get(legacy):
                    selected = canonical if raw.get(canonical) else legacy
                    if selected == legacy:
                        data[canonical] = raw[legacy]
                    warnings.append({"legacy": legacy, "replacement": canonical, "selected": selected})
            # The retired toggle no longer disables compatibility.
            data.pop("ENABLE_LEGACY_ENV_ALIASES", None)
            data["configuration_warnings"] = warnings
            return data
        return init_settings, compatible_environment, file_secret_settings

    @model_validator(mode="after")
    def warn_legacy_names(self):
        for warning in self.configuration_warnings:
            logging.getLogger(__name__).warning(
                "Deprecated environment variable %s: update it to %s. Using %s; values are not logged.",
                warning["legacy"], warning["replacement"], warning["selected"],
            )
        return self

    APP_NAME: str = "Acestream Scraper"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./config/scraper.db"
    LEGACY_DATABASE_URL: str = "sqlite:///./config/acestream.db"
    # EPG programs that ended more than this many hours ago are dead weight:
    # the hourly `epg_program_cleanup` job deletes them and the v1 -> v2
    # migration skips them. Negative disables both (keep everything).
    EPG_PROGRAM_RETENTION_HOURS: float = 24.0
    # Channels hidden from the playlist (is_active=false) are only deleted once no
    # scrape has seen them for this many days and no TV channel links them.
    CHANNEL_CLEANUP_DAYS: int = 30
    ZERONET_URL: str = "http://127.0.0.1:43110"
    # HTTP gateway used to fetch ipfs:// and ipns:// sources. Defaults to the
    # embedded Kubo daemon's gateway (entrypoint.sh binds it on 8081 because
    # Acexy owns 8080 in-container); point it at any external gateway instead.
    IPFS_GATEWAY_URL: str = "http://127.0.0.1:8081"
    SCRAPER_TIMEOUT: int = 10
    SCRAPER_RETRIES: int = 3
    ZERONET_TIMEOUT: int = 20
    ZERONET_RETRIES: int = 5
    # Cold gateway fetches wait on DHT provider lookups; give them more room
    # than plain HTTP sources.
    IPFS_TIMEOUT: int = 30
    IPFS_RETRIES: int = 3
    # NoDecode: pydantic-settings would otherwise json-decode the env value before
    # the validator runs, rejecting the documented comma-separated form.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = ["http://localhost:3000"]
    FRONTEND_BUILD_PATH: str = "frontend_build"
    ACE_ENGINE_URL: str = ""
    # Explicit probe route; an unavailable checker must never fall back to playback.
    ACE_CHECK_ENGINE_URL: str = ""

    # --- Media integrations (spec 4.3–4.5) ---------------------------------
    # Externally reachable origin (scheme://host[:port]) advertised to tuners,
    # remote players and the SPA copy link. Empty = derive from the request.
    PUBLIC_BASE_URL: str = ""
    # Peers whose X-Forwarded-* headers the app trusts (IPs, CIDRs, "*", or
    # literal tokens such as "testclient"). uvicorn's own proxy-header handling
    # is disabled in favour of app/middleware/forwarded.py.
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    # Networks allowed to reach the token-free /tuner/* routes ("*" disables).
    TUNER_ALLOWED_NETWORKS: str = (
        "127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10"
    )
    # Web player (plan 2).
    PLAYER_HLS_DIR: str = "/tmp/acestream-player"
    PLAYER_MAX_SESSIONS: int = 3
    PLAYER_START_TIMEOUT_SECONDS: int = 45
    FFMPEG_BINARY_PATH: str = ""
    # Media servers (plan 4): minimum minutes between automatic guide refreshes; 0 disables the debounce.
    MEDIA_SERVER_MIN_REFRESH_MINUTES: int = 30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
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
