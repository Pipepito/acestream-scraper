"""Cutover env compatibility behavior tests."""

from app.config.settings import (
    LEGACY_ENV_ALIAS_MAP,
    LEGACY_ENV_ALIAS_WINDOW,
    apply_legacy_env_aliases,
)


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
