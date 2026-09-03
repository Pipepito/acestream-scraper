from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import os

from app.models.models import Setting

logger = logging.getLogger(__name__)

class SettingsRepository:
    """Repository for application settings"""

    # Constants for settings keys
    BASE_URL = 'base_url'
    ACE_ENGINE_URL = 'ace_engine_url'
    RESCRAPE_INTERVAL = 'rescrape_interval'
    ADDPID = 'addpid'
    EPG_REFRESH_INTERVAL = 'epg_refresh_interval'
    ACESTREAM_CHECK_TIMEOUT = 'acestream_check_timeout'
    PUBLIC_BASE_URL = 'public_base_url'

    # Constants for default values
    DEFAULT_BASE_URL = 'acestream://'
    # A container that runs no engine of its own points at an external one through ACE_ENGINE_URL
    # (legacy alias ACESTREAM_ENGINE_URL); the Settings page can still override it per database.
    DEFAULT_ACE_ENGINE_URL = os.environ.get('ACE_ENGINE_URL') or os.environ.get('ACESTREAM_ENGINE_URL') or 'http://localhost:6878'
    DEFAULT_RESCRAPE_INTERVAL = '24'
    DEFAULT_ADDPID = 'false'
    DEFAULT_EPG_REFRESH_INTERVAL = '6'
    DEFAULT_ACESTREAM_CHECK_TIMEOUT = '10'

    @property
    def DEFAULT_PUBLIC_BASE_URL(self) -> str:  # noqa: N802 - matches the DEFAULT_<KEY> lookup convention
        # Read at call time (not import time) so tests and runtime env changes apply.
        from app.config.settings import get_settings
        return get_settings().PUBLIC_BASE_URL or ''

    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        try:
            setting = self.db.query(Setting).filter(Setting.key == key).first()
            if setting:
                return setting.value
            logger.info(f"Setting {key} not found, using default")
            # Use class default if available
            return self._get_class_default(key, default)
        except Exception as e:
            return self._get_class_default(key, default)

    def _get_class_default(self, key: str, custom_default: Any = None) -> Any:
        """Get default value from class constants or custom default"""
        default_attr = f'DEFAULT_{key.upper()}'
        if hasattr(self, default_attr):
            return getattr(self, default_attr)
        return custom_default

    def set_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set or update a setting value"""
        try:
            setting = self.db.query(Setting).filter(Setting.key == key).first()

            if setting:
                logger.info(f"Updating setting {key} to {value}")
                setting.value = str(value)
                if description:
                    setting.description = description
            else:
                logger.info(f"Creating setting {key} = {value}")
                setting = Setting(
                    key=key,
                    value=str(value),
                    description=description
                )
                self.db.add(setting)

            self.db.commit()
            self.db.flush()
            self.db.expire_all()
            logger.info(f"Committed setting {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            self.db.rollback()
            return False

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        try:
            settings = self.db.query(Setting).all()
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            return {}

    def setup_defaults(self) -> bool:
        """Set up default settings if they don't exist"""
        default_settings = {
            self.BASE_URL: (self.DEFAULT_BASE_URL, "Base URL for Acestream links"),
            self.ACE_ENGINE_URL: (self.DEFAULT_ACE_ENGINE_URL, "Acestream Engine URL"),
            self.RESCRAPE_INTERVAL: (self.DEFAULT_RESCRAPE_INTERVAL, "Hours between automatic rescrapes"),
            self.ADDPID: (self.DEFAULT_ADDPID, "Add PID to Acestream links"),
            self.EPG_REFRESH_INTERVAL: (self.DEFAULT_EPG_REFRESH_INTERVAL, "Hours between EPG refreshes"),
            self.ACESTREAM_CHECK_TIMEOUT: (self.DEFAULT_ACESTREAM_CHECK_TIMEOUT, "Seconds before an engine status check times out"),
            self.PUBLIC_BASE_URL: (self.DEFAULT_PUBLIC_BASE_URL, "Externally reachable origin for tuners and players"),
        }

        success = True
        for key, (value, description) in default_settings.items():
            # Check if setting exists
            setting = self.db.query(Setting).filter(Setting.key == key).first()

            if not setting:
                if not self.set_setting(key, value, description):
                    success = False

        return success
