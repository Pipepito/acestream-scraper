import os
import json
import logging
from pathlib import Path
from app.repositories import SettingsRepository
from flask import has_app_context, current_app

logger = logging.getLogger(__name__)
class Config:
    """Configuration management class."""
    
    # Add default values as class constants
    DEFAULT_BASE_URL = 'acestream://'
    DEFAULT_ACE_ENGINE_URL = 'http://localhost:6878'
    DEFAULT_RESCRAPE_INTERVAL = 24
    
    _instance = None
    config_path = None
    database_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self.logger = logging.getLogger(__name__)
        self.settings_repo = None
        self._needs_init = True
        
        # Set up paths first, which don't require app context
        if os.environ.get('DOCKER_ENVIRONMENT'):
            base_config_dir = Path('/config')
        else:
            project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            base_config_dir = project_root / 'config'
        
        base_config_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Using configuration directory: {base_config_dir}")
        
        if Config.config_path is None:
            try:
                Config.config_path = base_config_dir / 'config.json'
                self.logger.info(f"Config path set to {Config.config_path}")
            except Exception as e:
                self.logger.warning(f"Could not set config path: {e}")
                Config.config_path = Path("/tmp/non_existent_config.json")
        
        if Config.database_path is None:
            try:
                Config.database_path = base_config_dir / 'acestream.db'
                self.logger.info(f"Database path set to {Config.database_path}")
            except Exception as e:
                self.logger.warning(f"Could not set database path: {e}")
                Config.database_path = Path("/tmp/acestream.db")
        
        self._config = {}
        self._load_config()
        
        # Initialize settings repo but don't access database yet
        try:
            self.settings_repo = SettingsRepository()
        except Exception as e:
            self.logger.warning(f"Could not initialize settings repository: {e}")
        
        self._initialized = True

    def _ensure_app_context(self):
        """Ensure we're in an app context and initialize if needed."""
        if not has_app_context():
            return False
            
        # Only do this once
        if self._needs_init and self.settings_repo:
            self._needs_init = False
            self._ensure_required_settings()
            # Commit any cached settings
            if hasattr(self.settings_repo, 'commit_cache_to_db'):
                self.settings_repo.commit_cache_to_db()
            
        return True

    def _ensure_required_settings(self):
        """Ensure all required settings exist with default values."""
        # Skip setting defaults during testing to avoid unexpected method calls
        if not self.settings_repo or os.environ.get('TESTING'):
            return
            
        required_settings = {
            'base_url': self.DEFAULT_BASE_URL,
            'ace_engine_url': self.DEFAULT_ACE_ENGINE_URL,
            'rescrape_interval': self.DEFAULT_RESCRAPE_INTERVAL
        }
        
        for key, default_value in required_settings.items():
            try:
                if not self.settings_repo.get_setting(key):
                    self.logger.info(f"Setting default value for {key}: {default_value}")
                    self.settings_repo.set_setting(key, default_value)
            except Exception as e:
                self.logger.error(f"Error ensuring required setting {key}: {e}")

    def set_settings_repository(self, settings_repo):
        """Set the settings repository after database initialization (for testing)."""
        try:
            self.settings_repo = settings_repo
            self._needs_init = False
            
            if self._config and hasattr(settings_repo, 'is_setup_completed') and not settings_repo.is_setup_completed():
                self.logger.info("First run detected: Importing config to database...")
                if hasattr(settings_repo, 'import_from_json_config'):
                    settings_repo.import_from_json_config(self._config)
                else:
                    for key, value in self._config.items():
                        self.set(key, value)
                    if hasattr(settings_repo, 'mark_setup_completed'):
                        settings_repo.mark_setup_completed()
                self.logger.info("Config import completed")
        except Exception as e:
            self.logger.error(f"Error during repository setup: {e}")
    
    def _load_config(self):
        """Load configuration from file if it exists, fallback to database."""
        try:
            if Config.config_path and Config.config_path.exists():
                with open(Config.config_path, 'r') as f:
                    self._config = json.load(f)
                self.logger.info(f"Configuration loaded from {Config.config_path}")
            else:
                self._config = {}
                self.logger.warning("No config file found")
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            self._config = {}
    
    def get(self, key, default=None):
        """Get a configuration value with database fallback."""
        # Try to initialize if possible
        self._ensure_app_context()
        
        try:
            if self.settings_repo:
                value = self.settings_repo.get_setting(key)
                if value is not None:
                    return value
            
            # Check file-based config
            if key in self._config:
                return self._config[key]
                
            # Use class default if available
            default_attr = f'DEFAULT_{key.upper()}'
            if hasattr(self, default_attr):
                return getattr(self, default_attr)
                
            return default
        except Exception as e:
            self.logger.error(f"Error getting config value for {key}: {e}")
            return default
    
    def set(self, key, value):
        """Set a configuration value in the database."""
        # Try to initialize if possible
        self._ensure_app_context()
        
        try:
            if self.settings_repo:
                self.settings_repo.set_setting(key, value)
            self._config[key] = value
        except Exception as e:
            self.logger.error(f"Error setting config value for {key}: {e}")
            return value
    
    def save(self):
        """Save configuration to file for compatibility with older versions."""
        if not Config.config_path:
            self.logger.info("Config path is None, not saving to file")
            return
            
        if not Config.config_path.exists():
            try:
                Config.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(Config.config_path, 'w') as f:
                    json.dump({}, f)
            except Exception as e:
                self.logger.error(f"Could not create config file: {e}")
                return
                
        try:
            settings = {}
            if self.settings_repo and hasattr(self.settings_repo, 'get_all_settings'):
                settings = self.settings_repo.get_all_settings()
            else:
                self.logger.warning("Settings repository has no get_all_settings method")
            
            for key, value in settings.items():
                self._config[key] = value
                
            with open(Config.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
                
            self.logger.info(f"Configuration saved to {Config.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config to file: {str(e)}")
    
    def migrate_to_database(self):
        """Migrate settings from config.json to the database."""
        # Try to initialize if possible
        if not self._ensure_app_context():
            self.logger.warning("Cannot migrate to database without app context")
            return False
            
        if not Config.config_path or not Config.config_path.exists():
            self.logger.info("No config file to migrate")
            return False
            
        try:
            with open(Config.config_path, 'r') as f:
                file_config = json.load(f)
                
            for key, value in file_config.items():
                self.set(key, value)
                
            self.logger.info("Successfully migrated settings from config.json to database")
            return True
        except Exception as e:
            self.logger.error(f"Failed to migrate config to database: {str(e)}")
            return False
            
    @property
    def database_uri(self) -> str:
        """Get SQLite database URI."""
        if os.environ.get('TESTING'):
            return 'sqlite:///:memory:'
            
        try:
            if Config.database_path:
                Config.database_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Using database at: {Config.database_path.absolute()}")
                
            return f'sqlite:///{Config.database_path}'
        except Exception as e:
            self.logger.error(f"Error ensuring database directory exists: {e}")
            return 'sqlite:///:memory:'
    
    @property
    def base_url(self):
        """Get base URL for acestream links."""
        return self.get('base_url', 'acestream://')
        
    @base_url.setter
    def base_url(self, value):
        """Set base URL for acestream links."""
        self.set('base_url', value)
    
    @property
    def ace_engine_url(self):
        """Get Acestream Engine URL."""
        return self.get('ace_engine_url', 'http://localhost:6878')
    
    @ace_engine_url.setter
    def ace_engine_url(self, value):
        """Set Acestream Engine URL."""
        self.set('ace_engine_url', value)
        
    @property
    def rescrape_interval(self):
        """Get rescrape interval in hours."""
        interval = self.get('rescrape_interval', 24)
        return int(interval) if isinstance(interval, (int, str)) else 24
    
    @rescrape_interval.setter
    def rescrape_interval(self, value):
        """Set rescrape interval in hours."""
        self.set('rescrape_interval', str(value))
        
    def is_initialized(self):
        """Check if configuration is fully initialized."""
        # Try to initialize if possible
        self._ensure_app_context()
        
        try:
            if self.settings_repo:
                setup_completed = self.settings_repo.get_setting('setup_completed')
                if setup_completed and setup_completed.lower() == 'true':
                    # Only check for required settings
                    required_settings = [
                        'base_url',
                        'ace_engine_url',
                        'rescrape_interval'
                    ]
                    for setting in required_settings:
                        if not self.settings_repo.get_setting(setting):
                            return False
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking initialization: {e}")
            return False