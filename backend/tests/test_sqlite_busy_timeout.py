"""SQLite contention waits are bounded and do not block the health event loop."""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import OperationalError

from app.config import database
from app.config.settings import get_settings


@pytest.fixture
def sqlite_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'busy.db'}")
    get_settings.cache_clear()
    engine = database._build_engine()
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE sample (value INTEGER)")
            connection.exec_driver_sql("INSERT INTO sample VALUES (1)")
        yield engine
    finally:
        engine.dispose()
        get_settings.cache_clear()


def test_a_sqlite_connection_waits_for_the_lock(sqlite_engine):
    with sqlite_engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() == 30_000


@pytest.mark.parametrize("statement", [
    "SELECT value FROM sample",
    "UPDATE sample SET value = 2",
])
def test_contention_longer_than_old_timeout_recovers(sqlite_engine, statement):
    """Real independent connections survive a lock held beyond the old 5 s limit."""
    def contender():
        with sqlite_engine.begin() as connection:
            connection.exec_driver_sql(statement)

    with sqlite_engine.connect() as owner, ThreadPoolExecutor(max_workers=1) as pool:
        owner.exec_driver_sql("BEGIN EXCLUSIVE")
        future = pool.submit(contender)
        try:
            time.sleep(5.2)
            assert not future.done(), "The contender failed before the lock was released"
        finally:
            owner.rollback()
        future.result(timeout=5)


def test_expired_lock_wait_releases_connection_and_can_retry(sqlite_engine):
    with sqlite_engine.connect() as owner, sqlite_engine.connect() as contender:
        owner.exec_driver_sql("BEGIN EXCLUSIVE")
        # Accelerate only this connection's wait; the production 30 s default
        # is verified separately and the >5 s contention case uses that default.
        contender.exec_driver_sql("PRAGMA busy_timeout = 150")
        started = time.monotonic()
        try:
            with pytest.raises(OperationalError, match="database is locked"):
                contender.exec_driver_sql("UPDATE sample SET value = 3")
            assert time.monotonic() - started >= 0.1
            contender.rollback()
        finally:
            owner.rollback()
        contender.exec_driver_sql("UPDATE sample SET value = 3")
        contender.commit()
        assert contender.exec_driver_sql("SELECT value FROM sample").scalar() == 3


@pytest.mark.asyncio
async def test_health_lock_wait_leaves_event_loop_responsive(sqlite_engine):
    from app.api.endpoints.health import check_health

    def health_read():
        with sqlite_engine.connect() as connection:
            return {"value": connection.exec_driver_sql("SELECT value FROM sample").scalar()}

    with sqlite_engine.connect() as owner:
        owner.exec_driver_sql("BEGIN EXCLUSIVE")
        task = asyncio.create_task(check_health(SimpleNamespace(check_system_health=health_read)))
        try:
            await asyncio.sleep(0.1)
            assert not task.done()
        finally:
            owner.rollback()
        assert await asyncio.wait_for(task, timeout=5) == {"value": 1}
