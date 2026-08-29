"""Periodic purge of EPG programs that already ended (EPG_PROGRAM_RETENTION_HOURS)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.models import EPGChannel, EPGProgram, EPGSource
from app.services.epg_service import EPGService


# Seeded relative to the real clock so the task (which uses datetime.now) and the
# explicit ``now=NOW`` calls agree; every boundary is >= 30 min away from a cutoff.
NOW = datetime.now(timezone.utc).replace(microsecond=0)


def _program(channel_id: int, title: str, start: datetime, end: datetime) -> EPGProgram:
    return EPGProgram(epg_channel_id=channel_id, title=title, start_time=start, end_time=end)


@pytest.fixture
def seeded_programs(db_session):
    source = EPGSource(url="http://example.com/epg.xml", name="Main")
    db_session.add(source)
    db_session.flush()
    channel = EPGChannel(epg_source_id=source.id, channel_xml_id="ch1", name="Channel 1")
    db_session.add(channel)
    db_session.flush()
    db_session.add_all([
        _program(channel.id, "ended two days ago", NOW - timedelta(days=2, hours=1), NOW - timedelta(days=2)),
        _program(channel.id, "ended 25h ago", NOW - timedelta(hours=26), NOW - timedelta(hours=25)),
        _program(channel.id, "ended 1h ago", NOW - timedelta(hours=2), NOW - timedelta(hours=1)),
        _program(channel.id, "on air", NOW - timedelta(minutes=30), NOW + timedelta(minutes=30)),
        _program(channel.id, "tonight", NOW + timedelta(hours=8), NOW + timedelta(hours=9)),
    ])
    db_session.commit()
    return db_session


def _set_retention(monkeypatch, value: str):
    from app.config import settings as settings_module

    monkeypatch.setenv("EPG_PROGRAM_RETENTION_HOURS", value)
    settings_module.get_settings.cache_clear()


def _titles(session):
    return {row.title for row in session.query(EPGProgram).all()}


def test_purge_deletes_only_programs_past_retention(seeded_programs, monkeypatch):
    _set_retention(monkeypatch, "24")

    result = EPGService(seeded_programs).purge_expired_programs(now=NOW)

    assert result["deleted"] == 2
    assert result["disabled"] is False
    assert _titles(seeded_programs) == {"ended 1h ago", "on air", "tonight"}


def test_purge_with_short_retention_keeps_current_and_future_programs(seeded_programs, monkeypatch):
    _set_retention(monkeypatch, "0.5")

    result = EPGService(seeded_programs).purge_expired_programs(now=NOW)

    assert result["deleted"] == 3
    assert _titles(seeded_programs) == {"on air", "tonight"}


def test_purge_is_disabled_with_negative_retention(seeded_programs, monkeypatch):
    _set_retention(monkeypatch, "-1")

    result = EPGService(seeded_programs).purge_expired_programs(now=NOW)

    assert result == {"deleted": 0, "retention_hours": -1.0, "cutoff": None, "disabled": True}
    assert len(_titles(seeded_programs)) == 5


def test_cleanup_task_purges_and_closes_its_session(seeded_programs, monkeypatch):
    from app.tasks import epg_program_cleanup_task as task_module

    closed = {"count": 0}
    original_close = seeded_programs.close

    def tracking_close():
        closed["count"] += 1
        original_close()

    seeded_programs.close = tracking_close
    # The task opens SessionLocal() on the runtime engine; point it at the
    # per-test session (which lives on its own engine) instead.
    monkeypatch.setattr(task_module, "SessionLocal", lambda: seeded_programs)
    _set_retention(monkeypatch, "24")

    result = task_module.run_epg_program_cleanup_task()

    assert result["deleted"] == 2
    assert closed["count"] == 1
