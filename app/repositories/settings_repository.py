from app.models import Setting
from app.extensions import db

class SettingsRepository:
    """Repository for application settings."""
    
    # Constants for common settings (for backwards compatibility)
    ACE_ENGINE_URL = 'ace_engine_url'
    DEFAULT_ACE_ENGINE_URL = 'http://localhost:6878'
    BASE_URL = 'base_url'
    DEFAULT_BASE_URL = 'acestream://'
    RESCRAPE_INTERVAL = 'rescrape_interval'
    DEFAULT_RESCRAPE_INTERVAL = '24'
    SETUP_COMPLETED = 'setup_completed'
    
    def get_setting(self, key, default=None):
        """Get a setting value by key, with database fallback."""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default
        
    def set_setting(self, key, value):
        """Set a setting value by key."""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()
        
    # Alias methods for backwards compatibility
    def get(self, key, default=None):
        """Alias for get_setting."""
        return self.get_setting(key, default)
        
    def set(self, key, value):
        """Alias for set_setting."""
        return self.set_setting(key, value)
        
    def get_all_settings(self):
        """Get all settings as a dictionary."""
        return {setting.key: setting.value for setting in Setting.query.all()}
        
    def is_setup_completed(self):
        """Check if setup has been completed."""
        return self.get_setting(self.SETUP_COMPLETED) == 'True'
        
    def mark_setup_completed(self):
        """Mark setup as completed."""
        self.set_setting(self.SETUP_COMPLETED, 'True')
        
    def setup_defaults(self):
        """Set up default settings."""
        default_settings = {
            self.BASE_URL: self.DEFAULT_BASE_URL,
            self.ACE_ENGINE_URL: self.DEFAULT_ACE_ENGINE_URL,
            self.RESCRAPE_INTERVAL: self.DEFAULT_RESCRAPE_INTERVAL
        }
        
        for key, value in default_settings.items():
            if not self.get_setting(key):
                self.set_setting(key, value)
                
    def import_from_json_config(self, config_data):
        """Import settings from a JSON configuration dictionary."""
        for key, value in config_data.items():
            self.set_setting(key, value)
        self.mark_setup_completed()