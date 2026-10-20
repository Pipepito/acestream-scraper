"""Switched on for a match: the relay also tries sources with an old status.

A box that is only on now and then: when it is switched on, every status is
hours or days old, and the source live tonight may be the one a check last
week found offline. Only online sources were tried, so the channel failed
with a live source assigned to it. Now a recent online
source goes first, then an old online one, then never checked or offline
from an old check; a recent offline verdict still leaves a source out.
"""
from datetime import datetime, timedelta, timezone

from app.models.models import AcestreamChannel, TVChannel
from app.services.tuner_service import TunerService


def _stream(db, key, tv, *, online, hours_ago, bitrate=None):
    checked = None if hours_ago is None else datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    db.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id, is_online=online, is_active=True,
                            bitrate_bps=bitrate, last_checked=checked))


def _channel(db):
    tv = TVChannel(name='M+ LaLiga', is_active=True)
    db.add(tv)
    db.flush()
    return tv


def test_after_power_on_sources_with_an_old_status_are_tried_too(db_session):
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, online=False, hours_ago=70, bitrate=9_000_000)   # offline last week
    _stream(db_session, 'b', tv, online=True, hours_ago=70, bitrate=4_000_000)    # online last week
    _stream(db_session, 'c', tv, online=None, hours_ago=None, bitrate=20_000_000)  # never checked
    _stream(db_session, 'd', tv, online=True, hours_ago=1)                        # online just now
    db_session.commit()
    assert TunerService(db_session).relay_stream_ids(tv.id) == ['d' * 40, 'b' * 40, 'c' * 40, 'a' * 40]


def test_a_source_found_offline_recently_is_not_tried(db_session):
    """A recent check that found it offline is respected."""
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, online=False, hours_ago=0.2, bitrate=9_000_000)
    _stream(db_session, 'b', tv, online=None, hours_ago=None)
    db_session.commit()
    assert TunerService(db_session).relay_stream_ids(tv.id) == ['b' * 40]


def test_the_route_uses_this_order(db_session, monkeypatch):
    from app.api.endpoints import tuner
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, online=False, hours_ago=70)
    db_session.commit()
    monkeypatch.setattr(tuner, 'SessionLocal', lambda: db_session)
    monkeypatch.setattr(db_session, 'close', lambda: None)
    assert tuner._channel_candidates(tv.id) == ['a' * 40]
