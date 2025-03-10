import os
import json
import logging
from pathlib import Path
from app.repositories import SettingsRepository


class Config:
    """Configuration management class."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        # Setup console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Determine config path
        if os.environ.get('DOCKER_ENVIRONMENT'):
            self.config_path = Path('/app/config')
        else:
            self.config_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / 'config'
        
        # Legacy config file path - kept for backwards compatibility
        self.config_file = self.config_path / 'config.json'
        
        # Database path
        self.database_path = self.config_path / 'acestream.db'
        
        # Initialize default values
        self._legacy_config = {}
        self._settings_repo = None
        self._base_url = 'acestream://'  # Default value
        self.ace_engine_url = 'http://localhost:6878'
        self.rescrape_interval = 24
        
        # Load legacy config if it exists (for non-test environments)
        if self.config_file.exists():
            self._legacy_config = self._load_legacy_config()
            # Apply legacy config values over defaults
            if self._legacy_config:
                self.base_url = self._legacy_config.get('base_url', self.base_url)
                self.ace_engine_url = self._legacy_config.get('ace_engine_url', self.ace_engine_url)
                self.rescrape_interval = self._legacy_config.get('rescrape_interval', self.rescrape_interval)
        
        self._initialized = True
    
    def set_settings_repository(self, settings_repo):
        """Set the settings repository after database initialization."""
        self._settings_repo = settings_repo
        
        # Import from legacy config if this is the first run and settings are empty
        if self._legacy_config and not settings_repo.is_setup_completed():
            self.logger.info("First run detected: Importing legacy config to database...")
            settings_repo.import_from_json_config(self._legacy_config)
            self.logger.info("Legacy config import completed")
    
    def _load_legacy_config(self):
        """Load configuration from legacy JSON file (read-only)."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading legacy config: {e}")
            return {}
    
    def is_initialized(self):
        """Check if configuration is fully initialized."""
        if self._settings_repo:
            return self._settings_repo.is_setup_completed()
        return False
    
    @property
    def base_url(self) -> str:
        """Get base URL for acestream links."""
        return getattr(self, '_base_url', 'acestream://')
    
    @base_url.setter
    def base_url(self, value: str):
        """Set base URL for acestream links."""
        self._base_url = value
    
    @property
    def database_uri(self) -> str:
        """Get SQLite database URI."""
        # Make sure database_path is set
        if not hasattr(self, 'database_path'):
            self.database_path = self.config_path / 'acestream.db'
        return f'sqlite:///{self.database_path}'
    
    @property
    def ace_engine_url(self) -> str:
        """Get Acestream Engine URL."""
        if self._settings_repo:
            return self._settings_repo.get(
                SettingsRepository.ACE_ENGINE_URL, 
                SettingsRepository.DEFAULT_ACE_ENGINE_URL
            )
        return self._legacy_config.get('ace_engine_url', SettingsRepository.DEFAULT_ACE_ENGINE_URL) if self._legacy_config else SettingsRepository.DEFAULT_ACE_ENGINE_URL
    
    @ace_engine_url.setter
    def ace_engine_url(self, value: str):
        """Set Acestream Engine URL."""
        if self._settings_repo:
            self._settings_repo.set(SettingsRepository.ACE_ENGINE_URL, value)
    
    @property
    def rescrape_interval(self) -> int:
        """Get URL rescrape interval in hours."""
        if self._settings_repo:
            try:
                interval = self._settings_repo.get(SettingsRepository.RESCRAPE_INTERVAL, self._rescrape_interval)
                return int(interval)
            except Exception:
                return self._rescrape_interval
        return self._rescrape_interval
    
    @rescrape_interval.setter
    def rescrape_interval(self, value: int):
        """Set URL rescrape interval in hours."""
        self._rescrape_interval = int(value)
        if self._settings_repo:
            try:
                self._settings_repo.set(SettingsRepository.RESCRAPE_INTERVAL, str(value))
            except Exception as e:
                self.logger.error(f"Error saving rescrape_interval: {e}")