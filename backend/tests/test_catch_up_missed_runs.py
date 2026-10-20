"""Jobs missed while the machine was off run at startup.

Interval jobs are re-created in memory on every start, so their first run
lands one whole interval after startup. On a box that is only switched on for
a few hours, `epg_refresh` (6 h) had never run while `epg_program_cleanup`
(1 h) kept deleting expired programmes: the guide emptied itself. One manual
refresh on a test bench took it from 12 programmes for the day to 26,259.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.config import ScheduleAnchors
from app.services.task_service import TaskService

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
H = 3600


def _noop():
    return None


@pytest.fixture
def service():
    s = TaskService()
    s.scheduler.start(paused=True)          # nothing actually runs
    yield s
    s.scheduler.shutdown(wait=False)


def _register(s, job_id, seconds, last_run):
    s.add_interval_task(_noop, seconds=seconds, job_id=job_id)
    with s._state_lock:
        s._task_states[job_id]["last_run"] = last_run


def _next_run(s, job_id):
    return s.scheduler.get_job(job_id).next_run_time


def test_a_guide_refresh_that_never_ran_is_brought_forward(service):
    """The case seen on a box: epg_refresh had never run."""
    _register(service, "epg_refresh", 6 * H, None)
    assert service.catch_up_missed_runs(now=NOW) == ["epg_refresh"]
    assert _next_run(service, "epg_refresh") == NOW


def test_an_overdue_job_is_brought_forward(service):
    _register(service, "epg_refresh", 6 * H, NOW - timedelta(hours=9))
    assert service.catch_up_missed_runs(now=NOW) == ["epg_refresh"]


def test_a_recent_run_is_left_alone(service):
    """Run an hour ago: the guide is not downloaded again at startup."""
    _register(service, "epg_refresh", 6 * H, NOW - timedelta(hours=1))
    before = _next_run(service, "epg_refresh")
    assert service.catch_up_missed_runs(now=NOW) == []
    assert _next_run(service, "epg_refresh") == before


def test_the_job_that_empties_the_guide_is_never_brought_forward(service):
    """Running epg_program_cleanup early would worsen what this fixes."""
    _register(service, "epg_program_cleanup", H, None)
    assert service.catch_up_missed_runs(now=NOW) == []


def test_the_job_that_opens_engine_sessions_is_not_either(service):
    """channel_status chokes a small box that is still loading its catalogue."""
    _register(service, "channel_status", 60 * 60, None)
    assert service.catch_up_missed_runs(now=NOW) == []


def test_staggered_guide_first_then_playlists(service):
    _register(service, "url_scraping", 24 * H, None)
    _register(service, "epg_refresh", 6 * H, None)
    assert service.catch_up_missed_runs(now=NOW) == ["epg_refresh", "url_scraping"]
    assert _next_run(service, "epg_refresh") == NOW
    assert _next_run(service, "url_scraping") == NOW + timedelta(seconds=300)


def test_a_user_set_start_time_is_left_alone(service):
    """Whoever asked for 04:00 wants 04:00."""
    service.configure_schedule(ScheduleAnchors(epg_refresh="04:00"))
    _register(service, "epg_refresh", 6 * H, None)
    assert service.catch_up_missed_runs(now=NOW) == []


def test_last_run_stored_as_text_also_works(service):
    """In case the state store returns it serialized."""
    _register(service, "epg_refresh", 6 * H, (NOW - timedelta(hours=1)).isoformat())
    assert service.catch_up_missed_runs(now=NOW) == []


# --- channel_status: looked at again 15 minutes after startup ---------------
# On a machine that is only on now and then, the first pass came 60 minutes
# after startup and every restart pushed it back again. Not at startup, which
# opens the engine while the catalogue loads and a channel is opened: 15 min.

def test_channel_status_is_looked_at_after_15_minutes(service):
    _register(service, "channel_status", H, None)
    assert service.catch_up_later("channel_status", delay_seconds=900, now=NOW)
    assert _next_run(service, "channel_status_catch_up") == NOW + timedelta(seconds=900)


def test_still_overdue_after_15_minutes_it_runs(service, monkeypatch):
    _register(service, "channel_status", H, NOW - timedelta(hours=14))
    triggered = []
    monkeypatch.setattr(service, "run_task_now", lambda job_id: triggered.append(job_id) or "triggered")
    assert service.run_if_overdue("channel_status", now=NOW) == "triggered"
    assert triggered == ["channel_status"]


def test_a_pass_run_since_startup_is_not_repeated(service, monkeypatch):
    """The decision is taken when it fires: a pass run by hand, or a quick
    restart, makes it unnecessary."""
    _register(service, "channel_status", H, NOW - timedelta(minutes=10))
    triggered = []
    monkeypatch.setattr(service, "run_task_now", lambda job_id: triggered.append(job_id) or "triggered")
    assert service.run_if_overdue("channel_status", now=NOW) == "not_needed"
    assert triggered == []


def test_a_user_set_start_time_is_not_scheduled_either(service):
    service.configure_schedule(ScheduleAnchors(channel_status="04:00"))
    _register(service, "channel_status", H, None)
    assert not service.catch_up_later("channel_status", delay_seconds=900, now=NOW)


def test_at_power_on_the_guide_waits_as_asked(service):
    """Right after power-on is when channels are opened, and the guide
    refresh holds the SQLite write lock: the first catch-up waits."""
    _register(service, "url_scraping", 24 * H, None)
    _register(service, "epg_refresh", 6 * H, None)
    assert service.catch_up_missed_runs(now=NOW, start_after_seconds=300) == ["epg_refresh", "url_scraping"]
    assert _next_run(service, "epg_refresh") == NOW + timedelta(seconds=300)
    assert _next_run(service, "url_scraping") == NOW + timedelta(seconds=600)
