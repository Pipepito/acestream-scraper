"""Pre-upgrade backups (``app.config.database.backup_sqlite``).

The rollback documented in the release notes restores one of these copies, so a
file that is not a complete database must never be presented as one.
"""
import sqlite3

import pytest

from app.config.database import backup_sqlite


def _database(path) -> str:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.executemany("INSERT INTO t (v) VALUES (?)", [("a",), ("b",)])
        conn.commit()
    finally:
        conn.close()
    return f"sqlite:///{path.as_posix()}"


def test_backup_copies_the_database_and_reuses_the_copy(tmp_path):
    url = _database(tmp_path / "scraper.db")

    first = backup_sqlite(url, label="pre-upgrade-a-b")
    assert first is not None
    with sqlite3.connect(first) as conn:
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 2
    assert not list((tmp_path / "backups").glob("*/*.part"))

    # A second boot against the same pending upgrade reuses it instead of
    # writing another full copy of the database.
    assert backup_sqlite(url, label="pre-upgrade-a-b") == first


def test_an_unfinished_copy_is_never_reused_as_a_backup(tmp_path, monkeypatch):
    """The config volume filling mid-copy is exactly when the backup matters:
    what it leaves behind must not be handed to the next boot as a good copy."""
    url = _database(tmp_path / "scraper.db")
    real_connect = sqlite3.connect

    class OutOfSpace:
        """The source connection, with the copy itself failing part-way."""

        def __init__(self, conn):
            self._conn = conn

        def backup(self, *args, **kwargs):
            raise sqlite3.OperationalError("database or disk is full")

        def __getattr__(self, name):
            return getattr(self._conn, name)

    def failing_connect(target, *args, **kwargs):
        conn = real_connect(target, *args, **kwargs)
        return conn if str(target).endswith(".part") else OutOfSpace(conn)

    monkeypatch.setattr(sqlite3, "connect", failing_connect)
    with pytest.raises(sqlite3.OperationalError):
        backup_sqlite(url, label="pre-upgrade-a-b")
    monkeypatch.undo()

    assert list((tmp_path / "backups").glob("*/*")) == [], "a half-written copy must not survive the failure"

    # The next boot takes a real backup rather than reusing the wreckage.
    second = backup_sqlite(url, label="pre-upgrade-a-b")
    assert second is not None
    with sqlite3.connect(second) as conn:
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 2


def test_a_zero_byte_file_left_by_an_older_build_is_not_reused(tmp_path):
    url = _database(tmp_path / "scraper.db")
    stale_dir = tmp_path / "backups" / "20260101-000000-pre-upgrade-a-b"
    stale_dir.mkdir(parents=True)
    (stale_dir / "scraper.db").write_bytes(b"")

    taken = backup_sqlite(url, label="pre-upgrade-a-b")
    assert taken is not None and taken != str(stale_dir / "scraper.db")
    with sqlite3.connect(taken) as conn:
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 2
