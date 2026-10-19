"""A healthy acestream can be silent for over 16 s between engine pieces.

Measured on a live engine: at 97 kB/s the engine handed over ~1.5 MB pieces,
with gaps of up to 16.4 s, and the relay's 15 s stall timeout cut a source
that was playing fine. And the time a source counts as healthy ends at its
last chunk when it stalls, not after the stall wait: counted with the wait,
a source that sent one chunk and stalled looked healthy, the attempts were
reset, and with recovery enabled two such sources took turns forever.
"""
import asyncio
from unittest.mock import Mock

import pytest

import app.services.tuner_playback_service as playback
from app.services.stream_relay import EngineStreamError, RelayRegistry


@pytest.fixture(autouse=True)
def clean_failures(monkeypatch):
    monkeypatch.setattr(playback, '_failures', __import__('collections').OrderedDict())


def test_the_stall_timeout_is_above_a_healthy_sources_longest_gap():
    assert playback.STALL_SECONDS > 16.4 * 1.4


@pytest.mark.asyncio
async def test_a_source_silent_between_pieces_is_not_cut(monkeypatch):
    async def bursty(_engine, content_id, _label, **kwargs):
        for i in range(3):
            yield f'piece-{i}'.encode()
            await asyncio.sleep(0.08)          # a gap, scaled down
    monkeypatch.setattr(playback, 'relay_engine_stream', bursty)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.1)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    stream = playback.relay_ranked_streams(Mock(), ['one'], 'viewer', claim, registry=registry)
    got = [await anext(stream) for _ in range(3)]
    await stream.aclose()
    assert got == [b'piece-0', b'piece-1', b'piece-2']


@pytest.mark.asyncio
async def test_two_stalling_sources_do_not_take_turns_forever(monkeypatch):
    calls = []

    async def stalls(_engine, content_id, _label, **kwargs):
        calls.append(content_id)
        yield f'{content_id}-a'.encode()
        await asyncio.sleep(10)

    monkeypatch.setattr(playback, 'relay_engine_stream', stalls)
    monkeypatch.setattr(playback, 'remux_source', lambda raw, **kwargs: raw)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    monkeypatch.setattr(playback, 'HEALTHY_SECONDS', 0.04)
    monkeypatch.setattr(playback, 'STARTUP_BUDGET_SECONDS', 60)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    with pytest.raises(EngineStreamError):
        async with asyncio.timeout(3):
            async for _ in playback.relay_ranked_streams(Mock(), ['one', 'two'], 'viewer', claim,
                                                          registry=registry, experimental_transcoding=True):
                pass
    assert calls == ['one', 'two']


@pytest.mark.asyncio
@pytest.mark.parametrize('ending', ['eof', 'transport'])
async def test_silence_before_eof_or_transport_failure_does_not_reset_budget(monkeypatch, ending):
    """Neither quiet gap reaches the stall limit, but silence is not delivery."""
    from types import SimpleNamespace

    calls = []
    clock = [0.0]
    monkeypatch.setattr(playback, 'time', SimpleNamespace(monotonic=lambda: clock[0]))

    async def short_source(_engine, content_id, _label, **kwargs):
        calls.append(content_id)
        assert len(calls) <= 2, 'quiet time incorrectly renewed the recovery budget'
        yield b'first'
        clock[0] += 10
        yield b'last'
        clock[0] += 24
        if ending == 'transport':
            raise EngineStreamError('connection lost')

    monkeypatch.setattr(playback, 'relay_engine_stream', short_source)
    monkeypatch.setattr(playback, 'remux_source', lambda raw, **kwargs: raw)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 25)
    monkeypatch.setattr(playback, 'HEALTHY_SECONDS', 30)
    monkeypatch.setattr(playback, 'STARTUP_BUDGET_SECONDS', 45)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    with pytest.raises(EngineStreamError):
        async with asyncio.timeout(1):
            async for _ in playback.relay_ranked_streams(
                Mock(), ['one', 'two'], 'viewer', claim,
                registry=registry, experimental_transcoding=True,
            ):
                pass
    assert calls == ['one', 'two']
