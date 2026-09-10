"""Bounded retries for complete, rolled-back database operations."""
import sqlite3
import time
from functools import wraps
from sqlalchemy.exc import OperationalError


def is_database_locked(exc: Exception) -> bool:
    return isinstance(exc, OperationalError) and isinstance(exc.orig, sqlite3.OperationalError) and (
        getattr(exc.orig, "sqlite_errorcode", 0) & 0xFF in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
        or "database is locked" in str(exc.orig)
    )


def retry_database_write(func):
    """Retry a DB-only method from the beginning; never retry just commit()."""
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        for attempt in range(3):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                self.db.rollback()
                if not is_database_locked(exc) or attempt == 2:
                    raise
                time.sleep(0.1 * (2 ** attempt))
    return wrapped


async def run_database_write(operation, *args, **kwargs):
    """Keep the session alive until its worker finishes, even on cancellation."""
    import asyncio
    task = asyncio.create_task(asyncio.to_thread(operation, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # The caller owns the session and may close it in finally. Cancelling an
        # await cannot stop a worker thread, so finish before releasing ownership.
        try:
            await task
        finally:
            raise
