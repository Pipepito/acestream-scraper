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
                            revision, update_config, resolved_values)


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


def test_existing_database_still_needs_setup_when_config_is_missing(tmp_path):
    (tmp_path / 'scraper.db').touch()
    path = tmp_path / 'runtime-config.json'
    state = ensure_config(path, {'PLAYER_MAX_SESSIONS': '9', 'ENABLE_IPFS': 'true'})
    assert state['setup_complete'] is False
    assert state['runtime']['PLAYER_MAX_SESSIONS'] == 9
    assert state['runtime']['ENABLE_IPFS'] is True
    saved = update_config(path, state['runtime'], revision(state), True)
    assert ensure_config(path, {'PLAYER_MAX_SESSIONS': '2'}) == saved


def test_bundled_endpoint_is_seeded_with_deployment_port():
    values = bootstrap_values({'ENABLE_ACESTREAM_ENGINE': 'true', 'ACESTREAM_HTTP_PORT': '16878'})
    assert values['ACE_ENGINE_URL'] == ''
    assert resolved_values(values)['ACE_ENGINE_URL'] == 'http://localhost:16878'
    assert bootstrap_values({'ENABLE_ACESTREAM_ENGINE': 'true', 'ACE_ENGINE_URL': 'http://external:6878'})['ACE_ENGINE_URL'] == 'http://external:6878'
    assert bootstrap_values({})['ACE_ENGINE_URL'] == ''


def test_wizard_exposes_complete_saved_values_and_defaults(wizard_client):
    path = config_path()
    ensure_config(path, {'PLAYER_MAX_SESSIONS': '7', 'ENABLE_IPFS': 'true'})
    data = read_config(path)
    del data['runtime']['SCRAPER_TIMEOUT']
    path.write_text(json.dumps(data))
    state = wizard_client.get('/api/v1/setup').json()
    assert state['runtime']['PLAYER_MAX_SESSIONS'] == 7
    assert state['runtime']['ENABLE_IPFS'] is True
    assert state['runtime']['SCRAPER_TIMEOUT'] == OPTION_MAP['SCRAPER_TIMEOUT']['default']
    assert state['setup_complete'] is False


def test_upgrade_imports_missing_keys_once_and_ignores_invalid_overridden_env(tmp_path):
    path = tmp_path / 'runtime-config.json'
    path.write_text(json.dumps({'version': 1, 'setup_complete': True, 'runtime': {
        'ACE_ENGINE_URL': '', 'ENABLE_ACESTREAM_ENGINE': False, 'PLAYER_MAX_SESSIONS': 7,
    }}))
    data = ensure_config(path, {'PLAYER_MAX_SESSIONS': 'invalid', 'ENABLE_ACESTREAM_ENGINE': 'true',
                              'ACE_ENGINE_URL': 'http://ignored:1234', 'ACEXY_LISTEN_ADDR': ':8084',
                              'ACEXY_BUFFER_SIZE': '10MiB', 'ACEXY_NO_RESPONSE_TIMEOUT': '10s', 'TZ': 'Europe/Madrid'})
    assert data['setup_complete'] is True
    assert data['runtime']['PLAYER_MAX_SESSIONS'] == 7
    assert data['runtime']['ENABLE_ACESTREAM_ENGINE'] is False
    assert data['runtime']['ACE_ENGINE_URL'] == ''
    assert data['runtime']['ACEXY_LISTEN_ADDR'] == ':8084'
    env = environment_for(data, {'ACEXY_BUFFER_SIZE': 'wrong', 'ACEXY_LISTEN_ADDR': ':1234', 'API_TOKEN': 'private'})
    assert env['ACEXY_LISTEN_ADDR'] == ':8084'
    assert env['ACEXY_BUFFER_SIZE'] == '10MiB'
    assert env['TZ'] == 'Europe/Madrid'
    assert env['API_TOKEN'] == 'private'
    assert ensure_config(path, {'ACEXY_LISTEN_ADDR': ':9999'}) == data


@pytest.mark.parametrize('values', [
    {'ACESTREAM_HTTP_PORT': 65536}, {'ACEXY_LISTEN_ADDR': ':0'},
    {'ACEXY_LISTEN_ADDR': 'http://host:8080'}, {'ACEXY_HOST': 'host;touch /tmp/pwn'},
    {'ZERONET_UI_HOST': 'localhost $(id)'}, {'ZERONET_UI_HOST': '--help'},
    {'IPFS_API_HOST': 'not-an-ip'}, {'ACEXY_BUFFER_SIZE': 'forever'},
    {'ACEXY_NO_RESPONSE_TIMEOUT': 'tomorrow'}, {'TZ': '../../etc/passwd'},
])
def test_service_options_are_validated_as_data(values):
    from runtime_config import validate_values
    with pytest.raises(ConfigError): validate_values(values)


def test_checker_is_derived_not_saved_as_external(wizard_client):
    path = config_path()
    ensure_config(path, {'ENABLE_ACESTREAM_ENGINE': 'true', 'ENABLE_ACESTREAM_CHECK_ENGINE': 'true',
                        'ACESTREAM_HTTP_PORT': '16878', 'ACEXY_LISTEN_ADDR': ':8084'})
    first = wizard_client.get('/api/v1/setup').json()
    assert first['runtime']['ACE_ENGINE_URL'] == ''
    assert first['resolved_runtime']['ACE_ENGINE_URL'] == 'http://localhost:16878'
    assert first['resolved_runtime']['ACE_CHECK_ENGINE_URL'] == 'http://127.0.0.1:6880'
    assert first['runtime']['ACE_CHECK_ENGINE_URL'] == ''
    response = wizard_client.put('/api/v1/setup', json={'runtime': first['runtime'], 'expected_revision': first['revision']})
    assert response.status_code == 200, response.text
    assert read_config(path)['runtime']['ACE_CHECK_ENGINE_URL'] == ''


def test_setup_reports_saved_preferences_without_changing_them(wizard_client, db_session):
    from app.repositories.settings_repository import SettingsRepository
    repository = SettingsRepository(db_session)
    repository.set_setting('ace_engine_url', '')
    repository.set_setting('public_base_url', 'https://tv.example')
    repository.set_setting('playback_routing', '{"use_acexy":true,"acexy_url":"http://localhost:8084"}')
    state = wizard_client.get('/api/v1/setup').json()
    assert state['saved_overrides']['ACE_ENGINE_URL'] == ''
    assert state['saved_overrides']['PUBLIC_BASE_URL'] == 'https://tv.example'
    assert state['saved_overrides']['ACEXY_URL'] == 'http://localhost:8084'
    assert repository.get_setting('ace_engine_url') == ''


def test_service_restart_environment_uses_saved_values(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'db.sqlite'),
           'SUPERVISOR_RUN_DIR': str(tmp_path / 'run'), 'ACEXY_LISTEN_ADDR': ':8084',
           'ACEXY_NO_RESPONSE_TIMEOUT': '10s', 'ACEXY_BUFFER_SIZE': '5MiB'}
    command = [sys.executable, str(root / 'runtime_config.py')]
    probe = [sys.executable, '-c', 'import os; print(os.environ["ACEXY_LISTEN_ADDR"], os.environ["ACEXY_NO_RESPONSE_TIMEOUT"], os.environ["ACEXY_BUFFER_SIZE"])']
    assert subprocess.check_output([*command, 'run', *probe], env=env, text=True).strip() == ':8084 10s 5MiB'
    path = config_path(env['DATABASE_URL'])
    first = read_config(path)
    update_config(path, {'ACEXY_LISTEN_ADDR': ':8086', 'ACEXY_BUFFER_SIZE': '10MiB'}, revision(first), True)
    assert subprocess.check_output([*command, 'health', *probe], env=env, text=True).strip() == ':8084 10s 5MiB'
    assert subprocess.check_output([*command, 'run', *probe], env=env, text=True).strip() == ':8086 10s 10MiB'
