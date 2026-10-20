"""A SQLite connection waits for a lock instead of failing at once.

Python's default is 5 s. On a box (18-10) a guide refresh held the database
for longer, and two channel opens failed with «database is locked».
"""
from app.config import database


def test_a_sqlite_connection_waits_for_the_lock(tmp_path, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'busy.db'}")
    get_settings.cache_clear()
    try:
        engine = database._build_engine()
        with engine.connect() as connection:
            busy_ms = connection.exec_driver_sql("PRAGMA busy_timeout").scalar()
        engine.dispose()
    finally:
        get_settings.cache_clear()
    assert busy_ms == database.SQLITE_BUSY_SECONDS * 1000
