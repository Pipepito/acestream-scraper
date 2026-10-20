import asyncio
from datetime import datetime, timedelta, timezone
from threading import Event
from unittest.mock import AsyncMock

import pytest

from app.services import tuner_probe_service as module


@pytest.mark.asyncio
async def test_refresh_coalesces_requests_and_bounds_workers(monkeypatch):
    entered, release = Event(), Event()
    calls = []
    def refresh(channel_id, stopping):
        calls.append(channel_id)
        entered.set()
        release.wait(2)
    monkeypatch.setattr(module, 'refresh_channel', refresh)
    service = module.TunerProbeService()
    first = service.start(1)
    assert service.start(1) is first
    second = service.start(2)
    while not entered.is_set():
        await asyncio.sleep(.001)
    assert calls == [1]
    release.set()
    await asyncio.gather(first, second)
    assert calls == [1, 2]
    assert service.tasks == {}
    await service.stop()


def _sources(db_session, rows):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='Example', is_active=True)
    db_session.add(tv)
    db_session.flush()
    for key, online, active, checked_minutes_ago in rows:
        checked = None if checked_minutes_ago is None else \
            datetime.now(timezone.utc) - timedelta(minutes=checked_minutes_ago)
        db_session.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id,
            is_online=online, is_active=active, last_checked=checked))
    db_session.commit()
    return tv


def test_refresh_follows_the_relay_order_and_skips_fresh_invalid_and_inactive(alembic_db_session, monkeypatch):
    """While a channel plays, only the sources the relay would try next."""
    tv = _sources(alembic_db_session, [('a', True, True, 30), ('b', False, True, None),
                                      ('c', None, True, None), ('d', True, False, 30),
                                      ('e', False, True, 0), ('bad', False, True, None)])
    probe = AsyncMock(return_value={'status': 'online'})
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', probe)
    module.refresh_channel(tv.id, Event())
    assert [call.args[0].id for call in probe.call_args_list] == ['a' * 40, 'b' * 40, 'c' * 40]
    assert all(call.kwargs['priority'] == module.ProbePriority.PLAYBACK for call in probe.call_args_list)


def test_refresh_checks_an_http_source_in_the_relay_order(alembic_db_session, monkeypatch):
    """HTTP sources are relayed too (#264), so a refresh checks them in turn."""
    from app.models.models import AcestreamChannel
    tv = _sources(alembic_db_session, [('a', True, True, 30)])
    http_id = 'url:' + 'f' * 40
    alembic_db_session.add(AcestreamChannel(id=http_id, name='laSexta', tv_channel_id=tv.id,
        is_online=None, is_active=True, stream_url='atresplayer://lasexta'))
    alembic_db_session.commit()
    probe = AsyncMock(return_value={'status': 'online'})
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', probe)
    module.refresh_channel(tv.id, Event())
    assert [call.args[0].id for call in probe.call_args_list] == ['a' * 40, http_id]


def test_refresh_checks_at_most_three_and_leaves_recent_ones_alone(alembic_db_session, monkeypatch):
    """A 120 s view of a channel with 39 sources used to check them all."""
    rows = [('a', True, True, 5)]                                   # checked 5 min ago: left alone
    rows += [(k, True, True, 30) for k in 'bcdefgh']                # online, checked 30 min ago
    tv = _sources(alembic_db_session, rows)
    probe = AsyncMock(return_value={'status': 'online'})
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', probe)
    module.refresh_channel(tv.id, Event())
    checked = [call.args[0].id[0] for call in probe.call_args_list]
    assert len(checked) == module.PLAYBACK_REFRESH_LIMIT
    assert 'a' not in checked


def test_a_skipped_source_does_not_use_up_the_limit(alembic_db_session, monkeypatch):
    """The source playing is owned by the relay; the status service skips it."""
    tv = _sources(alembic_db_session, [(k, True, True, 30) for k in 'abcde'])
    results = iter([{'status': 'skipped'}] + [{'status': 'online'}] * 10)
    probe = AsyncMock(side_effect=lambda *a, **k: next(results))
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', probe)
    module.refresh_channel(tv.id, Event())
    assert probe.call_count == module.PLAYBACK_REFRESH_LIMIT + 1


def test_refresh_stops_when_asked(alembic_db_session, monkeypatch):
    tv = _sources(alembic_db_session, [(k, True, True, 30) for k in 'abc'])
    stop = Event()
    calls = []

    async def check(self, channel, priority):
        calls.append(channel.id)
        stop.set()                                                  # the viewer leaves during the first
        return {'status': 'online'}
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', check)
    module.refresh_channel(tv.id, stop)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_stop_channel_ends_that_channels_refresh(monkeypatch):
    entered = Event()
    seen = []

    def refresh(channel_id, stopping):
        entered.set()
        seen.append(stopping.wait(2))
    monkeypatch.setattr(module, 'refresh_channel', refresh)
    service = module.TunerProbeService()
    task = service.start(7)
    while not entered.is_set():
        await asyncio.sleep(.001)
    service.stop_channel(7)
    await task
    assert seen == [True]
    assert service.channel_stops == {}
    await service.stop()


@pytest.mark.asyncio
async def test_shutdown_drains_running_probe_and_skips_queued_work(monkeypatch):
    entered = Event()
    calls = []
    def refresh(channel_id, stopping):
        calls.append(channel_id)
        entered.set()
        stopping.wait(2)
    monkeypatch.setattr(module, 'refresh_channel', refresh)
    service = module.TunerProbeService()
    service.start(1)
    while not entered.is_set():
        await asyncio.sleep(.001)
    service.start(2)
    await service.stop()
    assert calls == [1]
    assert service.tasks == {}


@pytest.mark.asyncio
async def test_browser_stream_refresh_resolves_tv_channel(alembic_db_session, monkeypatch):
    db_session = alembic_db_session
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='Browser channel')
    db_session.add(tv)
    db_session.flush()
    stream = AcestreamChannel(id='f' * 40, name='Browser stream', tv_channel_id=tv.id)
    db_session.add(stream)
    db_session.commit()
    service = module.TunerProbeService()
    called = []
    monkeypatch.setattr(service, 'start', called.append)
    await service.start_for_stream(stream.id)
    assert called == [tv.id]
    await service.start_for_stream('0' * 40)
    assert called == [tv.id]
