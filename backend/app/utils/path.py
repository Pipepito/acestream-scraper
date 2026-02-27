import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def project_root() -> Path:
    """Return the project root directory as a Path object."""
    return Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def config_dir() -> Path:
    """Return the configuration directory path."""
    if os.environ.get('DOCKER_ENVIRONMENT'):
        path = Path('/config')
    else:
        path = project_root() / 'config'
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Using config directory: {path}")
    return path

def log_dir() -> Path:
    """Return the log directory path."""
    if os.environ.get('DOCKER_ENVIRONMENT'):
        path = Path('/config/logs')
    else:
        path = project_root() / 'logs'
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_database_path() -> Path:
    """Return the database file path."""
    return config_dir() / 'acestream.db'
