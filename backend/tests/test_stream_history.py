"""Per-source playback history and how the tuner ranks with it.

A channel collects sources from several lists. Some lists stop being
maintained and their sources die, some sources are no longer published by any
list, and some source played for an hour yesterday while another never
started. The relay records how each attempt ended; within each freshness group
a source that played goes first, and a source that is clearly dead goes after
every group (it is never dropped, only tried last).
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, inspect

from app.models.models import AcestreamChannel, TVChannel
from app.models.stream_attempts import StreamAttempt
from app.services import tuner_playback_service
from app.services.stream_history import StreamHistoryRecorder, score_sources
from app.services.tuner_service import TunerService
from tests.migration_test_utils import database_url_for, downgrade_to_revision, upgrade_to_head, upgrade_to_revision

NOW = datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc)
LIST_A = 'https://lists.example.test/a.m3u'
LIST_B = 'https://lists.example.test/b.m3u'


class Row:
    def __init__(self, key, source_url=None, last_seen=NOW):
        self.id, self.source_url, self.last_seen = key * 40, source_url, last_seen


def attempt(key, outcome, days_ago=0.0, seconds=0.0):
    return (key * 40, outcome, seconds, NOW - timedelta(days=days_ago))


def test_a_source_that_played_ranks_above_one_that_never_started():
    scores = score_sources([Row('a'), Row('b')],
                           [attempt('a', 'ok', seconds=3600), attempt('b', 'no_data'), attempt('b', 'no_data')], {}, NOW)
    assert scores['a' * 40].score > 0.5 > scores['b' * 40].score


def test_old_attempts_count_less_than_recent_ones():
    recent = score_sources([Row('a')], [attempt('a', 'no_data', days_ago=1), attempt('a', 'ok', days_ago=30)], {}, NOW)
    old = score_sources([Row('a')], [attempt('a', 'no_data', days_ago=30), attempt('a', 'ok', days_ago=1)], {}, NOW)
    assert old['a' * 40].score > recent['a' * 40].score


def test_a_source_watched_longer_ranks_above_one_watched_briefly():
    scores = score_sources([Row('a'), Row('b')],
                           [attempt('a', 'ok', seconds=3600), attempt('a', 'stall', seconds=60),
                            attempt('b', 'ok', seconds=60), attempt('b', 'stall', seconds=60)], {}, NOW)
    assert scores['a' * 40].score > scores['b' * 40].score


@pytest.mark.parametrize('outcome', ['engine_unavailable', 'handover'])
def test_outcomes_that_say_nothing_about_the_source_are_ignored(outcome):
    scores = score_sources([Row('a')], [attempt('a', outcome)] * 5, {}, NOW)
    assert scores['a' * 40].evidence == 0.0 and scores['a' * 40].score == 0.5


def test_the_list_is_the_prior_for_a_source_without_history():
    health = {LIST_A: (20, 18), LIST_B: (20, 2)}
    scores = score_sources([Row('a', LIST_A), Row('b', LIST_B)], [], health, NOW)
    assert scores['a' * 40].score > scores['b' * 40].score
    assert scores['b' * 40].demoted and not scores['a' * 40].demoted


def test_a_mostly_dead_list_does_not_demote_a_source_that_plays():
    scores = score_sources([Row('a', LIST_B)], [attempt('a', 'ok', seconds=1800)], {LIST_B: (20, 2)}, NOW)
    assert not scores['a' * 40].demoted


def test_a_source_no_list_has_published_for_two_weeks_is_demoted():
    scores = score_sources([Row('a', last_seen=NOW - timedelta(days=60)), Row('b', last_seen=NOW - timedelta(days=3))],
                           [], {}, NOW)
    assert scores['a' * 40].demoted and not scores['b' * 40].demoted


def test_attempts_written_with_a_clock_ahead_are_ignored():
    future = [(('a' * 40), 'ok', 3600.0, NOW + timedelta(days=41))]
    scores = score_sources([Row('a')], future, {}, NOW)
    assert scores['a' * 40].evidence == 0.0 and scores['a' * 40].score == 0.5


def test_repeated_recent_failures_demote_a_source():
    scores = score_sources([Row('a')], [attempt('a', 'no_data', days_ago=d) for d in (0, 1, 2)], {}, NOW)
    assert scores['a' * 40].demoted


def _channel(db):
    tv = TVChannel(name='Example Sports', is_active=True)
    db.add(tv)
    db.flush()
    return tv


def _stream(db, key, tv, *, online=True, source_url=None, last_seen=None, order=None):
    db.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id, is_online=online, is_active=True,
                            last_checked=datetime.now(timezone.utc), source_url=source_url,
                            last_seen=last_seen or datetime.now(timezone.utc), stream_order=order))


def _attempts(db, key, outcome, count, seconds=0.0):
    for _ in range(count):
        db.add(StreamAttempt(content_id=key * 40, outcome=outcome, seconds=seconds,
                             created_at=datetime.now(timezone.utc)))


def test_the_relay_tries_the_source_that_played_first(db_session):
    tv = _channel(db_session)
    _stream(db_session, 'a', tv)
    _stream(db_session, 'b', tv)
    _attempts(db_session, 'a', 'no_data', 1)
    _attempts(db_session, 'b', 'ok', 1, seconds=2400)
    db_session.commit()
    assert TunerService(db_session).relay_stream_ids(tv.id) == ['b' * 40, 'a' * 40]


def test_a_demoted_source_goes_after_every_other_group_but_stays(db_session):
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, online=True, last_seen=datetime.now(timezone.utc) - timedelta(days=60))
    _stream(db_session, 'b', tv, online=None)
    db_session.commit()
    assert TunerService(db_session).relay_stream_ids(tv.id) == ['b' * 40, 'a' * 40]


def test_a_saved_preference_still_comes_first(db_session):
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, order=0, last_seen=datetime.now(timezone.utc) - timedelta(days=60))
    _stream(db_session, 'b', tv)
    _attempts(db_session, 'b', 'ok', 2, seconds=3600)
    db_session.commit()
    assert TunerService(db_session).relay_stream_ids(tv.id)[0] == 'a' * 40


def test_the_recorder_writes_the_outcome_with_its_list_and_channel_size(db_session):
    from sqlalchemy.orm import Session
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, source_url=LIST_A)
    _stream(db_session, 'b', tv)
    db_session.commit()
    recorder = StreamHistoryRecorder(lambda: Session(bind=db_session.get_bind()), clock=lambda: NOW)
    recorder.record('A' * 40, tv.id, 'early_death', seconds=12.5)
    recorder.flush()
    db_session.expire_all()
    row = db_session.query(StreamAttempt).one()
    assert (row.content_id, row.outcome, row.seconds, row.source_url, row.channel_sources) == \
        ('a' * 40, 'early_death', 12.5, LIST_A, 2)


def test_a_failing_recorder_never_breaks_playback(monkeypatch, caplog):
    def broken(*_args, **_kwargs):
        raise RuntimeError('disk full')
    monkeypatch.setattr(tuner_playback_service, '_outcome_recorder', broken)
    tuner_playback_service.record_outcome('a' * 40, 1, 'ok', seconds=10)
    assert 'outcome recorder failed' in caplog.text


def test_without_a_recorder_outcomes_are_ignored(monkeypatch):
    monkeypatch.setattr(tuner_playback_service, '_outcome_recorder', None)
    tuner_playback_service.record_outcome('a' * 40, 1, 'ok', seconds=10)


@pytest.mark.parametrize('previous_revision', ['20261103_1200'])
def test_stream_attempts_migration_upgrade_path(tmp_path, previous_revision):
    path = tmp_path / 'history.db'
    upgrade_to_revision(path, previous_revision)
    upgrade_to_head(path)
    engine = create_engine(database_url_for(path))
    assert 'stream_attempts' in inspect(engine).get_table_names()
    downgrade_to_revision(path, previous_revision)
    assert 'stream_attempts' not in inspect(engine).get_table_names()
    upgrade_to_head(path)
    engine.dispose()


def _playlist(db, **options):
    from app.services.playlist_service import PlaylistService
    return asyncio.run(PlaylistService(db).generate_playlist(
        only_online=False, base_url='http://tuner.example/tuner/channel/{tv_channel_id}.ts', **options))


def test_hide_unusable_leaves_out_a_channel_with_no_useful_source(db_session):
    gone = TVChannel(name='Stale Channel', is_active=True)
    kept = TVChannel(name='Live Channel', is_active=True)
    db_session.add_all([gone, kept])
    db_session.flush()
    _stream(db_session, 'a', gone, last_seen=datetime.now(timezone.utc) - timedelta(days=60))
    _stream(db_session, 'b', gone)
    _attempts(db_session, 'b', 'no_data', 3)
    _stream(db_session, 'c', kept)
    db_session.commit()
    assert 'Stale Channel' in _playlist(db_session)
    hidden = _playlist(db_session, hide_unusable=True)
    assert 'Stale Channel' not in hidden and 'Live Channel' in hidden


def test_hide_unusable_keeps_a_channel_while_one_source_is_useful(db_session):
    tv = _channel(db_session)
    _stream(db_session, 'a', tv, last_seen=datetime.now(timezone.utc) - timedelta(days=60))
    _stream(db_session, 'b', tv, online=None)
    db_session.commit()
    body = _playlist(db_session, hide_unusable=True, per_source=True)
    assert 'Example Sports' in body
    assert 'b' * 40 in body and 'a' * 40 not in body


def test_the_tuner_setting_hides_unusable_channels_in_the_playlist_and_lineup(db_session):
    gone = TVChannel(name='Stale Channel', is_active=True)
    kept = TVChannel(name='Live Channel', is_active=True)
    db_session.add_all([gone, kept])
    db_session.flush()
    _stream(db_session, 'a', gone, last_seen=datetime.now(timezone.utc) - timedelta(days=60))
    _stream(db_session, 'c', kept)
    db_session.commit()
    tuner = TunerService(db_session)
    assert not tuner.settings().hide_unusable
    assert {entry.guide_name for entry in tuner.build_lineup().entries} == {'Stale Channel', 'Live Channel'}
    tuner.update_settings(hide_unusable=True)
    assert 'Stale Channel' not in _playlist(db_session)
    assert 'Stale Channel' in _playlist(db_session, hide_unusable=False)
    assert {entry.guide_name for entry in tuner.build_lineup().entries} == {'Live Channel'}


def test_a_clock_that_starts_ahead_hides_nothing_until_the_lists_are_read(db_session):
    from app.services.stream_history import unusable_ids
    tv = _channel(db_session)
    _stream(db_session, 'a', tv)
    _stream(db_session, 'b', tv, last_seen=datetime.now(timezone.utc) - timedelta(days=3))
    db_session.commit()
    streams = db_session.query(AcestreamChannel).all()
    assert unusable_ids(db_session, streams, now=datetime.now(timezone.utc) + timedelta(days=45)) == set()


def test_a_box_left_off_for_weeks_hides_only_what_the_last_reading_had_already_lost(db_session):
    gone = TVChannel(name='Stale Channel', is_active=True)
    kept = TVChannel(name='Live Channel', is_active=True)
    db_session.add_all([gone, kept])
    db_session.flush()
    last_reading = datetime.now(timezone.utc) - timedelta(days=21)
    _stream(db_session, 'a', gone, last_seen=last_reading - timedelta(days=20))
    _stream(db_session, 'c', kept, last_seen=last_reading)
    db_session.commit()
    body = _playlist(db_session, hide_unusable=True)
    assert 'Live Channel' in body and 'Stale Channel' not in body


def test_a_source_that_kept_jumping_back_ranks_below_one_that_played_cleanly():
    scores = score_sources([Row('a'), Row('b')],
                           [attempt('a', 'jumpy', seconds=600), attempt('b', 'ok', seconds=600)], {}, NOW)
    assert scores['b' * 40].score > 0.5 > scores['a' * 40].score


def test_a_long_jumpy_viewing_counts_more_against_the_source_than_a_short_one():
    long = score_sources([Row('a')], [attempt('a', 'jumpy', seconds=3600)], {}, NOW)
    short = score_sources([Row('a')], [attempt('a', 'jumpy', seconds=10)], {}, NOW)
    assert long['a' * 40].score < short['a' * 40].score


def test_the_relay_turns_a_viewing_with_jumps_back_into_jumpy():
    from app.services.tuner_playback_service import _with_clock
    from app.services.ts_clock import ClockWatch
    watch = ClockWatch('a' * 40)
    assert _with_clock('ok', watch) == 'ok'
    watch.back_jumps = 2
    assert [_with_clock(o, watch) for o in ('ok', 'ended', 'stall', 'no_data', 'early_death')] == \
        ['jumpy', 'jumpy', 'jumpy', 'no_data', 'early_death']
