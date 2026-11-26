"""The channel session's choice of sources, and how its callers share it."""
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

import pytest

from app.models.models import AcestreamChannel, TVChannel
from app.services import tuner_playback_service as playback
from app.services.channel_session import ChannelSession, NoSources, TunerBusy, last_resort_candidates, relay_candidates
from app.services.recording_coordinator import candidates as recording_candidates
from app.services.stream_relay import RelayRegistry
from fake_source_reader import FakeReader, environment

A, B, C = 'a' * 40, 'b' * 40, 'c' * 40


@pytest.fixture(autouse=True)
def no_recent_failures(monkeypatch):
    monkeypatch.setattr(playback, '_failures', OrderedDict())
    monkeypatch.setattr(playback, '_openings', {})


def seed(db, rows, *, active=True):
    tv = TVChannel(name='Example channel', is_active=active)
    db.add(tv)
    db.flush()
    now = datetime.now(timezone.utc)
    for cid, online, minutes_ago, bitrate in rows:
        db.add(AcestreamChannel(id=cid, name='Example source', tv_channel_id=tv.id, is_active=True, is_online=online,
                                last_checked=now - timedelta(minutes=minutes_ago), bitrate_bps=bitrate))
    db.commit()
    return tv


def test_a_recording_chooses_the_sources_a_viewer_would(alembic_db_session):
    tv = seed(alembic_db_session, [(A, True, 1, 100), (B, True, 1, 900), (C, False, 1, 5000)])
    playback.record_source_failure(B)
    assert relay_candidates(tv.id) == [A, B]
    assert recording_candidates(tv.id) == relay_candidates(tv.id)
    tv.is_active = False
    alembic_db_session.commit()
    assert recording_candidates(tv.id) == relay_candidates(tv.id) == []
    assert recording_candidates(None) == []


def test_the_last_resort_has_its_own_order_and_keeps_recent_offline_sources(alembic_db_session):
    """Every source, by freshness and bitrate: not the relay order, which
    leaves a recent offline verdict out."""
    tv = seed(alembic_db_session, [(A, True, 1, 100), (B, True, 1, 900), (C, False, 1, 5000)])
    assert relay_candidates(tv.id) == [B, A]
    assert last_resort_candidates(tv.id) == [C, B, A]


@pytest.mark.asyncio
async def test_a_channel_with_nothing_to_try_starts_nothing():
    reader = FakeReader()
    session = ChannelSession(1, 'viewer', environment(reader, candidates=[], last_resort=[]))
    with pytest.raises(NoSources):
        await session.check()
    with pytest.raises(NoSources):
        await session.start()
    assert reader.opened == []


@pytest.mark.asyncio
async def test_no_free_slot_starts_nothing_and_frees_the_opening():
    registry = RelayRegistry()
    held = registry.try_open('other', 'someone', 1)
    reader = FakeReader({A: [b'video']})
    env = environment(reader, candidates=[A], registry=registry)
    with pytest.raises(TunerBusy) as busy:
        await ChannelSession(1, 'viewer', env).start()
    assert busy.value.limit == 1 and reader.opened == []
    registry.close(held.id)
    stream = await ChannelSession(1, 'viewer', env).start()
    assert await anext(stream) == b'video'
    await stream.aclose()
    assert registry.count_active() == 0
