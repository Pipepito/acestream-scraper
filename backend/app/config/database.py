"""
Database initialization and utilities.

The engine and session factory are built lazily so tests can swap the bound
``DATABASE_URL`` without reloading the ``app.config.database`` module. The
module-level ``Base`` is constructed once and reused for every binding so
SQLAlchemy's mapper registry stays consistent across the test suite.
"""
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings


# Single canonical declarative base. Never recreated — recreating ``Base``
# splits SQLAlchemy's mapper registry, which is the root cause of the
# "expression 'AcestreamChannel' failed to locate a name" crash that hit
# the test suite under the previous module-reload conftest design.
Base = declarative_base()

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def _build_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


def get_engine() -> Engine:
    """Return the cached engine, building it on first access."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """Return the cached session factory, building it on first access."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _session_factory


def reset_engine() -> None:
    """Dispose the current engine and clear the cached session factory.

    Used by the test harness after overriding ``DATABASE_URL`` so the next
    call to :func:`get_engine` / :func:`SessionLocal` rebuilds against the
    new settings without reloading any modules.
    """
    global _engine, _session_factory
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _session_factory = None


def SessionLocal():  # noqa: N802 — backward-compat callable shim
    """Return a new ``Session`` bound to the current engine.

    Callable-compatible with the previous ``sessionmaker`` instance pattern
    so existing call sites (``db = SessionLocal()``) continue to work after
    :func:`reset_engine` has rebound the underlying factory.
    """
    return get_session_factory()()


def get_db():
    """FastAPI dependency that yields a ``Session`` bound to the current engine."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def __getattr__(name):
    """Lazy access to ``engine`` so ``from app.config.database import engine``
    resolves to whatever the current binding is at first import. Modules that
    capture ``engine`` at import time will hold a stale reference after
    :func:`reset_engine`; production callers should use :func:`get_engine`
    or the ``SessionLocal`` shim instead.
    """
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Schema provisioning (Alembic)
# ---------------------------------------------------------------------------

_APP_TABLE_MARKERS = ("settings", "acestream_channels", "scraped_urls")


def _alembic_config():
    from alembic.config import Config
    from pathlib import Path

    # backend/app/config/database.py -> backend/
    backend_dir = Path(__file__).resolve().parents[2]
    migrations_dir = backend_dir / "migrations"
    config = Config(str(migrations_dir / "alembic.ini"))
    # Absolute script_location so Alembic finds env.py regardless of the CWD
    # (uvicorn runs from /app in Docker, tests from the repo root).
    config.set_main_option("script_location", str(migrations_dir))
    return config


def _sqlite_path_from_url(database_url: str) -> Optional[str]:
    if not database_url.startswith("sqlite:///"):
        return None
    path = database_url[len("sqlite:///"):]
    return path or None


def schema_stamp_state(database_url: Optional[str] = None) -> str:
    """Classify the database at ``database_url`` (default: current settings).

    Returns ``"missing"`` (file absent or no tables at all), ``"stamped"``
    (has a populated ``alembic_version``), or ``"unstamped"`` (application
    tables exist but Alembic has no record of them — the state a pre-fix
    v1->v2 migration left behind via ``Base.metadata.create_all``).
    """
    import os
    import sqlite3

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return "missing"
    conn = sqlite3.connect(path)
    try:
        names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "alembic_version" in names:
            if conn.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0] > 0:
                return "stamped"
        if any(marker in names for marker in _APP_TABLE_MARKERS):
            return "unstamped"
        return "missing"
    finally:
        conn.close()


def upgrade_schema_to_head() -> None:
    """Run ``alembic upgrade head`` in-process against the current settings."""
    from alembic import command

    command.upgrade(_alembic_config(), "head")


def ensure_schema_stamped(database_url: Optional[str] = None) -> bool:
    """Stamp an ``unstamped`` database with the Alembic head; return True if stamped.

    The schema created by ``Base.metadata.create_all`` matches the Alembic
    head (``tests/test_schema_parity.py`` guards this), so recording the head
    revision is the correct repair — it lets future revisions apply instead of
    failing on ``CREATE TABLE`` for tables that already exist.
    """
    if schema_stamp_state(database_url) != "unstamped":
        return False
    from alembic import command

    command.stamp(_alembic_config(), "head")
    return True


def backfill_scraped_url_flags(database_url: Optional[str] = None) -> int:
    """Set ``scraped_urls.scrape_bare_ids`` to false where it is NULL; return rows changed.

    The pre-2026-08-29 v1 migrator provisioned v2 with ``create_all`` (no server
    default) and copied URLs with raw SQL, so every migrated row carries NULL —
    which ``URLResponse`` rejects, turning the URL list into a 500. Those
    databases are already stamped at the Alembic head, so no revision would
    reach them; startup repairs the rows directly.
    """
    import os
    import sqlite3

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return 0
    conn = sqlite3.connect(path)
    try:
        has_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='scraped_urls'"
        ).fetchone()
        if not has_table:
            return 0
        columns = {row[1] for row in conn.execute("PRAGMA table_info(scraped_urls)")}
        if "scrape_bare_ids" not in columns:
            return 0
        cursor = conn.execute(
            "UPDATE scraped_urls SET scrape_bare_ids = 0 WHERE scrape_bare_ids IS NULL"
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def provision_schema(database_url: Optional[str] = None) -> str:
    """Bring the database to the Alembic head, stamping first when needed.

    Returns the pre-provisioning state (``missing``/``unstamped``/``stamped``).
    """
    state = schema_stamp_state(database_url)
    if state == "unstamped":
        ensure_schema_stamped(database_url)
    upgrade_schema_to_head()
    return state


def current_revision(database_url: Optional[str] = None) -> Optional[str]:
    """The revision recorded in ``alembic_version`` (None when unstamped/missing)."""
    import os
    import sqlite3

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return None
    conn = sqlite3.connect(path)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "alembic_version" not in names:
            return None
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def head_revision() -> str:
    """The Alembic head of the bundled migrations."""
    from alembic.script import ScriptDirectory

    return ScriptDirectory.from_config(_alembic_config()).get_current_head()


def backup_sqlite(database_url: Optional[str] = None, label: str = "pre-upgrade") -> Optional[str]:
    """Copy the SQLite file to ``<db dir>/backups/<stamp>-<label>/<name>`` via the
    online backup API (safe while the file is open). Returns the copy's path, or
    None for non-SQLite URLs."""
    import os
    import sqlite3
    from datetime import datetime, timezone

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "backups", f"{stamp}-{label}")
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(path))
    source = sqlite3.connect(path)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    return target
