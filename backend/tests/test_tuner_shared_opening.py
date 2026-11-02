"""Kodi's two GETs of a channel share one opening.

Kodi sends its second GET as soon as the first one gets bytes, and each GET
ran its own rotation from the first source, so a dead source was tried again.
The newer GET must go on from where the older one is, and the older one must
start no further source.
"""
import asyncio
import time
from unittest.mock import Mock

import pytest

import app.services.tuner_playback_service as playback
from app.services.stream_relay import RelayRegistry

DEAD, LIVE, OTHER = "d1" * 20, "e1" * 20, "f1" * 20


@pytest.fixture(autouse=True)
def fresh_memory():
    """The relay's failure memory and openings are process-wide."""
    playback._failures.clear()
    playback._openings.clear()
    yield
    playback._failures.clear()
    playback._openings.clear()


@pytest.fixture
def sources(monkeypatch):
    """A dead source (an ID starting with d) never sends a byte; any other sends video."""
    calls = []
    t0 = time.monotonic()

    async def relay(_engine, content_id, _label, **kwargs):
        calls.append((round(time.monotonic() - t0, 2), content_id))
        if content_id.startswith("d"):
            await asyncio.sleep(60)
        while True:
            yield b"video"
            await asyncio.sleep(0.01)
    monkeypatch.setattr(playback, "relay_engine_stream", relay)
    return calls


def _relay(registry, ids, **kwargs):
    claim = registry.try_open(ids[0], "tuner:kodi", 4)
    return playback.relay_ranked_streams(Mock(), ids, "tuner:kodi", claim, registry=registry,
                                         attempt_seconds=0.4, startup_budget_seconds=3, **kwargs)


@pytest.mark.asyncio
async def test_the_second_get_goes_on_from_the_first_instead_of_starting_again(sources):
    registry = RelayRegistry()
    key = ("kodi", 1)
    first_opening, previous = playback.take_over_opening(key)
    assert previous is None
    first = _relay(registry, [DEAD, LIVE], opening=first_opening)
    first_task = asyncio.ensure_future(anext(first))
    await asyncio.sleep(0.2)

    second_opening, previous = playback.take_over_opening(key)
    order, resume_deadline, skip = playback.resume_order([DEAD, LIVE], previous)
    assert order == [DEAD, LIVE] and resume_deadline is not None and not skip
    second = _relay(registry, order, opening=second_opening, resume_deadline=resume_deadline, skip=skip)
    assert await anext(second) == b"video"

    # The older GET gave way once its source failed: no source of its own.
    with pytest.raises(StopAsyncIteration):
        await first_task
    started = [cid for _, cid in sources]
    assert started == [DEAD, DEAD, LIVE], sources
    # The second GET waited for the dead source only as long as the first had left.
    live_at = next(at for at, cid in sources if cid == LIVE)
    assert live_at < 0.55, sources
    await second.aclose()
    await first.aclose()
    playback.end_opening(key, second_opening)


def test_a_playing_source_goes_first_without_a_deadline():
    previous = playback.ChannelOpening(current=LIVE, current_deadline=None, failed=[DEAD])
    assert playback.resume_order([DEAD, OTHER, LIVE], previous) == ([LIVE, OTHER], None, {DEAD})


def test_a_source_out_of_time_counts_as_failed():
    previous = playback.ChannelOpening(current=DEAD, current_deadline=time.monotonic() - 1)
    assert playback.resume_order([DEAD, LIVE], previous) == ([LIVE], None, {DEAD})


@pytest.mark.asyncio
async def test_a_source_the_older_get_saw_fail_is_not_started_again(sources):
    """A source the older GET saw fail moments ago is not started again."""
    from app.services.stream_relay import EngineStreamError
    with pytest.raises(EngineStreamError):
        await anext(_relay(RelayRegistry(), [DEAD], skip={DEAD}))
    assert sources == []


@pytest.mark.asyncio
async def test_a_playing_older_get_ends_once_taken_over(sources):
    """The older GET stops relaying once the newer one plays the source."""
    opening = playback.ChannelOpening()
    stream = _relay(RelayRegistry(), [LIVE], opening=opening)
    assert await anext(stream) == b"video"
    assert await anext(stream) == b"video"
    opening.superseded = True
    with pytest.raises(StopAsyncIteration):
        await anext(stream)


def test_an_opening_that_just_ended_is_still_taken_over():
    """Kodi closes its first GET as soon as it gets bytes; the second came
    30 ms later on the bench and found nothing to go on from."""
    key = ("kodi", 2)
    opening, _ = playback.take_over_opening(key)
    opening.current = LIVE
    playback.end_opening(key, opening)
    _, previous = playback.take_over_opening(key)
    assert previous is opening


def test_an_opening_that_ended_long_ago_is_not_taken_over(monkeypatch):
    key = ("kodi", 3)
    opening, _ = playback.take_over_opening(key)
    playback.end_opening(key, opening)
    opening.ended_at -= playback.STOP_LINGER_SECONDS
    _, previous = playback.take_over_opening(key)
    assert previous is None


def _dead_relay(calls):
    t0 = time.monotonic()

    async def relay(_engine, content_id, _label, **kwargs):
        calls.append((round(time.monotonic() - t0, 2), content_id))
        await asyncio.sleep(60)
        yield b""
    return relay


@pytest.mark.asyncio
async def test_a_source_that_dies_in_its_first_minute_failed_to_start(monkeypatch):
    """Some 15 s of picture and then nothing: an old broadcast the engine still
    holds pieces of. It stays behind the others for longer than a plain
    failure, and the statistics hear of it."""
    monkeypatch.setattr(playback, "STALL_SECONDS", 0.2)
    outcomes = []
    playback.set_outcome_recorder(lambda cid, tv, outcome, **kw: outcomes.append((cid, tv, outcome)))

    async def short_lived(_engine, content_id, _label, **kwargs):
        for _ in range(3):
            yield b"video"
            await asyncio.sleep(0.01)
        await asyncio.sleep(60)
    monkeypatch.setattr(playback, "relay_engine_stream", short_lived)
    try:
        stream = _relay(RelayRegistry(), [DEAD], tv_channel_id=7)
        async for _ in stream:             # the response ends: nothing else to try
            pass
        assert outcomes == [(DEAD, 7, "early_death")]
        # Past the plain 60 s cooldown it is still behind a fresh source.
        monkeypatch.setattr(playback.time, "monotonic", lambda real=time.monotonic: real() + 120)
        assert playback.prefer_recovered_sources([DEAD, LIVE]) == [LIVE, DEAD]
    finally:
        playback.set_outcome_recorder(None)


@pytest.mark.asyncio
async def test_each_attempt_reports_how_it_ended(sources):
    outcomes = []
    playback.set_outcome_recorder(lambda cid, tv, outcome, **kw: outcomes.append((cid, outcome)))
    try:
        stream = _relay(RelayRegistry(), [DEAD, LIVE], tv_channel_id=7)
        assert await anext(stream) == b"video"
        await stream.aclose()              # the viewer leaves
        assert outcomes == [(DEAD, "no_data"), (LIVE, "ok")]
    finally:
        playback.set_outcome_recorder(None)


@pytest.mark.asyncio
async def test_a_broken_recorder_never_breaks_playback(sources):
    def broken(*args, **kwargs):
        raise RuntimeError("statistics down")
    playback.set_outcome_recorder(broken)
    try:
        stream = _relay(RelayRegistry(), [DEAD, LIVE])
        assert await anext(stream) == b"video"
        await stream.aclose()
    finally:
        playback.set_outcome_recorder(None)
