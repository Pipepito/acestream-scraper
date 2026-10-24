"""The per-source start setting must not be cut short by the relay's HTTP read
timeout.

`relay_engine_stream` reads the engine through httpx with
`RELAY_TIMEOUT.read`. A cold engine that answers the headers and then sends
nothing for longer than that read timeout raised `ReadTimeout` -- and so ended
the attempt -- before `source_start_seconds` was up: raising that setting past
the read timeout did nothing (#226).

These tests use a real HTTP server and the real relay, no mocks in between,
scaled down from `RELAY_TIMEOUT.read`: headers at once, the first video byte
after 2.5 read timeouts.
"""
import asyncio
import collections

import httpx
import pytest

from app.services import stream_relay, tuner_playback_service as playback
from app.services.engine_client import EngineSession
from app.services.stream_relay import EngineStreamError, RelayRegistry

READ = 0.2                    # the scaled read timeout
FIRST_BYTE = 2.5 * READ       # how long the cold engine is silent after the headers
PAYLOAD = b'G' + bytes(187)   # one MPEG-TS packet


@pytest.fixture(autouse=True)
def scaled(monkeypatch):
    monkeypatch.setattr(stream_relay, 'RELAY_TIMEOUT', httpx.Timeout(connect=1.0, read=READ, write=1.0, pool=1.0))
    monkeypatch.setattr(playback, '_failures', collections.OrderedDict())


class ColdEngine:
    """Hands out a playback URL on a local server that answers the headers at
    once and the first byte after FIRST_BYTE."""
    use_acexy = False

    def __init__(self, port):
        self.engine_url = 'http://127.0.0.1:%d' % port

    def start(self, content_id, *, startup_deadline=None):
        url = '%s/ace/r/%s' % (self.engine_url, content_id)
        return EngineSession(content_id=content_id, pid='p', playback_url=url, stat_url=url,
                             command_url=url, is_live=True)

    def stop(self, session, *, linger_seconds=0):
        pass

    def close(self):
        pass


async def _serve(reader, writer):
    await reader.readuntil(b'\r\n\r\n')
    writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: video/mp2t\r\nTransfer-Encoding: chunked\r\n\r\n')
    await writer.drain()
    await asyncio.sleep(FIRST_BYTE)
    try:
        writer.write(b'%x\r\n%s\r\n0\r\n\r\n' % (len(PAYLOAD), PAYLOAD))
        await writer.drain()
    except ConnectionError:
        pass                  # the relay already gave up: that is the failure under test
    writer.close()


def _first_chunk(attempt_seconds):
    async def run():
        server = await asyncio.start_server(_serve, '127.0.0.1', 0)
        registry = RelayRegistry()
        claim = registry.try_open('cold', 'test', 1)
        relay = playback.relay_ranked_streams(
            ColdEngine(server.sockets[0].getsockname()[1]), ['cold'], 'test', claim,
            registry=registry, attempt_seconds=attempt_seconds, startup_budget_seconds=2 * attempt_seconds)
        try:
            return await anext(relay)
        finally:
            await relay.aclose()
            server.close()
    return asyncio.run(run())


def test_a_start_setting_longer_than_the_read_timeout_is_honoured():
    # 5 read timeouts per source, first byte at 2.5: the setting covers it,
    # the read timeout alone would not.
    assert _first_chunk(attempt_seconds=5 * READ) == PAYLOAD


def test_a_start_setting_shorter_than_the_first_byte_still_fails():
    # Control: the setting itself still ends the attempt.
    with pytest.raises(EngineStreamError):
        _first_chunk(attempt_seconds=1.5 * READ)
