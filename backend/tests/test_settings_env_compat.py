"""Legacy names continue working, with value-free deprecation notices."""
import pytest
from app.config.settings import Settings, LEGACY_ENV_NAMES, get_settings


@pytest.mark.parametrize('legacy,canonical', LEGACY_ENV_NAMES.items())
def test_alias_fallback_and_canonical_precedence(monkeypatch, caplog, legacy, canonical):
    monkeypatch.delenv(canonical, raising=False)
    monkeypatch.setenv(legacy, 'https://legacy.invalid/private-secret')
    setting = Settings(_env_file=None)
    assert 'legacy.invalid' in str(getattr(setting, canonical))
    assert setting.configuration_warnings == [{'legacy': legacy, 'replacement': canonical, 'selected': legacy}]
    assert 'private-secret' not in caplog.text
    assert legacy in caplog.text and canonical in caplog.text
    monkeypatch.setenv(canonical, 'https://canonical.invalid')
    setting = Settings(_env_file=None)
    assert 'canonical.invalid' in str(getattr(setting, canonical))
    assert setting.configuration_warnings[0]['selected'] == canonical


def test_dotenv_alias_and_process_precedence(tmp_path, monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('SCRAPER_DB_URL', raising=False)
    path = tmp_path / '.env'
    path.write_text('SCRAPER_DB_URL=sqlite:///old.db\nENABLE_LEGACY_ENV_ALIASES=false\n')
    assert Settings(_env_file=path).DATABASE_URL == 'sqlite:///old.db'
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///current.db')
    assert Settings(_env_file=path).DATABASE_URL == 'sqlite:///current.db'
    assert Settings(DATABASE_URL='sqlite:///explicit.db', _env_file=path).DATABASE_URL == 'sqlite:///explicit.db'


def test_engine_url_default_uses_compatible_settings(monkeypatch, db_session):
    from app.repositories.settings_repository import SettingsRepository
    monkeypatch.delenv('ACE_ENGINE_URL', raising=False)
    monkeypatch.setenv('ACESTREAM_ENGINE_URL', 'http://engine:6878')
    get_settings.cache_clear()
    try:
        assert SettingsRepository(db_session).DEFAULT_ACE_ENGINE_URL == 'http://engine:6878'
    finally:
        get_settings.cache_clear()
