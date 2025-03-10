from typing import Any, Optional, Dict
from datetime import datetime, timezone
from ..models import Setting
from .base import BaseRepository

class SettingsRepository(BaseRepository):
    """Repository for accessing and managing settings."""
    
    # Define constants for setting keys
    BASE_URL = 'base_url'
    DEFAULT_BASE_URL = 'http://localhost:6878/ace/getstream?id='
    
    ACE_ENGINE_URL = 'ace_engine_url'
    DEFAULT_ACE_ENGINE_URL = 'http://localhost:6878'
    
    RESCRAPE_INTERVAL = 'rescrape_interval'
    DEFAULT_RESCRAPE_INTERVAL = 24  # hours
    
    SETUP_COMPLETED = 'setup_completed'
    SETUP_TIMESTAMP = 'setup_timestamp'
    
    def __init__(self):
        super().__init__(Setting)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        setting = self.model.query.get(key)
        return setting.value if setting else default
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        setting = self.model.query.get(key) or self.model(key=key)
        setting.value = str(value)
        self._db.session.merge(setting)
        self._db.session.commit()
    
    def delete(self, key: str) -> bool:
        """Delete a setting by key."""
        setting = self.get_by_id(key)
        if setting is not None:
            super().delete(setting)
            self.commit()
            return True
        return False
    
    def get_all(self) -> Dict[str, str]:
        """Get all settings as a dictionary."""
        settings = super().get_all()
        return {setting.key: setting.value for setting in settings}
    
    def setup_defaults(self) -> None:
        """Set up default values for settings if they don't exist."""
        if not self.get(self.BASE_URL):
            self.set(self.BASE_URL, self.DEFAULT_BASE_URL)
        if not self.get(self.ACE_ENGINE_URL):
            self.set(self.ACE_ENGINE_URL, self.DEFAULT_ACE_ENGINE_URL)
        if not self.get(self.RESCRAPE_INTERVAL):
            self.set(self.RESCRAPE_INTERVAL, self.DEFAULT_RESCRAPE_INTERVAL)
    
    def is_setup_completed(self) -> bool:
        """Check if initial setup has been completed."""
        return self.get(self.SETUP_COMPLETED) == 'True'
    
    def mark_setup_completed(self) -> None:
        """Mark initial setup as completed."""
        self.set(self.SETUP_COMPLETED, 'True')
        self.set(self.SETUP_TIMESTAMP, datetime.now(timezone.utc).isoformat())
    
    def import_from_json_config(self, config: dict) -> None:
        """Import settings from JSON configuration."""
        if 'base_url' in config:
            self.set(self.BASE_URL, config['base_url'])
            
        if 'ace_engine_url' in config:
            self.set(self.ACE_ENGINE_URL, config['ace_engine_url'])
            
        if 'rescrape_interval' in config:
            self.set(self.RESCRAPE_INTERVAL, config['rescrape_interval'])
        
        # Mark setup as completed
        self.mark_setup_completed()