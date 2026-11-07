"""The scheduled status pass waits while someone watches.

On 2026-10-14 the hourly pass started at 21:49, in the middle of a match,
and kept opening the engine next to the channel being watched until the box
was switched off at 22:58. It only skipped the source the relay was playing.
"""
import asyncio
import logging
from types import SimpleNamespace

import pytest

from app.services import viewing
from app.services.stream_relay import relay_registry
from app.tasks import channel_status_task


@pytest.fixture(autouse=True)
def _nobody_watching(monkeypatch):
    # A fresh shutdown flag: an earlier test that stops the app leaves the
    # process-wide one set, and then the pass stops before waiting at all.
    import threading
    from app.services.task_service import task_service
    monkeypatch.setattr(task_service, "shutdown_event", threading.Event())
    for info in relay_registry.active():
        relay_registry.close(info.id)
    yield
    for info in relay_registry.active():
        relay_registry.close(info.id)


def test_nobody_watching():
    assert viewing.watching() is None


def test_the_tv_relay_counts_while_its_claim_lasts():
    claim = relay_registry.try_open("", "tuner:192.168.1.20", 4)
    assert viewing.watching() == "tv relay"
    relay_registry.close(claim.id)
    assert viewing.watching() is None


def test_the_web_player_counts_only_while_starting_or_ready(monkeypatch):
    from app.services.player_service import player_service
    sessions = [SimpleNamespace(state="error"), SimpleNamespace(state="stopped")]
    monkeypatch.setattr(player_service, "list_sessions", lambda: sessions)
    assert viewing.watching() is None
    sessions.append(SimpleNamespace(state="ready"))
    assert viewing.watching() == "web player"


def _fast_sleep(monkeypatch):
    clock = {"t": 0.0}

    class Loop:
        def time(self):
            return clock["t"]

    async def sleep(seconds):
        clock["t"] += seconds

    monkeypatch.setattr(channel_status_task.asyncio, "get_running_loop", lambda: Loop())
    monkeypatch.setattr(channel_status_task.asyncio, "sleep", sleep)
    return clock


def test_it_waits_until_nobody_watches(monkeypatch):
    clock = _fast_sleep(monkeypatch)
    answers = iter(["tv relay", "tv relay", "tv relay", None])
    monkeypatch.setattr(viewing, "watching", lambda: next(answers))
    waited, gave_up = asyncio.run(channel_status_task.wait_while_watching(logging.getLogger("t"), 3600))
    assert not gave_up
    assert waited == 3 * channel_status_task.VIEWING_POLL_SECONDS == clock["t"]


def test_it_gives_up_after_the_limit_instead_of_hanging(monkeypatch):
    _fast_sleep(monkeypatch)
    monkeypatch.setattr(viewing, "watching", lambda: "tv relay")
    waited, gave_up = asyncio.run(channel_status_task.wait_while_watching(logging.getLogger("t"), 60))
    assert gave_up
    assert waited == 60


def test_the_pass_checks_nothing_while_someone_watches(db_session, monkeypatch):
    """The whole pass: with someone watching it opens no source."""
    from app.models.models import AcestreamChannel
    for cid in ("a", "b"):
        db_session.add(AcestreamChannel(id=cid, name=cid, is_active=True))
    db_session.commit()
    _fast_sleep(monkeypatch)
    probed = []

    class Service:
        def __init__(self, db):
            pass

        def _get_engine_url(self):
            return "http://engine.test:6878"

        async def check_channel_status(self, channel, **kwargs):
            probed.append(channel.id)
            return {"status": "checked", "is_online": True}

    monkeypatch.setattr(channel_status_task, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(channel_status_task, "ChannelStatusService", Service)
    monkeypatch.setattr(db_session, "close", lambda: None)
    monkeypatch.setattr(viewing, "watching", lambda: "tv relay")
    result = channel_status_task.run_channel_status_task()
    assert probed == []
    assert result["checked"] == 0

    monkeypatch.setattr(viewing, "watching", lambda: None)
    result = channel_status_task.run_channel_status_task()
    assert sorted(probed) == ["a", "b"]
    assert result["checked"] == 2


def test_remaining_pause_budget_is_not_rounded_up_to_poll_interval(monkeypatch):
    _fast_sleep(monkeypatch)
    monkeypatch.setattr(viewing, "watching", lambda: "tv relay")
    waited, gave_up = asyncio.run(channel_status_task.wait_while_watching(logging.getLogger("t"), 1.5))
    assert gave_up
    assert waited == 1.5


def _prepare_counted_pass(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.task_service import TaskService
    service = TaskService()
    monkeypatch.setattr(channel_status_task, "task_service", service)
    for cid in ("a", "b", "c"):
        db_session.add(AcestreamChannel(id=cid, name=cid, is_active=True))
    db_session.commit()
    probed = []
    notified = []

    class Checker:
        def __init__(self, db):
            pass

        def _get_engine_url(self):
            return "http://checker.test:6880"

        async def check_channel_status(self, channel, **kwargs):
            probed.append(channel.id)
            return {"status": "checked", "is_online": True}

    monkeypatch.setattr(channel_status_task, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)
    monkeypatch.setattr(channel_status_task, "ChannelStatusService", Checker)
    monkeypatch.setattr(channel_status_task.notification_service, "channel_status_completed", lambda result: notified.append(result.copy()))
    return service, probed, notified


def test_pause_budget_is_cumulative_and_remaining_work_is_reported(alembic_db_session, monkeypatch):
    from app.repositories.task_state_repository import TaskStateRepository
    from app.services.task_service import TaskService
    db_session = alembic_db_session
    service, probed, notified = _prepare_counted_pass(db_session, monkeypatch)
    service._state_store = TaskStateRepository()
    budgets = []
    async def wait(logger, remaining):
        assert not db_session.in_transaction(), "Waiting must not retain a SQLite transaction"
        budgets.append(remaining)
        return (200.0, False) if len(budgets) == 1 else (400.0, True)
    monkeypatch.setattr(channel_status_task, "wait_while_watching", wait)
    result = service._instrument_task("channel_status", channel_status_task.run_channel_status_task, maintenance=True)()
    assert budgets == [600.0, 400.0]
    assert probed == ["a"]
    assert result["checked"] == 1
    assert result["deferred"] == 2
    assert result["stop_reason"] == "viewing"
    assert service.get_task_state("channel_status")["last_result"] == result
    assert notified == [result]
    restored = TaskService(state_store=TaskStateRepository())
    restored.restore_states()
    assert restored.get_task_state("channel_status")["last_result"] == result


def test_shutdown_during_pause_stops_before_probe(db_session, monkeypatch):
    service, probed, notified = _prepare_counted_pass(db_session, monkeypatch)
    async def wait(logger, remaining):
        service.shutdown_event.set()
        return 1.0, False
    monkeypatch.setattr(channel_status_task, "wait_while_watching", wait)
    result = channel_status_task.run_channel_status_task()
    assert probed == []
    assert result["deferred"] == 3
    assert result["stop_reason"] == "shutdown"


def test_expired_viewing_pause_releases_fifo_to_next_job(db_session, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    service, probed, _ = _prepare_counted_pass(db_session, monkeypatch)
    entered = Event()
    release = Event()
    next_ran = Event()
    async def wait(logger, remaining):
        entered.set()
        assert release.wait(3)
        return remaining, True
    monkeypatch.setattr(channel_status_task, "wait_while_watching", wait)
    with ThreadPoolExecutor(2) as pool:
        scan = pool.submit(service._instrument_task("channel_status", channel_status_task.run_channel_status_task, maintenance=True))
        assert entered.wait(3)
        next_job = pool.submit(service._instrument_task("epg_refresh", next_ran.set, maintenance=True))
        try:
            assert not next_ran.wait(0.05)
        finally:
            release.set()
        assert scan.result(3)["deferred"] == 3
        next_job.result(3)
    assert next_ran.is_set()
    assert probed == []
