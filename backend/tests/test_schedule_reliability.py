"""Concurrency and user-facing schedule contracts."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timezone
import sqlite3
import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.schemas.config import ScheduleAnchors
from app.services.task_service import TaskService


def test_due_jobs_wait_in_order_and_failure_releases_queue():
    service = TaskService()
    entered = Event()
    release = Event()
    calls = []

    def first():
        entered.set()
        assert release.wait(3)
        calls.append('first')
        raise ValueError('failed')

    def second():
        calls.append('second')
        return 2

    with ThreadPoolExecutor(2) as pool:
        one = pool.submit(service._instrument_task('epg_refresh', first, maintenance=True))
        assert entered.wait(2)
        two = pool.submit(service._instrument_task('url_scraping', second, maintenance=True))
        deadline = time.monotonic() + 2
        while not service.get_task_state('url_scraping') and time.monotonic() < deadline:
            time.sleep(.01)
        try:
            state = service.get_task_state('url_scraping')
            assert state['status'] == 'waiting'
            assert state['last_run'] is None
            assert service.run_task_now('url_scraping') == 'already_running'
            assert not calls
        finally:
            release.set()
        with pytest.raises(ValueError):
            one.result(3)
        assert two.result(3) == 2
    assert calls == ['first', 'second']


def test_clock_schedule_survives_restart_and_interval_changes():
    schedule = ScheduleAnchors(timezone='Europe/Madrid', url_scraping='03:15')
    now = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
    for _ in range(2):
        service = TaskService()
        service.configure_schedule(schedule)
        trigger = service._interval_trigger('url_scraping', 6 * 3600)
        assert trigger.get_next_fire_time(None, now).isoformat() == '2026-09-10T03:15:00+02:00'
        winter = datetime(2026, 12, 10, 0, 0, tzinfo=timezone.utc)
        assert trigger.get_next_fire_time(None, winter).isoformat() == '2026-12-10T03:15:00+01:00'
        service.add_interval_task(lambda: None, 3600, 'url_scraping')
        service.configure_schedule(schedule)
        assert service.reschedule_task('url_scraping', 2 * 3600)
        assert service.scheduler.get_job('url_scraping').trigger.get_next_fire_time(None, now).hour == 3


def test_schedule_api_roundtrip_and_validation(client):
    payload = {'timezone': 'Europe/Madrid', 'url_scraping': '03:15', 'epg_refresh': '02:00', 'channel_status': '03:30'}
    assert client.put('/api/v1/config/schedule-anchors', json=payload).status_code == 200
    assert client.get('/api/v1/config/schedule-anchors').json() == payload
    for key, value in [('timezone', 'Invalid/Zone'), ('url_scraping', '25:00'), ('channel_status', '3:00')]:
        assert client.put('/api/v1/config/schedule-anchors', json={**payload, key: value}).status_code == 422
    assert client.get('/api/v1/config/schedule-anchors').json() == payload


def test_status_write_retries_real_sqlite_lock_then_session_is_usable(alembic_db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.repositories.channel_repository import ChannelRepository
    from app.config import database_retry
    db_session = alembic_db_session
    channel_id = 'a' * 40
    db_session.add(AcestreamChannel(id=channel_id, name='Test', is_active=True))
    db_session.commit()
    # Separate connection owns a real write lock. Release it at retry backoff.
    engine = db_session.get_bind()
    with engine.connect() as holder:
        holder.execute(text('UPDATE acestream_channels SET name=name WHERE id=:id'), {'id': channel_id})
        db_session.execute(text('PRAGMA busy_timeout=1'))
        retries = []
        def release(_):
            retries.append(True)
            holder.rollback()
        monkeypatch.setattr(database_retry.time, 'sleep', release)
        ChannelRepository(db_session).update_channel_status(channel_id, False)
    assert len(retries) == 1
    assert db_session.get(AcestreamChannel, channel_id).is_online is False


def test_non_lock_failure_is_not_retried_and_rolls_back(db_session, monkeypatch):
    from app.repositories.channel_repository import ChannelRepository
    calls = []
    def fail(*args):
        calls.append(1)
        raise OperationalError('query', {}, sqlite3.OperationalError('no such table'))
    repository = ChannelRepository(db_session)
    monkeypatch.setattr(repository, 'get_channel_by_id', fail)
    with pytest.raises(OperationalError):
        repository.update_channel_status('a' * 40, False)
    assert len(calls) == 1
    assert db_session.execute(text('SELECT 1')).scalar() == 1


def test_scan_counts_outcomes_and_continues_after_failed_flush(alembic_db_session, monkeypatch):
    from app.tasks import channel_status_task as task
    from app.models.models import AcestreamChannel
    from app.repositories.settings_repository import SettingsRepository
    db = alembic_db_session
    SettingsRepository(db).set_setting('ace_engine_url', 'http://engine.test:6878')
    for i in range(4):
        db.add(AcestreamChannel(id=f'{i:040x}', name=f'Stream {i}', is_active=True))
    db.commit()
    monkeypatch.setattr(task, 'SessionLocal', lambda: db)
    monkeypatch.setattr(task.task_service, 'shutdown_event', Event())
    calls = []
    async def check(self, channel, **kwargs):
        i = len(calls)
        calls.append(channel.id)
        if i == 0:
            db.add(AcestreamChannel(id=channel.id, name="Duplicate"))  # Real flush failure.
            db.flush()
        if i == 1:
            return {'status': 'online', 'is_online': True}
        if i == 2:
            return {'status': 'offline', 'is_online': False}
        return {'status': 'skipped', 'is_online': False}
    monkeypatch.setattr(task.ChannelStatusService, 'check_channel_status', check)
    assert task.run_channel_status_task() == {'checked': 2, 'online': 1, 'offline': 1, 'skipped': 1, 'failed': 1}
    assert len(calls) == 4


def test_repeat_epg_parse_does_not_hold_writer_lock(alembic_db_session, monkeypatch):
    from app.models.models import EPGSource, EPGChannel
    from app.services.epg_service import EPGService
    db = alembic_db_session
    source = EPGSource(name='Test', url='https://example.test/epg.xml', enabled=True)
    db.add(source)
    db.commit()
    source_id = source.id
    db.add(EPGChannel(epg_source_id=source_id, channel_xml_id='test', name='Test'))
    db.commit()
    service = EPGService(db)
    parse = service._parse_xmltv_time
    observed = []
    def parse_while_another_writer_runs(value):
        with db.get_bind().begin() as connection:
            connection.execute(text('PRAGMA busy_timeout=1'))
            connection.execute(text('UPDATE epg_sources SET name=name WHERE id=:id'), {'id': source_id})
            observed.append(True)
        return parse(value)
    monkeypatch.setattr(service, '_parse_xmltv_time', parse_while_another_writer_runs)
    service._process_epg_xml(source_id, b'<tv><channel id="test"><display-name>Updated</display-name></channel><programme channel="test" start="20260910080000 +0000" stop="20260910090000 +0000"><title>News</title></programme></tv>')
    assert len(observed) == 2


@pytest.mark.asyncio
async def test_cancelling_database_await_keeps_session_owned_until_worker_finishes():
    import asyncio
    from app.config.database_retry import run_database_write
    entered = Event()
    release = Event()
    closed = []
    def write():
        entered.set()
        assert release.wait(2)
        assert not closed
    async def caller():
        try:
            await run_database_write(write)
        finally:
            closed.append(True)
    operation = asyncio.create_task(caller())
    while not entered.is_set():
        await asyncio.sleep(.01)
    operation.cancel()
    await asyncio.sleep(.01)
    assert not closed
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await operation
    assert closed == [True]


def test_lock_retries_are_bounded(db_session, monkeypatch):
    from app.repositories.channel_repository import ChannelRepository
    from app.config import database_retry
    repository = ChannelRepository(db_session)
    attempts = []
    def fail(*args):
        attempts.append(True)
        raise OperationalError('query', {}, sqlite3.OperationalError('database is locked'))
    monkeypatch.setattr(repository, 'get_channel_by_id', fail)
    monkeypatch.setattr(database_retry.time, 'sleep', lambda _: None)
    with pytest.raises(OperationalError):
        repository.update_channel_status('a' * 40, False)
    assert len(attempts) == 3
    assert db_session.is_active
