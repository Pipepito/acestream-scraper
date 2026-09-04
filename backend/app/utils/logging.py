import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from .path import log_dir

_TOKEN_RE = re.compile(r'([?&]token=)[^&\s"]*')


class RedactTokenFilter(logging.Filter):
    """Hide ?token= values in access-log lines (spec 4.4): native HLS players
    and copied links carry the API token in the query string."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                _TOKEN_RE.sub(r"\1[redacted]", arg) if isinstance(arg, str) else arg for arg in record.args
            )
        elif isinstance(record.msg, str):
            record.msg = _TOKEN_RE.sub(r"\1[redacted]", record.msg)
        return True


def setup_logging():
    """Configure application-wide logging for FastAPI."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(log_format))
    console.setLevel(logging.INFO)
    root_logger.addHandler(console)

    # File handler for important logs. Rotate: the unbounded FileHandler grew
    # to >150 MB in a dev checkout (every pytest run appends on import).
    log_path = log_dir() / 'acestream.log'
    max_bytes = int(os.environ.get('LOG_FILE_MAX_BYTES', str(10 * 1024 * 1024)))
    backup_count = int(os.environ.get('LOG_FILE_BACKUP_COUNT', '3'))
    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

    # If in debug mode, enable more verbose logging
    if os.environ.get('FASTAPI_DEBUG') == '1':
        root_logger.setLevel(logging.DEBUG)
        console.setLevel(logging.DEBUG)
        # Do NOT enable SQLAlchemy engine SQL logs in debug mode
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    access_logger = logging.getLogger('uvicorn.access')
    if not any(isinstance(f, RedactTokenFilter) for f in access_logger.filters):
        access_logger.addFilter(RedactTokenFilter())

    return root_logger
