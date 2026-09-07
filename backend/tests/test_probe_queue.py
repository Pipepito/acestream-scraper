import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event
from unittest.mock import AsyncMock

import pytest

from app.services import probe_queue as module
from app.services.probe_queue import ProbePriority, ProbeQueue


@pytest.mark.asyncio
async def test_priority_fifo_and_non_preemption():
    queue = ProbeQueue(cooldown=0)
    active = queue.enqueue(ProbePriority.BACKGROUND)
    await queue.acquire(active)
    order = []
    async def run(priority, name):
        ticket = queue.enqueue(priority)
        await queue.acquire(ticket)
        order.append(name)
        queue.release(ticket, probed=True)
    tasks = [asyncio.create_task(run(priority, name)) for priority, name in [
        (ProbePriority.BACKGROUND, 'scheduled'), (ProbePriority.MANUAL, 'manual 1'),
        (ProbePriority.PLAYBACK, 'tv 1'), (ProbePriority.MANUAL, 'manual 2'),
        (ProbePriority.PLAYBACK, 'tv 2'),
    ]]
    await asyncio.sleep(.01)
    assert order == []  # The running probe owns its cleanup, even for urgent arrivals.
    queue.release(active, probed=True)
    await asyncio.wait_for(asyncio.gather(*tasks), 2)
    assert order == ['tv 1', 'tv 2', 'manual 1', 'manual 2', 'scheduled']


@pytest.mark.asyncio
@pytest.mark.parametrize('outage,delay', [(False, 2), (True, 10)])
async def test_global_cooldown_allows_new_priority_arrivals(monkeypatch, outage, delay):
    clock = [100.0]
    monkeypatch.setattr(module, 'monotonic', lambda: clock[0])
    queue = ProbeQueue()
    active = queue.enqueue(ProbePriority.BACKGROUND)
    await queue.acquire(active)
    queue.release(active, probed=True, engine_unavailable=outage)
    background = queue.enqueue(ProbePriority.BACKGROUND)
    waiter = asyncio.create_task(queue.acquire(background))
    await asyncio.sleep(.01)
    urgent = queue.enqueue(ProbePriority.PLAYBACK)
    urgent_waiter = asyncio.create_task(queue.acquire(urgent))
    clock[0] += delay - .01
    await asyncio.sleep(.06)
    assert not waiter.done() and not urgent_waiter.done()
    clock[0] += .01
    await asyncio.wait_for(urgent_waiter, 1)
    assert not waiter.done()
    queue.release(urgent, probed=False)
    await asyncio.wait_for(waiter, 1)
    queue.release(background, probed=False)


@pytest.mark.asyncio
async def test_cancelled_waiter_does_not_block_other_requests():
    queue = ProbeQueue(cooldown=0)
    active = queue.enqueue(ProbePriority.BACKGROUND)
    await queue.acquire(active)
    urgent = queue.enqueue(ProbePriority.PLAYBACK)
    waiter = asyncio.create_task(queue.acquire(urgent))
    await asyncio.sleep(0)
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    queue.release(active, probed=True)
    next_ticket = queue.enqueue(ProbePriority.BACKGROUND)
    await asyncio.wait_for(queue.acquire(next_ticket), 1)
    queue.release(next_ticket, probed=False)


@pytest.mark.asyncio
async def test_queue_is_shared_across_thread_event_loops():
    queue = ProbeQueue(cooldown=0)
    active = queue.enqueue(ProbePriority.BACKGROUND)
    await queue.acquire(active)
    queued = Event()
    order = []
    def background_thread():
        async def work():
            ticket = queue.enqueue(ProbePriority.BACKGROUND)
            queued.set()
            await queue.acquire(ticket)
            order.append('scheduler')
            queue.release(ticket, probed=True)
        asyncio.run(work())
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(background_thread)
        assert await asyncio.to_thread(queued.wait, 1)
        urgent = queue.enqueue(ProbePriority.MANUAL)
        queue.release(active, probed=True)
        await queue.acquire(urgent)
        order.append('http')
        queue.release(urgent, probed=True)
        await asyncio.wrap_future(future)
    assert order == ['http', 'scheduler']


@pytest.mark.asyncio
async def test_scan_skips_result_written_by_request_that_overtook_it(db_session, monkeypatch):
    from sqlalchemy.orm import Session
    from app.models.models import AcestreamChannel
    from app.repositories.channel_repository import ChannelRepository
    from app.services.channel_status_service import ChannelStatusService
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0))
    channels = {key: AcestreamChannel(id=key * 40, name=key, is_online=False) for key in 'abcd'}
    db_session.add_all(channels.values())
    db_session.commit()
    started = datetime.now(timezone.utc)
    entered, release = asyncio.Event(), asyncio.Event()
    order = []
    async def probe(self, channel, **kwargs):
        if channel.name == 'a':
            entered.set()
            await release.wait()
        order.append(channel.name)
        with Session(bind=db_session.get_bind()) as db:
            ChannelRepository(db).update_channel_status(channel.id, True)
        return {'status': 'online', 'is_online': True}
    monkeypatch.setattr(ChannelStatusService, '_check_channel_status', probe)
    async def check(key, priority):
        return await ChannelStatusService(db_session).check_channel_status(
            channels[key], priority=priority, scan_started_at=started,
        )
    active = asyncio.create_task(check('a', ProbePriority.BACKGROUND))
    await entered.wait()
    background = asyncio.create_task(check('b', ProbePriority.BACKGROUND))
    manual = asyncio.create_task(check('c', ProbePriority.MANUAL))
    playback = asyncio.create_task(check('d', ProbePriority.PLAYBACK))
    manual_b = asyncio.create_task(check('b', ProbePriority.MANUAL))
    await asyncio.sleep(.01)
    release.set()
    await asyncio.wait_for(asyncio.gather(active, background, manual, playback, manual_b), 3)
    assert order == ['a', 'd', 'c', 'b']
    assert background.result()['status'] == 'skipped'
    assert background.result()['is_online'] is True
    assert channels['b'].is_online is False  # Loaded scan inventory was stale.


@pytest.mark.asyncio
async def test_manual_request_can_recheck_old_result_but_background_uses_scan_start(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.channel_status_service import ChannelStatusService
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0))
    now = datetime.now(timezone.utc)
    channel = AcestreamChannel(id='f' * 40, name='f', is_online=True, last_checked=now - timedelta(minutes=2))
    db_session.add(channel)
    db_session.commit()
    service = ChannelStatusService(db_session)
    service._check_channel_status = AsyncMock(return_value={'status': 'online'})
    result = await service.check_channel_status(channel, priority=ProbePriority.BACKGROUND, scan_started_at=now - timedelta(minutes=5))
    assert result['status'] == 'skipped'
    service._check_channel_status.assert_not_called()
    await service.check_channel_status(channel)
    service._check_channel_status.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_active_probe_finishes_cleanup_before_next_probe(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.channel_status_service import ChannelStatusService
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0))
    entered, cleaning, cleaned = asyncio.Event(), asyncio.Event(), asyncio.Event()
    urgent_started = asyncio.Event()
    service = ChannelStatusService(db_session)
    async def probe(channel, **kwargs):
        if channel.name == 'scheduled':
            try:
                entered.set()
                await asyncio.Event().wait()
            finally:
                cleaning.set()
                await cleaned.wait()
        urgent_started.set()
        return {'status': 'online'}
    service._check_channel_status = probe
    active = asyncio.create_task(service.check_channel_status(AcestreamChannel(id='a' * 40, name='scheduled'), persist=False, priority=ProbePriority.BACKGROUND))
    await entered.wait()
    active.cancel()
    await cleaning.wait()
    urgent = asyncio.create_task(service.check_channel_status(AcestreamChannel(id='b' * 40, name='urgent'), persist=False, priority=ProbePriority.PLAYBACK))
    await asyncio.sleep(.06)
    assert not urgent_started.is_set()
    cleaned.set()
    with pytest.raises(asyncio.CancelledError):
        await active
    await asyncio.wait_for(urgent, 1)
    assert urgent_started.is_set()


def test_scheduled_task_uses_background_priority_and_counts_skips(alembic_db_session, monkeypatch):
    db_session = alembic_db_session
    from app.models.models import AcestreamChannel
    from app.tasks import channel_status_task
    channel = AcestreamChannel(id='9' * 40, name='Scheduled', is_active=True)
    db_session.add(channel)
    db_session.commit()
    monkeypatch.setattr(channel_status_task.task_service, 'shutdown_event', Event())
    probe = AsyncMock(return_value={'status': 'skipped'})
    monkeypatch.setattr(channel_status_task.ChannelStatusService, 'check_channel_status', probe)
    result = channel_status_task.run_channel_status_task()
    assert result == {'checked': 0, 'skipped': 1, 'failed': 0}
    assert probe.call_args.kwargs['priority'] == ProbePriority.BACKGROUND
    assert probe.call_args.kwargs['scan_started_at'].tzinfo is not None
