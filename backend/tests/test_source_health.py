"""What checks and viewings say about one source (no lists involved)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.source_health import apply_worked, discarded, due_for_check, is_real_check, record_check

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


class Source:
    def __init__(self, failed_checks=0, last_worked_at=None, failing_since=None,
                 is_online=False, network_status='not_found', stream_url=None):
        self.is_online, self.network_status, self.stream_url = is_online, network_status, stream_url
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
        record_check(source, False, 'not_found', NOW + timedelta(minutes=minute))
    assert (source.failed_checks, source.failing_since) == (3, NOW)
    record_check(source, True, 'found', NOW + timedelta(hours=1))
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


# --- one writer of facts ------------------------------------------------------

@pytest.mark.parametrize('online, network_status, http, counted', [
    (False, 'unknown', False, False),     # a timeout says nothing
    (False, 'not_found', False, True),
    (False, 'unknown', True, True),       # an HTTP check always counts
])
def test_record_check_decides_by_itself_whether_the_check_was_real(online, network_status, http, counted):
    from app.services.source_health import record_check
    source = Source()
    assert record_check(source, online, network_status, NOW, http=http) is counted
    assert source.failed_checks == (1 if counted else 0)
    assert (source.failing_since is not None) is counted


def test_record_check_with_media_marks_the_source_as_working():
    from app.services.source_health import record_check
    source = Source(failed_checks=4, failing_since=NOW - timedelta(days=3))
    assert record_check(source, True, 'unknown', NOW) is True
    assert (source.failed_checks, source.failing_since, source.last_worked_at) == (0, None, NOW)


# --- removal (the cleanup asks the same module) ---------------------------------

OFFLINE_DAYS = 14


def _gone(days_failing, failed=5, worked_days_ago=None, **last_check):
    return Source(failed_checks=failed, failing_since=NOW - timedelta(days=days_failing),
                  last_worked_at=None if worked_days_ago is None else NOW - timedelta(days=worked_days_ago),
                  **last_check)


@pytest.mark.parametrize('source, removable_now', [
    (_gone(14), True),                           # exactly offline_days
    (_gone(13, ), False),                        # discarded but the streak is too young
    (_gone(30, failed=4), False),                # not enough failed checks
    (_gone(30, worked_days_ago=3), False),       # worked within the discard window
    (_gone(30, worked_days_ago=8), True),
    (Source(failed_checks=5), False),            # no streak start: unknown age
    (_gone(30, network_status='unknown'), False),    # the last check was a timeout: says nothing
    (_gone(30, network_status='found'), True),
    (_gone(30, network_status='unknown', stream_url='https://example.com/a.m3u8'), True),   # HTTP always counts
])
def test_removable_is_discarded_with_a_streak_of_offline_days(source, removable_now):
    from app.services.source_health import removable
    assert removable(source, NOW, OFFLINE_DAYS) is removable_now


def test_removable_python_and_sql_say_the_same(db_session):
    from app.models.models import AcestreamChannel
    from app.services.source_health import removable, removable_clause
    cases = [(_gone(14), 1), (_gone(13), 2), (_gone(30, failed=4), 3), (_gone(30, worked_days_ago=3), 4),
             (_gone(30, worked_days_ago=8), 5), (Source(failed_checks=5), 6),
             (Source(failed_checks=9, failing_since=NOW + timedelta(days=30)), 7),
             (Source(failed_checks=9, failing_since=NOW - timedelta(days=40),
                     last_worked_at=NOW + timedelta(days=30)), 8),
             (_gone(30, network_status='unknown'), 9),
             (_gone(30, network_status=None), 'a'),
             (_gone(30, network_status='unknown', stream_url='https://example.com/a.m3u8'), 'b')]
    for source, n in cases:
        db_session.add(AcestreamChannel(id=str(n) * 40, name=str(n), failed_checks=source.failed_checks,
                                        failing_since=source.failing_since, last_worked_at=source.last_worked_at,
                                        is_online=source.is_online, network_status=source.network_status,
                                        stream_url=source.stream_url))
    db_session.commit()
    sql = {row.id for row in db_session.query(AcestreamChannel).filter(removable_clause(NOW, OFFLINE_DAYS))}
    python = {row.id for row in db_session.query(AcestreamChannel).all() if removable(row, NOW, OFFLINE_DAYS)}
    assert sql == python == {'1' * 40, '5' * 40, 'b' * 40}


def test_the_relay_puts_discarded_sources_after_the_degraded_ones():
    from types import SimpleNamespace

    from app.services.stream_ranking import relay_order

    def row(key, **extra):
        values = dict(id=key * 40, is_online=None, stream_order=None, bitrate_bps=0, last_checked=None,
                      failed_checks=0, failing_since=None, last_worked_at=None)
        return SimpleNamespace(**{**values, **extra})
    gone = row('a', failed_checks=5, failing_since=NOW - timedelta(days=30), bitrate_bps=99_000_000)
    degraded = row('b')
    fine = row('c')
    history = {'b' * 40: SimpleNamespace(score=0.1, demoted=True)}
    assert relay_order([gone, degraded, fine], history, NOW) == ['c' * 40, 'b' * 40, 'a' * 40]


def test_a_discarded_source_that_is_also_demoted_stays_last_and_is_not_dropped():
    from types import SimpleNamespace

    from app.services.stream_ranking import relay_order
    gone = SimpleNamespace(id='a' * 40, is_online=None, stream_order=None, bitrate_bps=0, last_checked=None,
                           failed_checks=5, failing_since=NOW - timedelta(days=30), last_worked_at=None)
    assert relay_order([gone], {'a' * 40: SimpleNamespace(score=0.0, demoted=True)}, NOW) == ['a' * 40]


def test_a_check_dated_in_the_future_never_counts_as_fresh_for_the_relay():
    """The relay's freshness window has no clock tolerance: an offline check 3 minutes ahead is not
    "recent", so the source is still tried."""
    from types import SimpleNamespace

    from app.services.stream_ranking import relay_order
    ahead = SimpleNamespace(id='a' * 40, is_online=False, stream_order=None, bitrate_bps=0,
                            last_checked=NOW + timedelta(minutes=3), failed_checks=0, failing_since=None,
                            last_worked_at=None)
    assert relay_order([ahead], {}, NOW) == ['a' * 40]


# --- viewings ------------------------------------------------------------------

@pytest.mark.parametrize('outcome, seconds, worked, failed', [
    ('ok', 120, True, 0),
    ('ok', 119.9, False, 5),
    ('ended', 120, True, 1),
    ('stall', 600, True, 1),
    ('ended', 30, False, 5),
    ('jumpy', 3600, False, 5),
    ('handover', 3600, False, 5),
    ('no_data', 600, False, 5),
    ('ok', None, False, 5),
])
def test_a_viewing_of_two_minutes_counts_and_a_cut_source_counts_as_one_failure(outcome, seconds, worked, failed):
    from app.services.source_health import record_viewing
    source = Source(failed_checks=5, failing_since=NOW - timedelta(days=30))
    at = NOW + timedelta(hours=1)
    assert record_viewing(source, outcome, seconds, at) is worked
    assert (source.last_worked_at == at) is worked
    assert source.failed_checks == failed
    assert source.failing_since == (at if failed == 1 else None if failed == 0 else NOW - timedelta(days=30))


def test_a_viewing_that_worked_and_was_cut_is_not_discarded():
    from app.services.source_health import record_viewing
    source = Source(failed_checks=9, failing_since=NOW - timedelta(days=30))
    record_viewing(source, 'stall', 300, NOW)
    assert not discarded(source, NOW + timedelta(days=30))


def test_only_the_final_record_of_a_viewing_adds_the_failure():
    from app.services.source_health import record_viewing
    source = Source(failed_checks=0)
    for seconds in (30, 60, 120):
        record_viewing(source, 'ok', seconds, NOW, final=False)
    assert (source.failed_checks, source.last_worked_at) == (0, NOW)
    record_viewing(source, 'ended', 300, NOW, final=False)      # never sent today, but it must not count
    assert source.failed_checks == 0
    record_viewing(source, 'stall', 150, NOW, final=True)
    assert (source.failed_checks, source.failing_since) == (1, NOW)
