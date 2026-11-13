"""When the playing source stops mid-broadcast, the relay goes on with the next one.

Ending the response so the client reconnects does not work with Kodi: it goes
back to its menu. On a small ARM box a channel played its first seconds and
stopped for good. With tuner_switch_on_failure (off by default) the relay goes on
with the next source in the same response; Kodi follows a raw switch to another
source as a stream change (measured 720p->720p and 720p->1080p).
"""
import asyncio
import inspect
import logging
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


@pytest.mark.asyncio
async def test_the_channel_response_ends_cleanly_when_every_source_is_spent(monkeypatch, caplog):
    # Video already went out: running out of sources ends the response, it is
    # not an error raised into a transfer the client is reading.
    from types import SimpleNamespace
    from starlette.requests import Request
    from app.api.endpoints import tuner
    registry = RelayRegistry()
    stopped = []
    monkeypatch.setattr(tuner, 'relay_registry', registry)
    monkeypatch.setattr(tuner, '_channel_candidates', lambda *args, **kwargs: ['first', 'second'])
    monkeypatch.setattr(tuner, '_tuner_count', lambda: 1)
    monkeypatch.setattr(tuner, '_engine', Mock)
    monkeypatch.setattr(tuner, '_relay_settings', lambda: SimpleNamespace(
        experimental_transcoding=False, plex_compatible_audio=False, source_start_seconds=1, startup_budget_seconds=2))
    monkeypatch.setattr(tuner, '_switch_on_failure', lambda: True)
    monkeypatch.setattr(tuner.tuner_probe_service, 'start', Mock(return_value=None))
    monkeypatch.setattr(tuner.tuner_probe_service, 'stop_channel', stopped.append)

    async def relay(_engine, _candidates, _label, claim, **kwargs):
        assert kwargs['switch_midstream'] is True
        try:
            yield b'first-a'
            yield b'second-a'
            raise EngineStreamError('No source left')
        finally:
            registry.close(claim.id)
    monkeypatch.setattr(tuner, 'relay_ranked_streams', relay)

    response = await tuner.tuner_channel(7, Request({'type': 'http', 'method': 'GET', 'client': ('127.0.0.1', 1)}))
    with caplog.at_level(logging.INFO, logger=tuner.__name__):
        chunks = [chunk async for chunk in response.body_iterator]

    assert chunks == [b'first-a', b'second-a']
    assert 'ran out of sources after playback; ending tv_channel_id=7' in caplog.text
    assert stopped == [7]
    assert registry.count_active() == 0
