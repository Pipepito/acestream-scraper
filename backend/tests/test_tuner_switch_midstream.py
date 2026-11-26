"""When the playing source stops mid-broadcast, the relay goes on with the next one.

Ending the response so the client reconnects does not work with Kodi: it goes
back to its menu. On a small ARM box a channel played its first seconds and
stopped for good. With tuner_switch_on_failure (off by default) the relay goes on
with the next source in the same response; Kodi follows a raw switch to another
source as a stream change (measured 720p->720p and 720p->1080p).
"""
import asyncio
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


@pytest.mark.asyncio
@pytest.mark.parametrize('switch', [True, False])
async def test_the_channel_session_passes_the_setting(monkeypatch, switch):
    import app.services.tuner_playback_service as playback
    from app.services.channel_session import ChannelSession
    from fake_source_reader import FakeReader, environment
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    reader = FakeReader({'first': [b'first-a', 10], 'second': [b'second-a', b'second-b']})
    stream = await ChannelSession(7, 'viewer', environment(reader, candidates=['first', 'second'],
                                                            switch=switch)).start()
    chunks = [chunk async for chunk in stream]
    assert chunks == ([b'first-a', b'second-a', b'second-b'] if switch else [b'first-a'])


@pytest.mark.asyncio
async def test_the_channel_response_ends_cleanly_when_every_source_is_spent(monkeypatch, caplog):
    # Video already went out: running out of sources ends the response, it is
    # not an error raised into a transfer the client is reading.
    from types import SimpleNamespace
    import app.services.tuner_playback_service as playback
    from app.services import channel_session
    from fake_source_reader import FakeReader, environment
    monkeypatch.setattr(playback, 'STALL_SECONDS', 0.05)
    registry = RelayRegistry()
    stopped = []
    probes = SimpleNamespace(start=Mock(return_value=None), stop_channel=stopped.append)
    reader = FakeReader({'first': [b'first-a', 10], 'second': [b'second-a', 10]})
    session = channel_session.ChannelSession(7, '127.0.0.1', environment(
        reader, candidates=['first', 'second'], switch=True, registry=registry, probes=probes))
    stream = await session.start()
    with caplog.at_level(logging.INFO, logger=channel_session.logger.name):
        chunks = [chunk async for chunk in stream]

    assert chunks == [b'first-a', b'second-a']
    assert 'ran out of sources after playback; ending tv_channel_id=7' in caplog.text
    assert stopped == [7]
    assert registry.count_active() == 0
