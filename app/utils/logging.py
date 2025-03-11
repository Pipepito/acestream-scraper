import logging
import sys
import os
from pathlib import Path
from .path import log_dir

def setup_logging():
    """Configure application-wide logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(log_format))
    console.setLevel(logging.INFO)
    root_logger.addHandler(console)
    
    # File handler for important logs
    log_path = log_dir() / 'acestream.log'
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # If in debug mode, enable more verbose logging
    if os.environ.get('FLASK_DEBUG') == '1':
        root_logger.setLevel(logging.DEBUG)
        console.setLevel(logging.DEBUG)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    return root_logger
