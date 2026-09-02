"""Cutover env compatibility behavior tests."""

from packaging.version import parse as parse_version

from app.config.settings import (
    LEGACY_ENV_ALIAS_MAP,
    LEGACY_ENV_ALIAS_WINDOW,
    apply_legacy_env_aliases,
)
from app.config.version import get_app_version_parsed


# The ``v2-cutover-r1`` legacy env alias compatibility window covers exactly
# the v2.0.x release line. Once the project moves to v2.1.0, the alias map
# and ``apply_legacy_env_aliases`` machinery must be removed.
LEGACY_ENV_ALIAS_EXPIRY_VERSION = parse_version("2.1.0")


def test_legacy_alias_map_contains_expected_cutover_pairs():
    assert LEGACY_ENV_ALIAS_MAP["SCRAPER_DB_URL"] == "DATABASE_URL"
    assert LEGACY_ENV_ALIAS_MAP["LEGACY_DB_URL"] == "LEGACY_DATABASE_URL"


def test_alias_applies_when_new_var_missing():
    env = {"SCRAPER_DB_URL": "sqlite:///./config/legacy.db"}

    events = apply_legacy_env_aliases(environ=env)

    assert env["DATABASE_URL"] == "sqlite:///./config/legacy.db"
    assert len(events) == 1
    assert events[0]["kind"] == "alias_applied"
    assert events[0]["legacy_key"] == "SCRAPER_DB_URL"
    assert events[0]["new_key"] == "DATABASE_URL"
    assert events[0]["selected"] == "legacy"
    assert events[0]["window"] == LEGACY_ENV_ALIAS_WINDOW


def test_new_var_wins_on_conflict_and_emits_warning_event():
    env = {
        "SCRAPER_DB_URL": "sqlite:///./config/legacy.db",
        "DATABASE_URL": "sqlite:///./config/new.db",
    }

    events = apply_legacy_env_aliases(environ=env)

    assert env["DATABASE_URL"] == "sqlite:///./config/new.db"
    assert len(events) == 1
    assert events[0]["kind"] == "conflict"
    assert events[0]["legacy_key"] == "SCRAPER_DB_URL"
    assert events[0]["new_key"] == "DATABASE_URL"
    assert events[0]["selected"] == "new"
    assert events[0]["window"] == LEGACY_ENV_ALIAS_WINDOW


def test_compatibility_window_can_be_disabled():
    env = {"SCRAPER_DB_URL": "sqlite:///./config/legacy.db"}

    events = apply_legacy_env_aliases(environ=env, compat_enabled=False)

    assert "DATABASE_URL" not in env
    assert events == []


def test_legacy_env_aliases_must_be_removed_after_cutover_window():
    """Force the next release to actively decide about the compat shim.

    The ``v2-cutover-r1`` window is intentionally a *single* release pass
    (see ``docs/migration/migration-strategy.md``). When ``version.txt``
    is bumped to v2.1.0 or later, this test fails CI until somebody
    removes ``LEGACY_ENV_ALIAS_MAP`` and ``apply_legacy_env_aliases``
    from ``app/config/settings.py`` and drops the ``apply`` call from
    module load. That keeps a stale compatibility shim from quietly
    overstaying its window.
    """
    current = get_app_version_parsed()
    if current >= LEGACY_ENV_ALIAS_EXPIRY_VERSION:
        assert not LEGACY_ENV_ALIAS_MAP, (
            f"v{current}: legacy env alias compatibility window "
            f"({LEGACY_ENV_ALIAS_WINDOW!r}) closed at "
            f"v{LEGACY_ENV_ALIAS_EXPIRY_VERSION}. Remove "
            "LEGACY_ENV_ALIAS_MAP, apply_legacy_env_aliases, and the "
            "compat-event log call from app/config/settings.py and main.py."
        )


def test_engine_url_default_follows_env(monkeypatch):
    """A services-off container must reach the engine named by ACE_ENGINE_URL before anyone opens Settings."""
    import importlib
    from app.repositories import settings_repository

    monkeypatch.setenv("ACE_ENGINE_URL", "http://engine:6878")
    reloaded = importlib.reload(settings_repository)
    try:
        assert reloaded.SettingsRepository.DEFAULT_ACE_ENGINE_URL == "http://engine:6878"
    finally:
        monkeypatch.delenv("ACE_ENGINE_URL", raising=False)
        importlib.reload(settings_repository)
