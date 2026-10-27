"""Persisted bootstrap, restart boundaries, atomic saves and wizard access."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from runtime_config import (ConfigConflict, ConfigError, OPTION_MAP, bootstrap_values,
                            config_path, ensure_config, environment_for, read_config,
                            revision, update_config)


def test_seed_once_preserves_environment_and_secrets_boundary(tmp_path):
    path = tmp_path / 'runtime-config.json'
    first = ensure_config(path, {'PLAYER_MAX_SESSIONS': '7', 'API_TOKEN': 'private', 'APP_COMMAND': 'never save'})
    assert first['runtime']['PLAYER_MAX_SESSIONS'] == 7
    assert not first['setup_complete']
    assert 'private' not in path.read_text() and 'APP_COMMAND' not in path.read_text()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert ensure_config(path, {'PLAYER_MAX_SESSIONS': '9'}) == first
    env = environment_for(first, {'PLAYER_MAX_SESSIONS': '9', 'API_TOKEN': 'private'})
    assert env['PLAYER_MAX_SESSIONS'] == '7' and env['API_TOKEN'] == 'private'


def test_aliases_dotenv_and_saved_blank(tmp_path, monkeypatch):
    from app.config.settings import Settings
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///' + str(tmp_path / 'db.sqlite'))
    monkeypatch.setenv('ACESTREAM_ENGINE_URL', 'http://legacy:6878')
    assert bootstrap_values(dict(os.environ))['ACE_ENGINE_URL'] == 'http://legacy:6878'
    path = config_path()
    ensure_config(path, {'ACE_ENGINE_URL': ''})
    assert Settings(_env_file=None).ACE_ENGINE_URL == ''
    dotenv = tmp_path / '.env'
    dotenv.write_text('PLAYER_MAX_SESSIONS=99\n')
    assert Settings(_env_file=dotenv).PLAYER_MAX_SESSIONS == 3


def test_saved_file_and_constructor_database_location(tmp_path):
    from app.config.settings import Settings
    path = config_path('sqlite:///' + str(tmp_path / 'db.sqlite'))
    ensure_config(path, {'PLAYER_MAX_SESSIONS': '6'})
    assert Settings(DATABASE_URL='sqlite:///' + str(tmp_path / 'db.sqlite'), _env_file=None).PLAYER_MAX_SESSIONS == 6


@pytest.mark.parametrize('value', ['bad json', '{"version":99}', '[]'])
def test_invalid_existing_config_is_never_overwritten(tmp_path, value):
    path = tmp_path / 'runtime-config.json'
    path.write_text(value)
    with pytest.raises(ConfigError): ensure_config(path, {})
    assert path.read_text() == value


def test_symlink_is_rejected(tmp_path):
    target = tmp_path / 'private'
    target.write_text('secret')
    path = tmp_path / 'runtime-config.json'
    path.symlink_to(target)
    with pytest.raises(ConfigError): ensure_config(path, {})
    assert target.read_text() == 'secret'


def test_stale_edit_cannot_clobber_and_invalid_save_keeps_original(tmp_path):
    path = tmp_path / 'runtime-config.json'
    first = ensure_config(path, {})
    second = update_config(path, {'PLAYER_MAX_SESSIONS': 5}, revision(first), True)
    with pytest.raises(ConfigConflict): update_config(path, {}, revision(first), True)
    for bad in [{'PLAYER_MAX_SESSIONS': -1}, {'APP_COMMAND': 'id'}, {'ENABLE_IPFS': 'yes'}, {'ACE_ENGINE_URL': 'http://user:secret@host'}]:
        with pytest.raises(ConfigError): update_config(path, bad, revision(second), True)
    assert read_config(path) == second


def test_restart_snapshot_does_not_follow_pending_changes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'db.sqlite'), 'SUPERVISOR_RUN_DIR': str(tmp_path / 'run')}
    command = [sys.executable, str(root / 'runtime_config.py')]
    probe = [sys.executable, '-c', 'import os; print(os.environ["PLAYER_MAX_SESSIONS"])']
    assert subprocess.check_output([*command, 'run', *probe], env=env, text=True).strip() == '3'
    path = config_path(env['DATABASE_URL'])
    first = read_config(path)
    update_config(path, {'PLAYER_MAX_SESSIONS': 8}, revision(first), True)
    assert subprocess.check_output([*command, 'health', *probe], env=env, text=True).strip() == '3'
    assert subprocess.check_output([*command, 'run', *probe], env=env, text=True).strip() == '8'


@pytest.fixture
def wizard_client(client, tmp_path, monkeypatch):
    from app.config.settings import get_settings
    database_url = 'sqlite:///' + str(tmp_path / 'wizard.db')
    monkeypatch.setenv('DATABASE_URL', database_url)
    monkeypatch.setattr(get_settings(), 'DATABASE_URL', database_url)
    return client


def test_wizard_save_is_authenticated_and_does_not_mutate_runtime(wizard_client, monkeypatch):
    client = wizard_client
    monkeypatch.setenv('API_TOKEN', 'wizard-private-credential')
    assert client.get('/api/v1/setup').status_code == 401
    headers = {'X-Api-Token': 'wizard-private-credential'}
    first = client.get('/api/v1/setup', headers=headers).json()
    assert first['api_protected'] is True
    response = client.put('/api/v1/setup', headers=headers, json={'runtime': {'PLAYER_MAX_SESSIONS': 8}, 'expected_revision': first['revision']})
    assert response.status_code == 200, response.text
    assert response.json()['restart_required'] is True
    assert 'wizard-private-credential' not in response.text
    from app.config.settings import get_settings
    assert get_settings().PLAYER_MAX_SESSIONS == 3
    assert client.put('/api/v1/setup', headers=headers, json={'runtime': {}, 'expected_revision': first['revision']}).status_code == 409


def test_unavailable_service_cannot_be_enabled(wizard_client, monkeypatch):
    client = wizard_client
    monkeypatch.delenv('SUPERVISOR_RUN_DIR', raising=False)
    first = client.get('/api/v1/setup').json()
    assert 'ENABLE_ACESTREAM_ENGINE' in first['unavailable']
    response = client.put('/api/v1/setup', json={'runtime': {'ENABLE_ACESTREAM_ENGINE': True}, 'expected_revision': first['revision']})
    assert response.status_code == 422
    assert client.get('/api/v1/setup').json()['revision'] == first['revision']


def test_config_default_remains_live_until_operator_saves(db_session, monkeypatch):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.config_service import ConfigService
    from app.config.settings import get_settings
    repository = SettingsRepository(db_session)
    ConfigService(repository)
    monkeypatch.setattr(get_settings(), 'ACE_ENGINE_URL', 'http://new-engine:6878')
    assert repository.get_setting('ace_engine_url') == 'http://new-engine:6878'
    repository.set_setting('ace_engine_url', '')
    assert repository.get_setting('ace_engine_url') == ''


def test_fresh_database_has_no_sources(alembic_client, alembic_db_session):
    from app.models.models import ScrapedURL, AcestreamChannel
    assert alembic_db_session.query(ScrapedURL).count() == 0
    assert alembic_db_session.query(AcestreamChannel).count() == 0


def test_registry_defaults_match_settings():
    from app.config.settings import Settings
    for name, option in OPTION_MAP.items():
        if name in Settings.model_fields:
            default = Settings.model_fields[name].default
            if name == 'CORS_ORIGINS': default = ','.join(default)
            assert option['default'] == default, name


def test_any_negative_guide_retention_remains_a_supported_opt_out(tmp_path):
    path = tmp_path / 'runtime-config.json'
    ensure_config(path, {'EPG_PROGRAM_RETENTION_HOURS': '-48'})
    assert read_config(path)['runtime']['EPG_PROGRAM_RETENTION_HOURS'] == -48


def test_wizard_accepts_documented_json_cors_text(tmp_path):
    path = tmp_path / 'runtime-config.json'
    first = ensure_config(path, {})
    updated = update_config(path, {'CORS_ORIGINS': '["https://one.example", "https://two.example"]'}, revision(first), True)
    assert updated['runtime']['CORS_ORIGINS'] == 'https://one.example,https://two.example'
