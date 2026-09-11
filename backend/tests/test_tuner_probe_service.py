import asyncio
from datetime import datetime, timezone
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


def test_refresh_checks_offline_first_skips_fresh_invalid_and_inactive(alembic_db_session, monkeypatch):
    db_session = alembic_db_session
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='Example', is_active=True)
    db_session.add(tv)
    db_session.flush()
    for key, online, active, fresh in [('a', True, True, False), ('b', False, True, False),
                                     ('c', None, True, False), ('d', True, False, False),
                                     ('e', False, True, True), ('bad', False, True, False)]:
        db_session.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id,
            is_online=online, is_active=active, last_checked=datetime.now(timezone.utc) if fresh else None))
    db_session.commit()
    probe = AsyncMock()
    monkeypatch.setattr(module.ChannelStatusService, 'check_channel_status', probe)
    module.refresh_channel(tv.id, Event())
    assert [call.args[0].id for call in probe.call_args_list] == ['b' * 40, 'c' * 40, 'a' * 40]
    assert all(call.kwargs['priority'] == module.ProbePriority.PLAYBACK for call in probe.call_args_list)


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
