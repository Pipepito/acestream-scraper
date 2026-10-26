from typing import Dict, Any, Optional
import logging
from urllib.parse import urlsplit, urlunsplit
import httpx
from fastapi import HTTPException
from pydantic import AnyHttpUrl, TypeAdapter
import re

from app.repositories.settings_repository import SettingsRepository
from app.config.version import get_app_version
from app.schemas.config import PlaybackRouting
from app.services.public_url_service import InvalidPublicBaseUrl, normalize_public_base_url

# How a hidden secret reads in the API.
MASK = "•••"
_WEBHOOK_URL = TypeAdapter(AnyHttpUrl)

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

    def get_playback_routing(self) -> PlaybackRouting:
        return PlaybackRouting.model_validate_json(self.settings_repo.get_setting(SettingsRepository.PLAYBACK_ROUTING))

    def set_playback_routing(self, routing: PlaybackRouting) -> PlaybackRouting:
        if not self.settings_repo.set_setting(SettingsRepository.PLAYBACK_ROUTING, routing.model_dump_json(), "Playback routing"):
            raise HTTPException(status_code=500, detail="Failed to save playback routing")
        return routing

    def set_ace_engine_url(self, url: str) -> bool:
        """Set the Acestream Engine URL"""
        url = url.strip()
        if url and not self._validate_url(url):
            raise HTTPException(status_code=422, detail="Invalid URL format for ace_engine_url")
        return self.settings_repo.set_setting(
            SettingsRepository.ACE_ENGINE_URL,
            url,
            "Acestream Engine URL"
        )

    @staticmethod
    def normalize_public_base_url(value: str) -> str:
        """Accept http(s)://host[:port] only; strip a trailing slash; '' clears.

        Every rejection (a bad scheme, a missing host, a path/query/fragment/
        credentials, or a string urlsplit itself refuses such as "http://[::1")
        becomes a 422 rather than an uncaught ValueError.
        """
        try:
            return normalize_public_base_url(value)
        except InvalidPublicBaseUrl as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def get_public_base_url(self) -> str:
        """Get the externally reachable origin advertised to tuners and players"""
        return self.settings_repo.get_setting(SettingsRepository.PUBLIC_BASE_URL) or ""

    def set_public_base_url(self, value: str) -> bool:
        """Set (or, with an empty value, clear) the externally reachable origin"""
        normalized = self.normalize_public_base_url(value)
        return self.settings_repo.set_setting(
            SettingsRepository.PUBLIC_BASE_URL,
            normalized,
            "Externally reachable origin for tuners and players",
        )

    def get_notification_webhook_url(self) -> str:
        """Where task notifications are POSTed; empty means notifications are off (#41)"""
        return self.settings_repo.get_setting(SettingsRepository.NOTIFICATION_WEBHOOK_URL) or ""

    @staticmethod
    def _parse_webhook_url(url: str):
        """Validate syntax without resolving DNS or rewriting signed URLs."""
        if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url) or "\\" in url:
            raise ValueError("Invalid webhook URL")
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.fragment:
            raise ValueError("Invalid webhook URL")
        if parts.port is not None and not 1 <= parts.port <= 65535:
            raise ValueError("Invalid webhook port")
        # Also reject malformed authorities/IP literals accepted by urlsplit.
        # Keep the original bytes: normalization can change webhook signatures.
        _WEBHOOK_URL.validate_python(url)
        return parts

    @staticmethod
    def mask_webhook_url(url: str) -> str:
        """The webhook as the API shows it: scheme and host only, the rest
        hidden. Webhooks keep their secret in the query (Gotify's token) or in
        the path (a Home Assistant webhook id, a Telegram bot token), and
        secrets are never returned by the API. The host is enough to tell
        which one is set."""
        if not url:
            return ""
        try:
            parts = ConfigService._parse_webhook_url(url)
        except ValueError:
            # Older versions could persist malformed values before masking
            # failed. Keep settings readable so the user can replace/clear it.
            return MASK
        host = parts.hostname or ""
        if ":" in host:
            host = "[" + host + "]"
        if parts.port:
            host += ":%d" % parts.port
        hidden = parts.path not in ("", "/") or parts.query or parts.fragment or parts.username
        return "%s://%s%s" % (parts.scheme, host, "/" + MASK if hidden else "")

    def get_masked_notification_webhook_url(self) -> str:
        return self.mask_webhook_url(self.get_notification_webhook_url())

    def set_notification_webhook_url(self, value: str) -> bool:
        """Set (or, with an empty value, clear) the notification webhook.

        Saving back what the API showed -- the masked URL -- keeps the stored
        one: the secret never makes the round trip."""
        value = (value or "").strip()
        if value and value != MASK and value == self.get_masked_notification_webhook_url():
            return True
        if MASK in value:
            raise HTTPException(status_code=422, detail="Paste the whole webhook URL; the masked one cannot be saved")
        if value:
            try:
                self._parse_webhook_url(value)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Use an HTTP(S) webhook URL with a valid host and port, without spaces or a fragment",
                ) from None
        return self.settings_repo.set_setting(
            SettingsRepository.NOTIFICATION_WEBHOOK_URL,
            value,
            "Webhook that receives task notifications (empty = off)",
        )

    def get_rescrape_interval(self) -> int:
        """Get the interval between automatic rescrapes in hours"""
        interval_str = self.settings_repo.get_setting(SettingsRepository.RESCRAPE_INTERVAL)
        try:
            return int(interval_str)
        except (ValueError, TypeError):
            return int(self.settings_repo.DEFAULT_RESCRAPE_INTERVAL)

    def get_channel_status_interval(self) -> int:
        try:
            value = int(self.settings_repo.get_setting(SettingsRepository.CHANNEL_STATUS_INTERVAL))
            return value if 1 <= value <= 10080 else 60
        except (ValueError, TypeError):
            return 60

    def set_channel_status_interval(self, minutes: int) -> bool:
        if not 1 <= minutes <= 10080:
            raise HTTPException(status_code=422, detail="Stream check interval must be 1 to 10080 minutes")
        return self.settings_repo.set_setting(
            SettingsRepository.CHANNEL_STATUS_INTERVAL, str(minutes), "Minutes between stream online checks"
        )

    def get_epg_refresh_interval(self) -> int:
        """Hours between automatic EPG refreshes."""
        interval_str = self.settings_repo.get_setting(SettingsRepository.EPG_REFRESH_INTERVAL)
        try:
            return int(interval_str)
        except (ValueError, TypeError):
            return int(self.settings_repo.DEFAULT_EPG_REFRESH_INTERVAL)

    def set_epg_refresh_interval(self, hours: int) -> bool:
        if not isinstance(hours, int) or hours < 1:
            raise HTTPException(status_code=422, detail="EPG refresh interval must be positive")
        return self.settings_repo.set_setting(
            SettingsRepository.EPG_REFRESH_INTERVAL,
            str(hours),
            "Hours between EPG refreshes"
        )

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
        if settings.get(SettingsRepository.NOTIFICATION_WEBHOOK_URL):
            settings[SettingsRepository.NOTIFICATION_WEBHOOK_URL] = self.mask_webhook_url(
                str(settings[SettingsRepository.NOTIFICATION_WEBHOOK_URL]))
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
                # get_version is the lightest unauthenticated probe that both the
                # native Linux engine (3.2.x) and the Android engine used on ARM
                # answer; /server/ping does not exist on either (HTTP 500).
                response = client.get(f"{ace_url}webui/api/service?method=get_version", timeout=1.0)
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
            "version": get_app_version(),
            "uptime": "unknown",
            "memory": {},
            "cpu": {},
            "dependencies": []
        }
        return health
