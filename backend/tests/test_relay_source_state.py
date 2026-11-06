"""Each relay tells a source being tried from one that plays.

A client shows the relay's source as playing from ``/player/streams``. The
source was booked when the relay *started trying* it, so a source that never
delivered a frame showed as playing. The relay now
says ``probing`` until the source itself delivers bytes -- bytes the route sends
of its own do not count -- and ``playing`` after, and goes back to
``probing`` on every automatic switch to another source.
"""
import asyncio
from unittest.mock import Mock

import pytest

from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.tuner_playback_service import relay_ranked_streams


def _state(registry):
    [info] = registry.active()
    return info.content_id, info.source_state


@pytest.mark.asyncio
async def test_a_source_is_probing_until_it_delivers_and_again_after_a_switch(monkeypatch):
    import app.services.tuner_playback_service as playback
    release = {'first': asyncio.Event(), 'second': asyncio.Event()}

    async def relay(_engine, content_id, _label, **kwargs):
        await release[content_id].wait()
        yield f'{content_id}-a'.encode()
        if content_id == 'first':
            await asyncio.sleep(10)        # dries up after its first chunk
        yield f'{content_id}-b'.encode()
    monkeypatch.setattr(playback, 'relay_engine_stream', relay)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    registry = RelayRegistry()
    claim = registry.try_open('first', 'viewer', 1)
    stream = relay_ranked_streams(Mock(), ['first', 'second'], 'viewer', claim, registry=registry,
                                  attempt_seconds=1, startup_budget_seconds=2, switch_midstream=True)

    pending = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0.01)
    assert _state(registry) == ('first', 'probing')
    release['first'].set()
    assert await pending == b'first-a'
    assert _state(registry) == ('first', 'playing')

    pending = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0.2)               # past the stall: the relay moves on
    assert _state(registry) == ('second', 'probing')
    release['second'].set()
    assert await pending == b'second-a'
    assert _state(registry) == ('second', 'playing')

    with pytest.raises(EngineStreamError):
        async for _ in stream:
            pass


def test_a_new_relay_starts_probing():
    registry = RelayRegistry()
    assert registry.open('abc', 'viewer').source_state == 'probing'


@pytest.mark.asyncio
async def test_a_single_source_relay_plays_once_the_engine_delivers():
    """The channel route's raw content-ID relay has no ranking: the engine
    reader itself says when its source plays."""
    from tests.test_stream_relay import IH, _engine_and_factory, _fake_engine
    from app.services.stream_relay import relay_engine_stream
    engine, factory = _engine_and_factory(_fake_engine([]))
    registry = RelayRegistry()
    claim = registry.try_open(IH, 'tuner:test', 1)
    stream = relay_engine_stream(engine, IH, 'tuner:test', client_factory=factory, registry=registry, claim=claim)
    assert claim.source_state == 'probing'
    await anext(stream)
    assert _state(registry) == (IH, 'playing')
    await stream.aclose()
