"""Bounded, curated diagnostics; never expose exception text or database content."""
import secrets
import threading
from collections import deque
from datetime import datetime, timezone

from app.schemas.startup import StartupEvent, StartupStatus, MigrationProgress


class StartupService:
    def __init__(self):
        self.lock = threading.RLock()
        self.active = False
        self.reset()

    def reset(self):
        with self.lock:
            self.status = 'starting'
            self.phase = 'Preparing startup'
            self.events = deque(maxlen=300)
            self.migration = None
            self.recovery_available = False
            self.guidance = None
            self.recovery_token = secrets.token_urlsafe(32)

    def record(self, message, level='info'):
        with self.lock:
            self.phase = message
            self.events.append(StartupEvent(time=datetime.now(timezone.utc).isoformat(), message=message, level=level))

    def fail(self, exc, database=False):
        import sqlite3
        import errno
        from app.repositories.startup_recovery import NoRecoverableDataError, InterruptedRecoveryError
        from sqlalchemy.exc import DBAPIError
        cause = exc.orig if isinstance(exc, DBAPIError) else exc
        guidance = 'Download diagnostics and try again. If this keeps happening, share the report with support.'
        if isinstance(cause, NoRecoverableDataError):
            guidance = 'No readable data could be recovered. Your original files have been kept. Download diagnostics for help, or choose Start fresh to set up the app again.'
        elif isinstance(cause, InterruptedRecoveryError):
            guidance = 'A previous recovery was interrupted. Choose Recover readable data to rebuild from its preserved backup, or Start fresh to set up the app again.'
        elif isinstance(cause, BlockingIOError):
            guidance = 'Another app instance is using this data folder. Stop that instance, then try startup again.'
        elif isinstance(cause, PermissionError):
            guidance = 'The app cannot write to its data folder. Check the folder permissions in your Docker or NAS settings, then try again.'
        elif isinstance(cause, OSError) and cause.errno == errno.ENOSPC:
            guidance = 'The data drive is full. Free some space, then try again. Recovery also needs space for a backup.'
        elif isinstance(cause, sqlite3.DatabaseError) and getattr(cause, 'sqlite_errorcode', None) == sqlite3.SQLITE_FULL:
            guidance = 'The data drive is full. Free some space, then try again. Recovery also needs space for a backup.'
        elif isinstance(cause, sqlite3.DatabaseError):
            guidance = 'The database could not be opened or updated. Close other apps using this database and try again. You can also rebuild it from readable data or start fresh.'
        with self.lock:
            self.status = 'failed'
            self.guidance = guidance
            self.recovery_available = database
            self.record('Startup stopped. ' + type(cause).__name__, 'error')

    def progress(self, snapshot):
        with self.lock:
            self.migration = MigrationProgress.model_validate(snapshot)

    def snapshot(self):
        with self.lock:
            return StartupStatus(status=self.status, phase=self.phase, events=list(self.events),
                migration=self.migration, recovery_available=self.recovery_available,
                recovery_token=self.recovery_token, guidance=self.guidance)

    def diagnostics(self):
        return self.snapshot().model_dump_json(indent=2, exclude={'recovery_token'})


startup_service = StartupService()
