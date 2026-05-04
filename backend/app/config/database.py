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
