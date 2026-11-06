"""«Starts with»: the next opening of channel N from this device begins with
source X (acestream-tvbox #12, #20).

The Kodi skin asks for it with a short HTTP request and then opens the
channel through the PVR as always. The request is per device (client IP),
lasts 30 s from when it was made and covers one opening only: Kodi's HEAD and
both GETs start with it, a later GET does not.
"""
from collections import OrderedDict
from unittest.mock import Mock

import pytest

from app.models.models import AcestreamChannel, TVChannel


@pytest.fixture
def channel_failing():
    """Sources the fake relay gives up (on_source_failure) before going on."""
    return set()


@pytest.fixture
def channel(channel_failing, alembic_client, alembic_db_session, monkeypatch):
    """A channel with an online source, one a check found offline a moment
    ago (the relay leaves it out) and a source of another channel; the relay
    replaced by one that records the candidates it was given."""
    from datetime import datetime, timedelta, timezone
    from app.api.endpoints import tuner
    from app.config.settings import get_settings
    from app.services import tuner_first_source, tuner_playback_service
    from app.services.stream_relay import relay_registry
    from app.services.tuner_network import get_tuner_gate
    monkeypatch.setenv('TUNER_ALLOWED_NETWORKS', '*')
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    monkeypatch.setattr(tuner_first_source, '_choices', {})
    monkeypatch.setattr('app.services.tuner_playback_service._failures', OrderedDict())
    tv = TVChannel(name='Deportes Uno', is_active=True)
    other = TVChannel(name='Deportes Dos', is_active=True)
    alembic_db_session.add_all([tv, other]); alembic_db_session.flush()
    alembic_db_session.add_all([
        AcestreamChannel(id='a' * 40, name='online', tv_channel_id=tv.id, is_active=True, is_online=True),
        AcestreamChannel(id='b' * 40, name='offline', tv_channel_id=tv.id, is_active=True, is_online=False,
                         last_checked=datetime.now(timezone.utc) - timedelta(minutes=1)),
        AcestreamChannel(id='c' * 40, name='foreign', tv_channel_id=other.id, is_active=True, is_online=True),
    ])
    alembic_db_session.commit()
    monkeypatch.setattr(tuner.tuner_probe_service, 'start', Mock(return_value=None))
    monkeypatch.setattr(tuner, '_engine', lambda: Mock())
    calls = []
    failing = channel_failing

    async def ranked(_engine, ids, _label, claim, *, candidate_provider, on_source_failure, **kwargs):
        try:
            calls.append({'ids': list(ids), 'provider': candidate_provider})
            if ids[0] in failing:
                await on_source_failure(ids[0])
            yield b'video'
        finally:
            relay_registry.close(claim.id)
    # The channel session reads the relay from tuner_playback_service.
    monkeypatch.setattr(tuner_playback_service, 'relay_ranked_streams', ranked)
    yield tv, calls
    get_settings.cache_clear(); get_tuner_gate.cache_clear()


def _ask(client, tv_id, source):
    return client.post(f'/tuner/channel/{tv_id}/first-source', json={'source': source})


def test_the_chosen_source_goes_first_even_if_it_is_marked_offline(alembic_client, channel):
    tv, calls = channel
    assert _ask(alembic_client, tv.id, 'b' * 40).status_code == 204
    assert alembic_client.get(f'/tuner/channel/{tv.id}.ts').content == b'video'
    assert calls[0]['ids'] == ['b' * 40, 'a' * 40]


def test_without_a_request_the_order_is_the_automatic_one(alembic_client, channel):
    tv, calls = channel
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]


def test_kodi_head_and_both_gets_start_with_it(alembic_client, channel):
    tv, calls = channel
    _ask(alembic_client, tv.id, 'b' * 40)
    url = f'/tuner/channel/{tv.id}.ts'
    assert alembic_client.head(url).status_code == 200
    alembic_client.get(url)
    alembic_client.get(url)
    assert [call['ids'][0] for call in calls] == ['b' * 40, 'b' * 40]


def test_it_lasts_30_seconds_from_the_request(alembic_client, channel, monkeypatch):
    from app.services import tuner_first_source, tuner_playback_service
    tv, calls = channel
    now = [1000.0]
    monkeypatch.setattr(tuner_first_source.time, 'monotonic', lambda: now[0])
    _ask(alembic_client, tv.id, 'b' * 40)
    now[0] += 29
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    now[0] += 1
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert [call['ids'] for call in calls] == [['b' * 40, 'a' * 40], ['a' * 40]]


def test_only_the_device_that_asked(alembic_client, channel):
    from fastapi.testclient import TestClient
    tv, calls = channel
    _ask(alembic_client, tv.id, 'b' * 40)
    TestClient(alembic_client.app, client=('192.168.1.50', 50000)).get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]


def test_only_that_channel(alembic_client, channel):
    tv, calls = channel
    _ask(alembic_client, tv.id, 'b' * 40)
    assert alembic_client.get(f'/tuner/channel/{tv.id + 1}.ts').content == b'video'
    assert calls[0]['ids'] == ['c' * 40]


def test_a_source_of_another_channel_is_refused(alembic_client, channel):
    tv, calls = channel
    response = _ask(alembic_client, tv.id, 'c' * 40)
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'SOURCE_NOT_ON_CHANNEL'
    assert _ask(alembic_client, 999_999, 'a' * 40).status_code == 404
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]


def test_automatic_cancels_the_request(alembic_client, channel):
    tv, calls = channel
    _ask(alembic_client, tv.id, 'b' * 40)
    assert alembic_client.delete(f'/tuner/channel/{tv.id}/first-source').status_code == 204
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]


def test_a_source_that_failed_a_moment_ago_does_not_go_first(alembic_client, channel):
    from app.services.tuner_playback_service import record_source_failure
    tv, calls = channel
    _ask(alembic_client, tv.id, 'b' * 40)
    record_source_failure('b' * 40)
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]


def test_once_tried_the_relay_is_never_offered_it_again(alembic_client, channel):
    """The refreshed candidates the relay reads after a failure leave the
    chosen source out, even when it is online: no going back to it."""
    import asyncio
    tv, calls = channel
    _ask(alembic_client, tv.id, 'a' * 40)
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert calls[0]['ids'] == ['a' * 40]
    current, _refreshing = asyncio.run(calls[0]['provider']())
    assert 'a' * 40 not in current


def test_zapping_away_and_back_after_it_played_is_automatic(alembic_client, channel, monkeypatch):
    """Only that opening: once Kodi's GETs of it are over, changing channel
    and coming back within the 30 s uses the automatic order."""
    from app.services import tuner_first_source, tuner_playback_service
    tv, calls = channel
    now = [1000.0]
    monkeypatch.setattr(tuner_first_source.time, 'monotonic', lambda: now[0])
    _ask(alembic_client, tv.id, 'b' * 40)
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    now[0] += 10
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert [call['ids'] for call in calls] == [['b' * 40, 'a' * 40], ['a' * 40]]


def test_a_chosen_source_that_failed_is_not_first_on_the_next_get(alembic_client, channel, channel_failing,
                                                                   monkeypatch):
    """Not even within the moment left for Kodi's second GET, and not
    because of the relay's failure memory: with it off, still not first."""
    from app.services import tuner_playback_service
    monkeypatch.setattr(tuner_playback_service, 'FAILURE_COOLDOWN_SECONDS', 0)
    tv, calls = channel
    channel_failing.add('b' * 40)
    _ask(alembic_client, tv.id, 'b' * 40)
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    alembic_client.get(f'/tuner/channel/{tv.id}.ts')
    assert [call['ids'] for call in calls] == [['b' * 40, 'a' * 40], ['a' * 40]]


def test_kodi_overlapping_gets_share_it_and_then_it_is_spent(monkeypatch):
    """Kodi's second GET may start before the first one closes: both start
    with the chosen source, and once both have ended it is spent, even
    within the moment a second GET gets."""
    from app.services import tuner_first_source, tuner_playback_service
    monkeypatch.setattr(tuner_first_source, '_choices', {})
    tuner_first_source.choose_first_source('10.0.0.9', 7, 'b' * 40)
    first = tuner_first_source.open_channel('10.0.0.9', 7)
    second = tuner_first_source.open_channel('10.0.0.9', 7)
    first.ended()
    second.ended()
    assert (first.chosen, second.chosen) == ('b' * 40, 'b' * 40)
    assert tuner_first_source.open_channel('10.0.0.9', 7).chosen is None
