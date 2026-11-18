"""What checks and viewings say about one source (no lists involved)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.source_health import apply_check, apply_worked, discarded, due_for_check, is_real_check

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


class Source:
    def __init__(self, failed_checks=0, last_worked_at=None, failing_since=None):
        self.failed_checks = failed_checks
        self.last_worked_at = last_worked_at
        self.failing_since = failing_since


@pytest.mark.parametrize('online, network_status, http, real', [
    (False, None, True, True),            # an HTTP check always says something
    (True, 'unknown', False, True),       # media found
    (False, 'not_found', False, True),    # the engine looked it up
    (False, 'found', False, True),        # found, but no media came
    (False, 'unknown', False, False),     # a timeout or an engine outage
    (False, None, False, False),
])
def test_only_checks_that_reached_the_source_count(online, network_status, http, real):
    assert is_real_check(online, network_status, http=http) is real


def test_failed_checks_add_up_and_one_with_media_resets_them():
    source = Source()
    for minute in range(3):
        apply_check(source, False, NOW + timedelta(minutes=minute))
    assert (source.failed_checks, source.failing_since) == (3, NOW)
    apply_check(source, True, NOW + timedelta(hours=1))
    assert (source.failed_checks, source.failing_since, source.last_worked_at) == (0, None, NOW + timedelta(hours=1))


def test_an_older_viewing_does_not_move_last_worked_back():
    source = Source(failed_checks=5, last_worked_at=NOW, failing_since=NOW)
    apply_worked(source, NOW - timedelta(days=2))
    assert (source.failed_checks, source.failing_since, source.last_worked_at) == (0, None, NOW)


def test_a_discarded_source_is_rechecked_once_a_week():
    gone = Source(failed_checks=5, failing_since=NOW - timedelta(days=30))
    assert discarded(gone, NOW)
    assert not due_for_check(gone, NOW - timedelta(days=6), NOW)
    assert due_for_check(gone, NOW - timedelta(days=7), NOW)
    assert due_for_check(gone, None, NOW)
    assert due_for_check(gone, NOW + timedelta(days=40), NOW)       # a clock that ran ahead
    assert due_for_check(Source(), NOW - timedelta(minutes=1), NOW)


def _channel_with(db, name, stream_id, *, online, stream_url=None):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name=name, is_active=True)
    db.add(tv)
    db.flush()
    db.add(AcestreamChannel(id=stream_id, name=name, tv_channel_id=tv.id, is_active=True, is_online=online,
                            stream_url=stream_url, source_url='https://lists.example.test/a.m3u'))
    return tv


def test_only_online_keeps_the_same_channels_in_the_m3u_and_the_tuner(db_session):
    """Before, the M3U kept an HTTP stream not checked yet and the tuner left it out."""
    import asyncio

    from app.services.playlist_service import PlaylistService
    from app.services.tuner_service import TunerService
    _channel_with(db_session, 'Example Online', 'a' * 40, online=True)
    _channel_with(db_session, 'Example Unchecked HTTP', 'url:' + 'b' * 40, online=None,
                  stream_url='https://cdn.example.test/live/master.m3u8')
    _channel_with(db_session, 'Example Unchecked ID', 'c' * 40, online=None)
    _channel_with(db_session, 'Example Dead HTTP', 'url:' + 'd' * 40, online=False,
                  stream_url='https://cdn.example.test/dead/master.m3u8')
    db_session.commit()
    tuner = TunerService(db_session)
    tuner.update_settings(only_online=True)
    lineup = {entry.guide_name for entry in tuner.build_lineup().entries}
    body = asyncio.run(PlaylistService(db_session).generate_playlist(
        only_online=True, base_url='http://tuner.example/tuner/channel/{tv_channel_id}.ts'))
    m3u = {name for name in ('Example Online', 'Example Unchecked HTTP', 'Example Unchecked ID', 'Example Dead HTTP')
           if name in body}
    assert lineup == m3u == {'Example Online', 'Example Unchecked HTTP'}


def test_the_relay_order_is_a_pure_function_of_streams_history_and_now():
    """No database: the same rows give the same order."""
    from types import SimpleNamespace

    from app.services.stream_ranking import relay_order

    def row(key, online, hours_ago, order=None, bitrate=0):
        return SimpleNamespace(id=key * 40, is_online=online, stream_order=order, bitrate_bps=bitrate,
                               last_checked=None if hours_ago is None else NOW - timedelta(hours=hours_ago))
    streams = [row('a', True, 30), row('b', True, 1), row('c', None, None), row('d', False, 1),
               row('e', False, 30), row('f', True, 1, bitrate=9000), row('g', None, None, order=0)]
    history = {'c' * 40: SimpleNamespace(score=0.9, demoted=False),
               'f' * 40: SimpleNamespace(score=0.1, demoted=True)}
    assert relay_order(streams, history, NOW) == [k * 40 for k in 'gbacef']


def test_a_recent_viewing_outweighs_a_recent_offline_check_in_the_relay_order():
    """A check that finds no media right after the relay let the source go
    must not keep the source that just played out of the relay for hours: it
    is tried after the online ones. Without a viewing in the window, or with
    one dated in the future, a recent offline check still leaves it out."""
    from types import SimpleNamespace

    from app.services.stream_ranking import relay_order

    def row(key, online, checked_hours_ago, worked_hours_ago=None):
        return SimpleNamespace(id=key * 40, is_online=online, stream_order=None, bitrate_bps=0,
                               last_checked=NOW - timedelta(hours=checked_hours_ago),
                               last_worked_at=None if worked_hours_ago is None else NOW - timedelta(hours=worked_hours_ago))
    streams = [row('a', False, 1, worked_hours_ago=1.01),   # played, then a check said offline
               row('b', True, 1),
               row('c', False, 1, worked_hours_ago=30),     # played long ago
               row('d', False, 1),                          # never played
               row('e', False, 1, worked_hours_ago=-2)]     # clock ran ahead
    assert relay_order(streams, {}, NOW) == ['b' * 40, 'a' * 40]
