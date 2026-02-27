from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

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

    # Constants for default values
    DEFAULT_BASE_URL = 'acestream://'
    DEFAULT_ACE_ENGINE_URL = 'http://localhost:6878'
    DEFAULT_RESCRAPE_INTERVAL = '24'
    DEFAULT_ADDPID = 'false'
    DEFAULT_EPG_REFRESH_INTERVAL = '6'

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
            self.EPG_REFRESH_INTERVAL: (self.DEFAULT_EPG_REFRESH_INTERVAL, "Hours between EPG refreshes")
        }

        success = True
        for key, (value, description) in default_settings.items():
            # Check if setting exists
            setting = self.db.query(Setting).filter(Setting.key == key).first()

            if not setting:
                if not self.set_setting(key, value, description):
                    success = False

        return success
