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
    TUNER_DEVICE_ID = 'tuner_device_id'
    TUNER_FRIENDLY_NAME = 'tuner_friendly_name'
    TUNER_COUNT = 'tuner_count'
    TUNER_MAX_CHANNELS = 'tuner_max_channels'
    TUNER_ONLY_ONLINE = 'tuner_only_online'

    # Constants for default values
    DEFAULT_BASE_URL = 'acestream://'
    # A container that runs no engine of its own points at an external one through ACE_ENGINE_URL
    # (legacy alias ACESTREAM_ENGINE_URL); the Settings page can still override it per database.
    DEFAULT_ACE_ENGINE_URL = os.environ.get('ACE_ENGINE_URL') or os.environ.get('ACESTREAM_ENGINE_URL') or 'http://localhost:6878'
    DEFAULT_RESCRAPE_INTERVAL = '24'
    DEFAULT_ADDPID = 'false'
    DEFAULT_EPG_REFRESH_INTERVAL = '6'
    DEFAULT_ACESTREAM_CHECK_TIMEOUT = '10'
    # The tuner keys have no setup_defaults entry: get_setting falls back to
    # these, and the device id is generated on first use by TunerService.
    DEFAULT_TUNER_DEVICE_ID = ''
    DEFAULT_TUNER_FRIENDLY_NAME = 'AceStream Scraper'
    DEFAULT_TUNER_COUNT = '4'
    DEFAULT_TUNER_MAX_CHANNELS = '450'
    DEFAULT_TUNER_ONLY_ONLINE = 'false'

    # Keys whose stored empty value means "not configured" rather than
    # "deliberately blank". Their DEFAULT_<KEY> comes from the environment, and
    # setup_defaults seeds the row on first boot -- before the operator may have
    # set the variable. Without this, that empty row would win for good and
    # PUBLIC_BASE_URL would be inert with nothing to explain why.
    # Precedence: a non-empty stored value > the environment > unset.
    ENV_BACKED_KEYS = frozenset({PUBLIC_BASE_URL})

    @property
    def DEFAULT_PUBLIC_BASE_URL(self) -> str:  # noqa: N802 - matches the DEFAULT_<KEY> lookup convention
        # Read at call time (not import time) so tests and runtime env changes apply.
        from app.config.settings import get_settings
        from app.services.public_url_service import InvalidPublicBaseUrl, normalize_public_base_url

        raw = get_settings().PUBLIC_BASE_URL or ''
        try:
            # Seed the same canonical origin the API stores; a typo'd env value is
            # dropped (and logged) instead of being persisted unvalidated.
            return normalize_public_base_url(raw)
        except InvalidPublicBaseUrl as exc:
            logger.warning("Ignoring invalid PUBLIC_BASE_URL=%r: %s", raw, exc)
            return ''

    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        try:
            setting = self.db.query(Setting).filter(Setting.key == key).first()
            if setting is not None:
                value = setting.value
                if (value or '').strip() or key not in self.ENV_BACKED_KEYS:
                    return value
                logger.info(f"Setting {key} is empty, using the environment default")
                return self._get_class_default(key, default)
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
