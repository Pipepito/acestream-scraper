import logging
import os
import requests
from typing import Dict, Any
from app.config.settings import settings

logger = logging.getLogger(__name__)

class AcestreamStatusService:
    """Service for checking Acestream Engine status."""
    def __init__(self, engine_url: str = None):
        self.config_engine_url = engine_url or getattr(settings, 'ACE_ENGINE_URL', None)
        self.is_internal_engine = self.is_enabled()
        # Determine the URL to use based on whether internal engine is enabled
        if self.is_internal_engine:
            host = os.environ.get('ACESTREAM_HTTP_HOST', 'localhost')
            if host == "ACEXY_HOST":
                host = os.environ.get('ACEXY_HOST', 'localhost')
            port = os.environ.get('ACESTREAM_HTTP_PORT', '6878')
            self.engine_url = f"http://{host}:{port}"
        else:
            self.engine_url = self.config_engine_url or "http://localhost:6878"
        if not self.engine_url.startswith('http'):
            self.engine_url = f"http://{self.engine_url}"
        self.engine_url = self.engine_url.rstrip('/')

    def is_enabled(self) -> bool:
        return os.environ.get('ENABLE_ACESTREAM_ENGINE', 'false').lower() == 'true'

    def check_status(self) -> Dict[str, Any]:
        try:
            status_url = f"{self.engine_url}/server/api?api_version=3&method=get_status"
            network_url = f"{self.engine_url}/server/api?api_version=3&method=get_network_connection_status"
            status_response = requests.get(status_url, timeout=10)
            network_response = requests.get(network_url, timeout=10)
            if status_response.status_code == 200 and network_response.status_code == 200:
                status_data = status_response.json()
                network_data = network_response.json()
                engine_version = status_data.get('result', {}).get('version', {}).get('version', 'Unknown')
                platform = status_data.get('result', {}).get('version', {}).get('platform', 'Unknown')
                playlist_loaded = status_data.get('result', {}).get('playlist_loaded', False)
                connected = network_data.get('result', {}).get('connected', False)
                message = f"Acestream Engine v{engine_version} is online"
                if not self.is_internal_engine:
                    message = f"External {message}"
                return {
                    "enabled": self.is_internal_engine,
                    "is_internal": self.is_internal_engine,
                    "engine_url": self.engine_url,
                    "available": True,
                    "message": message,
                    "version": engine_version,
                    "platform": platform,
                    "playlist_loaded": playlist_loaded,
                    "connected": connected
                }
            error_details = ""
            if status_response.status_code != 200:
                error_details = f", status API returned {status_response.status_code}"
            if network_response.status_code != 200:
                error_details += f", network API returned {network_response.status_code}"
            message = f"Acestream Engine is not responding properly{error_details}"
            if not self.is_internal_engine:
                message = f"External {message}"
            return {
                "enabled": self.is_internal_engine,
                "is_internal": self.is_internal_engine,
                "engine_url": self.engine_url,
                "available": False,
                "message": message,
                "version": None,
                "platform": None,
                "playlist_loaded": None,
                "connected": None
            }
        except Exception as e:
            logger.error(f"Error checking Acestream Engine status: {str(e)}")
            message = f"Could not connect to Acestream Engine: {str(e)}"
            if not self.is_internal_engine:
                message = f"External {message}"
            return {
                "enabled": self.is_internal_engine,
                "is_internal": self.is_internal_engine,
                "engine_url": self.engine_url,
                "available": False,
                "message": message,
                "version": None,
                "platform": None,
                "playlist_loaded": None,
                "connected": None
            }
