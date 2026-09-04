"""Background tasks the FastAPI lifespan owns (see ``main.lifespan``).

The relay reaper runs for the whole process lifetime, so its failure mode
matters more than its happy path: if one sweep raises, the task must keep
sweeping instead of dying silently and leaking finished relay records.
"""
import asyncio
from contextlib import asynccontextmanager

import pytest

import main


@asynccontextmanager
async def _lifespan_without_io(monkeypatch, registered=None, intervals=(24, 6)):
    """Run the real ``main.lifespan`` with its heavy startup work stubbed out.

    Only the database provisioning, the APScheduler wiring and the player
    service are replaced; the relay reaper is left exactly as production
    creates it. Pass ``registered`` to collect the ``(job_id, seconds, func)``
    of every interval job the lifespan hands the scheduler, and ``intervals``
    to stand in for the ``(rescrape_hours, epg_refresh_hours)`` settings.
    """
    async def _noop_async():
        return None

    def record_interval_task(func, seconds, job_id, args=None, kwargs=None):
        if registered is not None:
            registered.append((job_id, seconds, func))

    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(main, "_configured_intervals", lambda: intervals)
    monkeypatch.setattr(main, "_schedule_deferred_migration", lambda: False)
    monkeypatch.setattr(main.task_service, "start", lambda: None)
    monkeypatch.setattr(main.task_service, "add_interval_task", record_interval_task)
    monkeypatch.setattr(main.task_service, "shutdown", lambda: None)
    monkeypatch.setattr(main.player_service, "start", _noop_async)
    monkeypatch.setattr(main.player_service, "stop", _noop_async)

    # A regression that leaves the reaper running (or awaits a dead one) would
    # hang the suite rather than fail it, so bound the whole lifespan.
    async with asyncio.timeout(10):
        async with main.lifespan(main.app):
            yield


@pytest.mark.asyncio
async def test_relay_reaper_keeps_sweeping_after_a_failing_sweep(monkeypatch):
    sweeps = []

    def exploding_sweep(**kwargs):
        sweeps.append(kwargs)
        raise RuntimeError("registry sweep failed")

    monkeypatch.setattr(main, "RELAY_REAP_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(main.relay_registry, "reap_finished", exploding_sweep)

    async with _lifespan_without_io(monkeypatch):
        for _ in range(500):
            if len(sweeps) >= 3:
                break
            await asyncio.sleep(0)

    assert len(sweeps) >= 3, f"the reaper stopped after {len(sweeps)} sweep(s)"
    assert sweeps[0] == {"older_than_seconds": main.RELAY_REAP_AGE_SECONDS}


@pytest.mark.asyncio
async def test_a_failing_player_start_still_stops_the_scheduler(monkeypatch):
    """The player is optional; starting it belongs inside the lifespan's
    ``try``/``finally`` so an unreadable ``PLAYER_HLS_DIR`` cannot leave
    APScheduler (started just before it) running for the life of the process.
    """
    shutdowns = []

    async def _noop_async():
        return None

    async def refuse_to_start():
        raise PermissionError(13, "Permission denied: /tmp/acestream-player")

    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(main, "_configured_intervals", lambda: (24, 6))
    monkeypatch.setattr(main, "_schedule_deferred_migration", lambda: False)
    monkeypatch.setattr(main.task_service, "start", lambda: None)
    monkeypatch.setattr(main.task_service, "add_interval_task", lambda *a, **k: None)
    monkeypatch.setattr(main.task_service, "shutdown", lambda: shutdowns.append(True))
    monkeypatch.setattr(main.player_service, "start", refuse_to_start)
    monkeypatch.setattr(main.player_service, "stop", _noop_async)

    with pytest.raises(PermissionError):
        async with asyncio.timeout(10):
            async with main.lifespan(main.app):
                pass

    assert shutdowns == [True], "the scheduler kept running after the player failed to start"


@pytest.mark.asyncio
async def test_lifespan_registers_the_documented_interval_jobs(monkeypatch):
    """The scheduler's job table is what CLAUDE.md and the wiki describe, so
    assert on the jobs the lifespan actually registers rather than on the
    source line that registers them.

    ``_configured_intervals`` is stubbed with the settings defaults (24h
    between rescrapes, 6h between EPG refreshes), so the two settings-driven
    periods are visible here as periods, not as constants.
    """
    registered = []

    async with _lifespan_without_io(monkeypatch, registered):
        pass

    assert registered == [
        ("activity_log_cleanup", 86400, main.run_activity_log_cleanup),
        ("epg_refresh", 6 * 3600, main.run_epg_refresh_task),
        ("epg_program_cleanup", 3600, main.run_epg_program_cleanup_task),
        ("url_scraping", 24 * 3600, main.run_url_scraping_task),
        ("channel_cleanup", 86400, main.run_channel_cleanup_task),
        ("channel_status", 600, main.run_channel_status_task),
        ("media_server_sync", 600, main.run_media_server_sync_task),
    ]


@pytest.mark.asyncio
async def test_the_settings_driven_jobs_follow_the_configured_intervals(monkeypatch):
    """A user who sets 2h rescrapes and 12h EPG refreshes gets those periods:
    the two jobs read their interval from settings, they are not fixed.
    """
    registered = []

    async with _lifespan_without_io(monkeypatch, registered, intervals=(2, 12)):
        pass

    periods = {job_id: seconds for job_id, seconds, _ in registered}
    assert periods["url_scraping"] == 2 * 3600
    assert periods["epg_refresh"] == 12 * 3600
