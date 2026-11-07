"""How long the relay waits for an acestream to start: a setting, not a constant.

A source gets ATTEMPT_SECONDS (15) to deliver its first byte and a channel
STARTUP_BUDGET_SECONDS (45) across its sources. A cold P2P start can take
longer (20-50 s in #226): those channels fail on the first press and play on
the retry, with the engine warmed. The two are
now tuner settings, defaulting to the old constants, so nothing changes until
someone raises them.
"""
import asyncio
import dataclasses
from unittest.mock import Mock

import pytest

from app.services.tuner_service import TunerService


@pytest.fixture(autouse=True)
def clean_failures(monkeypatch):
    monkeypatch.setattr('app.services.tuner_playback_service._failures', __import__('collections').OrderedDict())


def test_defaults_are_the_previous_constants(db_session):
    settings = TunerService(db_session).settings()
    assert (settings.source_start_seconds, settings.startup_budget_seconds) == (15, 45)


def test_saved_and_clamped(db_session):
    service = TunerService(db_session)
    service.update_settings(source_start_seconds=40, startup_budget_seconds=58)
    assert (service.settings().source_start_seconds, service.settings().startup_budget_seconds) == (40, 58)
    service.update_settings(source_start_seconds=1, startup_budget_seconds=9999)
    assert (service.settings().source_start_seconds, service.settings().startup_budget_seconds) == (5, 180)


def test_the_api_shows_and_changes_them(client):
    assert client.get('/api/v1/tuner/settings').json()['source_start_seconds'] == 15
    response = client.put('/api/v1/tuner/settings', json={'source_start_seconds': 35, 'startup_budget_seconds': 50})
    assert response.status_code == 200
    assert (response.json()['source_start_seconds'], response.json()['startup_budget_seconds']) == (35, 50)
    assert client.put('/api/v1/tuner/settings', json={'source_start_seconds': 0}).status_code == 422


def _open_slow_channel(alembic_client, alembic_db_session, monkeypatch, per_source):
    """GET a channel whose only source starts after 0.255 s, with `per_source`
    seconds per source: the setting, end to end through the channel route."""
    from app.api.endpoints import tuner
    from app.config.settings import get_settings
    from app.models.models import AcestreamChannel, TVChannel
    from app.services.tuner_network import get_tuner_gate
    import app.services.tuner_playback_service as playback
    monkeypatch.setenv('TUNER_ALLOWED_NETWORKS', '*')
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    try:
        tv = TVChannel(name='Slow', is_active=True)
        alembic_db_session.add(tv)
        alembic_db_session.flush()
        alembic_db_session.add(AcestreamChannel(id='a' * 40, name='cold', tv_channel_id=tv.id,
                                                is_active=True, is_online=True))
        alembic_db_session.commit()
        real = TunerService.settings
        monkeypatch.setattr(TunerService, 'settings', lambda self: dataclasses.replace(
            real(self), source_start_seconds=per_source, startup_budget_seconds=1))
        monkeypatch.setattr(tuner.tuner_probe_service, 'start', Mock())
        monkeypatch.setattr(tuner, '_engine', lambda: Mock())

        async def cold(_engine, content_id, *args, **kwargs):
            await asyncio.sleep(0.255)
            yield b'\x47' + bytes(187)
        monkeypatch.setattr(playback, 'relay_engine_stream', cold)
        return alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    finally:
        get_settings.cache_clear(); get_tuner_gate.cache_clear()


def test_a_slow_source_plays_when_the_setting_gives_it_time(alembic_client, alembic_db_session, monkeypatch):
    # Scaled down: 0.255 s of start against 0.3 s per source.
    response = _open_slow_channel(alembic_client, alembic_db_session, monkeypatch, per_source=0.3)
    assert response.status_code == 200 and response.content.startswith(b'\x47')


def test_the_same_source_fails_with_a_short_setting(alembic_client, alembic_db_session, monkeypatch):
    """The control: what #226 reports, a 502 on the first press."""
    response = _open_slow_channel(alembic_client, alembic_db_session, monkeypatch, per_source=0.1)
    assert response.status_code == 502
