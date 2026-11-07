"""The relay tries recently checked sources first.

On a box that is only on now and then "online" may come from a session hours or
days ago, and the first source tried eats 20 of the 30 s Kodi gives an
opening. Sorting only by bitrate tried a stale high-bitrate source first.
"""
from datetime import datetime, timedelta, timezone

from app.models.models import AcestreamChannel, TVChannel
from app.services import tuner_service
from app.services.tuner_service import TunerService


def _stream(db, key, tv, bitrate, hours_ago):
    checked = None if hours_ago is None else datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    db.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id, is_online=True, is_active=True,
                            bitrate_bps=bitrate, last_checked=checked))


def test_a_recent_online_source_goes_before_an_older_higher_bitrate_one(db_session):
    tv = TVChannel(name='DAZN LaLiga', is_active=True)
    db_session.add(tv)
    db_session.flush()
    _stream(db_session, 'a', tv, 16_000_000, hours_ago=30)   # yesterday's session
    _stream(db_session, 'b', tv, 8_000_000, hours_ago=0.5)   # checked just now
    _stream(db_session, 'c', tv, 12_000_000, hours_ago=2)
    _stream(db_session, 'd', tv, 32_000_000, hours_ago=None)  # online, never dated
    db_session.commit()
    # Fresh ones by bitrate, then the stale and the undated ones by bitrate.
    assert TunerService(db_session).online_stream_ids(tv.id) == ['c' * 40, 'b' * 40, 'd' * 40, 'a' * 40]


def test_without_dates_the_order_is_unchanged(db_session):
    tv = TVChannel(name='F1', is_active=True)
    db_session.add(tv)
    db_session.flush()
    for key, bitrate in (('a', 8_000_000), ('b', 16_000_000), ('f', None)):
        _stream(db_session, key, tv, bitrate, hours_ago=1)
    db_session.commit()
    assert TunerService(db_session).online_stream_ids(tv.id) == ['b' * 40, 'a' * 40, 'f' * 40]


def test_the_limit_is_6_hours():
    assert tuner_service.FRESH_CHECK_HOURS == 6
