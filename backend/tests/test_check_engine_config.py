from unittest.mock import AsyncMock, Mock
import pytest


@pytest.fixture(autouse=True)
def no_bundled_checker(monkeypatch):
    from app.config.settings import settings
    monkeypatch.setenv('ENABLE_ACESTREAM_CHECK_ENGINE', 'false')
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', '')


def test_checker_config_routes_and_persists(client, db_session):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.check_engine_config_service import CheckEngineConfigService
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, 'http://playback.test:6878')
    resolver = CheckEngineConfigService(repo)
    assert resolver.effective_url() == 'http://playback.test:6878'
    response = client.put('/api/v1/config/check-engine', json={'use_dedicated': True, 'url': 'http://checker.test:6880/'})
    assert response.status_code == 200
    assert resolver.effective_url() == 'http://checker.test:6880'
    assert client.get('/api/v1/config/check-engine').json()['use_dedicated'] is True
    assert client.put('/api/v1/config/check-engine', json={'use_dedicated': False, 'url': 'http://checker.test:6880'}).status_code == 200
    assert resolver.effective_url() == 'http://playback.test:6878'
    assert client.put('/api/v1/config/ace_engine_url', json={'value': ''}).status_code == 200
    assert resolver.effective_url() == ''


@pytest.mark.parametrize('url', ['', 'ftp://checker.test', 'http://user:secret@checker.test', 'http://checker.test/path', 'http://bad host'])
def test_checker_rejects_invalid_enabled_urls(client, url):
    assert client.put('/api/v1/config/check-engine', json={'use_dedicated': True, 'url': url}).status_code == 422


def test_bundled_checker_is_container_managed(client, monkeypatch):
    monkeypatch.setenv('ENABLE_ACESTREAM_CHECK_ENGINE', 'true')
    assert client.get('/api/v1/config/check-engine').json()['managed'] is True
    assert client.put('/api/v1/config/check-engine', json={'use_dedicated': False, 'url': ''}).status_code == 409


def test_explicit_disable_overrides_external_environment(client, db_session, monkeypatch):
    from app.config.settings import settings
    from app.repositories.settings_repository import SettingsRepository
    from app.services.check_engine_config_service import CheckEngineConfigService
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', 'http://unreachable.test:6880')
    assert client.get('/api/v1/config/check-engine').json()['use_dedicated'] is True
    client.put('/api/v1/config/check-engine', json={'use_dedicated': False, 'url': ''})
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, '')
    assert CheckEngineConfigService(repo).effective_url() == ''


@pytest.mark.asyncio
async def test_no_engine_does_not_probe_or_change_results(db_session, monkeypatch):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.channel_status_service import ChannelStatusService
    from app.models.models import AcestreamChannel
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, '')
    service = ChannelStatusService(db_session)
    fetch = AsyncMock()
    monkeypatch.setattr(service, '_fetch_engine_response', fetch)
    channel = AcestreamChannel(id='a' * 40, name='Test', is_online=True)
    result = await service.check_channel_status(channel)
    assert result['status'] == 'skipped'
    assert channel.is_online is True
    fetch.assert_not_called()


def test_no_engine_does_not_launch_job(client, db_session, monkeypatch):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.task_service import task_service
    from app.tasks import channel_status_task
    from app.models.models import AcestreamChannel
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, '')
    trigger = Mock()
    monkeypatch.setattr(task_service, 'run_task_now', trigger)
    response = client.post('/api/v1/background-tasks/channel_status/run')
    assert response.json()['status'] == 'disabled'
    trigger.assert_not_called()
    # Direct jobs create their own session; API dependency overrides do not apply.
    monkeypatch.setattr(channel_status_task, 'SessionLocal', lambda: db_session)
    original_query = db_session.query

    def query_without_channels(*entities, **kwargs):
        assert AcestreamChannel not in entities, 'Disabled checks must not load channels'
        return original_query(*entities, **kwargs)

    monkeypatch.setattr(db_session, 'query', query_without_channels)
    result = channel_status_task.run_channel_status_task()
    assert result == {
        'checked': 0, 'skipped': 0, 'failed': 0,
        'message': 'No engine configured; status checks are disabled.',
    }


def test_optional_health_cards_do_not_probe_missing_engines(tmp_path):
    from app.services.system_services_service import SystemServicesService
    http = Mock()
    service = SystemServicesService(run_dir=str(tmp_path), external_engine_url='', check_engine_url='', http_get=http)
    for name in ('acestream', 'acestream-check'):
        result = service.get_service(name)
        assert result['state'] == 'disabled'
        assert not result['running']
    http.assert_not_called()
