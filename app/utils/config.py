import os
import json
import logging
from pathlib import Path

class Config:
    """Configuration management class."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    DEFAULT_BASE_URL = "acestream://"
    DEFAULT_ACE_ENGINE_URL = "http://127.0.0.1:6878"
    DEFAULT_RESCRAPE_INTERVAL = 24  # hours
    
    def __init__(self):
        if self._initialized:
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
        
        self.config_file = self.config_path / 'config.json'
        self._ensure_config_exists()
        self._load_config()
        
        # Add database path property
        self.database_path = self.config_path / 'acestream.db'
        
        self._initialized = True

    def _ensure_config_exists(self):
        """Ensure config directory and file exist with default values."""
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            
            if not self.config_file.exists():
                default_config = {
                    "urls": [],
                    "base_url": self.DEFAULT_BASE_URL,
                    "ace_engine_url": self.DEFAULT_ACE_ENGINE_URL,
                    "rescrape_interval": self.DEFAULT_RESCRAPE_INTERVAL
                }
                
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                self.logger.info(f"Created default configuration at {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error ensuring config exists: {e}")
            raise

    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                self._config = json.load(f)
                
            # Ensure base_url exists with default value
            if not self._config.get('base_url'):
                self._config['base_url'] = self.DEFAULT_BASE_URL
                self._save_config()
                
            # Ensure urls exists
            if 'urls' not in self._config:
                self._config['urls'] = []
                self._save_config()
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise

    def _save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise

    @property
    def urls(self) -> list:
        """Get list of URLs to scrape."""
        return self._config.get('urls', [])

    @property
    def base_url(self) -> str:
        """Get base URL for acestream links."""
        return self._config.get('base_url', self.DEFAULT_BASE_URL)

    @property
    def database_uri(self) -> str:
        """Get SQLite database URI."""
        return f'sqlite:///{self.database_path}'

    @property
    def ace_engine_url(self) -> str:
        """Get Acestream Engine URL."""
        return self._config.get('ace_engine_url', self.DEFAULT_ACE_ENGINE_URL)

    @property
    def rescrape_interval(self) -> int:
        """Get URL rescrape interval in hours."""
        return self._config.get('rescrape_interval', self.DEFAULT_RESCRAPE_INTERVAL)

    def add_url(self, url: str) -> bool:
        """
        Add a URL to the configuration.
        Note: This is only used for initial setup or CLI tools.
        Web interface changes should be stored in the database.
        """
        if url not in self.urls:
            self._config['urls'].append(url)
            self._save_config()
            self.logger.info(f"Added URL to config: {url}")
            return True
        return False