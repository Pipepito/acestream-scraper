"""When the playing source stops mid-broadcast, the relay goes on with the next one.

Ending the response so the client reconnects does not work with Kodi: it goes
back to its menu. On a small ARM box a channel played its first seconds and
stopped for good. With tuner_switch_on_failure (off by default) the relay goes on
with the next source in the same response; Kodi follows a raw switch to another
source as a stream change (measured 720p->720p and 720p->1080p).
"""
import asyncio
import inspect
from unittest.mock import Mock

import pytest

from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.tuner_playback_service import relay_ranked_streams


@pytest.mark.asyncio
async def test_a_source_that_dries_up_mid_broadcast_switches_to_the_next(monkeypatch):
    import app.services.tuner_playback_service as playback
    calls = []

    async def relay(_engine, content_id, _label, **kwargs):
        calls.append(content_id)
        yield f'{content_id}-a'.encode()
        if content_id == 'first':
            await asyncio.sleep(10)        # stalls after its first chunk
        yield f'{content_id}-b'.encode()
    monkeypatch.setattr(playback, 'relay_engine_stream', relay)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    registry = RelayRegistry()
    claim = registry.try_open('first', 'viewer', 1)
    received = []
    # Once every source is spent the relay raises; the channel route ends the
    # response there.
    with pytest.raises(EngineStreamError):
        async for chunk in relay_ranked_streams(Mock(), ['first', 'second'], 'viewer', claim, registry=registry,
                                                attempt_seconds=1, startup_budget_seconds=2, switch_midstream=True):
            received.append(chunk)
    assert received == [b'first-a', b'second-a', b'second-b']
    assert calls == ['first', 'second']


@pytest.mark.asyncio
async def test_without_the_setting_the_response_ends_as_before(monkeypatch):
    import app.services.tuner_playback_service as playback

    async def relay(_engine, content_id, _label, **kwargs):
        yield f'{content_id}-a'.encode()
        await asyncio.sleep(10)
    monkeypatch.setattr(playback, 'relay_engine_stream', relay)
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    registry = RelayRegistry()
    claim = registry.try_open('first', 'viewer', 1)
    received = [chunk async for chunk in relay_ranked_streams(Mock(), ['first', 'second'], 'viewer', claim,
                                                              registry=registry, attempt_seconds=1, startup_budget_seconds=2)]
    assert received == [b'first-a']


def test_the_channel_route_passes_the_setting():
    from app.api.endpoints import tuner
    assert 'switch_midstream=await run_in_threadpool(_switch_on_failure)' in inspect.getsource(tuner)
