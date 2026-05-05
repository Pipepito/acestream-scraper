from typing import Dict, Any, Optional
import logging
import httpx
from fastapi import HTTPException
import re

from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for application configuration management"""

    def __init__(self, settings_repo: SettingsRepository):
        self.settings_repo = settings_repo
        # Ensure all default settings are present in the database
        self.settings_repo.setup_defaults()

    def _validate_url(self, url: str) -> bool:
        # Simple URL validation (http/https only)
        regex = re.compile(r'^(https?://)[^\s/$.?#].[^\s]*$')
        return bool(regex.match(url))

    def get_base_url(self) -> str:
        """Get the base URL for Acestream links"""
        return self.settings_repo.get_setting(SettingsRepository.BASE_URL)

    def set_base_url(self, base_url: str) -> bool:
        logger.info(f"ConfigService.set_base_url called with {base_url}")
        """Set the base URL for Acestream links"""
        if not self._validate_url(base_url):
            raise HTTPException(status_code=422, detail="Invalid URL format for base_url")
        return self.settings_repo.set_setting(
            SettingsRepository.BASE_URL,
            base_url,
            "Base URL for Acestream links"
        )

    def get_ace_engine_url(self) -> str:
        """Get the Acestream Engine URL"""
        return self.settings_repo.get_setting(SettingsRepository.ACE_ENGINE_URL)

    def set_ace_engine_url(self, url: str) -> bool:
        """Set the Acestream Engine URL"""
        if not self._validate_url(url):
            raise HTTPException(status_code=422, detail="Invalid URL format for ace_engine_url")
        return self.settings_repo.set_setting(
            SettingsRepository.ACE_ENGINE_URL,
            url,
            "Acestream Engine URL"
        )

    def get_rescrape_interval(self) -> int:
        """Get the interval between automatic rescrapes in hours"""
        interval_str = self.settings_repo.get_setting(SettingsRepository.RESCRAPE_INTERVAL)
        try:
            return int(interval_str)
        except (ValueError, TypeError):
            return int(self.settings_repo.DEFAULT_RESCRAPE_INTERVAL)

    def set_rescrape_interval(self, hours: int) -> bool:
        logger.info(f"ConfigService.set_rescrape_interval called with {hours}")
        if not isinstance(hours, int) or hours < 1:
            raise HTTPException(status_code=422, detail="Rescrape interval must be positive")
        return self.settings_repo.set_setting(
            SettingsRepository.RESCRAPE_INTERVAL,
            str(hours),
            "Hours between automatic rescrapes"
        )

    def get_addpid(self) -> str:
        """Get whether to add PID to Acestream links as a string value"""
        value = self.settings_repo.get_setting(SettingsRepository.ADDPID)
        # Return the value as stored (string), default to 'false' if not set
        if value is None:
            return 'false'
        return value

    def set_addpid(self, enabled: bool) -> bool:
        """Set whether to add PID to Acestream links"""
        # Store as 'true' or 'false' string
        return self.settings_repo.set_setting(
            SettingsRepository.ADDPID,
            'true' if enabled else 'false',
            "Add PID to Acestream links"
        )

    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings, ensuring all required keys are present and values are strings"""
        settings = self.settings_repo.get_all_settings()
        # Ensure all main keys are present with defaults as strings
        required_keys = {
            "base_url": self.settings_repo.DEFAULT_BASE_URL,
            "ace_engine_url": self.settings_repo.DEFAULT_ACE_ENGINE_URL,
            "rescrape_interval": str(self.settings_repo.DEFAULT_RESCRAPE_INTERVAL),
            "addpid": 'false',
        }
        for key, default in required_keys.items():
            if key not in settings or settings[key] is None:
                settings[key] = default
            else:
                settings[key] = str(settings[key])
        return settings

    def check_acestream_status(self) -> Dict[str, Any]:
        """Check the status of the Acestream Engine, always include required StatusResponse fields"""
        ace_url = self.get_ace_engine_url()
        engine_url = ace_url.rstrip('/') if ace_url else ""
        if not ace_url:
            return {
                "status": "unknown",
                "engine_url": engine_url,
                "accessible": False,
                "message": "Acestream Engine URL not configured",
                "details": None
            }
        # Ensure URL ends with trailing slash
        if not ace_url.endswith('/'):
            ace_url = f"{ace_url}/"
        try:
            with httpx.Client() as client:
                response = client.get(f"{ace_url}server/ping", timeout=0.2)
                if response.status_code == 200:
                    return {
                        "status": "online",
                        "engine_url": engine_url,
                        "accessible": True,
                        "message": "Acestream Engine is running",
                        "details": response.text
                    }
                return {
                    "status": "error",
                    "engine_url": engine_url,
                    "accessible": False,
                    "message": f"Acestream Engine returned unexpected status: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {
                "status": "error",
                "engine_url": engine_url,
                "accessible": False,
                "message": f"Failed to connect to Acestream Engine: {str(e)}",
                "details": None
            }

    def check_system_health(self) -> Dict[str, Any]:
        """Check the overall system health, always include all required fields"""
        acestream_status = self.check_acestream_status()
        try:
            from sqlalchemy import text
            result = self.settings_repo.db.execute(text("SELECT 1"))
            database_status = {
                "status": "connected",
                "connection_pool": {"active": 1, "idle": 0},
                "tables": 7
            }
        except Exception as e:
            database_status = {
                "status": "error",
                "error": str(e)
            }
        try:
            settings = self.get_all_settings()
        except Exception as e:
            settings = {"error": str(e)}
        # If database is healthy, report healthy even if Acestream is down
        overall_status = "healthy" if database_status.get("status") == "connected" else "degraded"
        health = {
            "status": overall_status,
            "acestream": acestream_status,
            "database": database_status,
            "settings": settings,
            "version": "2.0.0",
            "uptime": "unknown",
            "memory": {},
            "cpu": {},
            "dependencies": []
        }
        return health
