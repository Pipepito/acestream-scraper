"""Null packets (PID 0x1FFF) are padding, not media: the relay leaves them out,
so a source that sends only padding looks silent and the next one is tried."""
import asyncio
import collections

import pytest

from app.services import tuner_playback_service as playback
from app.services.stream_relay import RelayRegistry
from app.services.ts_nulls import drop_null_packets

NULL = b"\x47\x1f\xff\x10" + bytes(184)
MEDIA = b"\x47\x01\x00\x10" + b"\xaa" * 184
# Media whose third byte is 0xff on another PID: only PID 0x1FFF is padding.
MEDIA_FF = b"\x47\x00\xff\x10" + b"\xbb" * 184


def _drain(chunks):
    async def source():
        for chunk in chunks:
            yield chunk

    async def run():
        return [c async for c in drop_null_packets(source(), "test")]
    return asyncio.run(run())


def test_null_packets_are_dropped_and_media_kept_in_order():
    assert b"".join(_drain([NULL + MEDIA + NULL + MEDIA_FF + NULL])) == MEDIA + MEDIA_FF


def test_a_chunk_of_padding_alone_is_not_yielded():
    assert _drain([NULL * 50, MEDIA]) == [MEDIA]


def test_packets_split_across_chunks_are_put_back_together():
    stream = NULL + MEDIA + NULL + MEDIA
    chunks = [stream[i:i + 100] for i in range(0, len(stream), 100)]
    assert b"".join(_drain(chunks)) == MEDIA + MEDIA


def test_unaligned_bytes_pass_through_unchanged():
    data = b"\x00" * 10 + NULL + MEDIA
    assert b"".join(_drain([data, NULL])) == data + NULL


def test_a_trailing_partial_packet_is_kept():
    assert b"".join(_drain([MEDIA + MEDIA[:50]])) == MEDIA + MEDIA[:50]


@pytest.fixture
def engine_sources(monkeypatch):
    """Each content ID plays the chunks given for it, then stays open and silent."""
    monkeypatch.setattr(playback, "_failures", collections.OrderedDict())
    plays = {}

    async def fake_relay(engine, content_id, client_label, **kwargs):
        for chunk in plays[content_id]:
            yield chunk
            await asyncio.sleep(0.01)
        await asyncio.sleep(3600)

    monkeypatch.setattr(playback, "relay_engine_stream", fake_relay)
    return plays


class _Engine:
    use_acexy = False

    def stop(self, session, *, linger_seconds=0):
        pass

    def close(self):
        pass


def test_a_source_of_padding_alone_gives_way_to_the_next(engine_sources):
    engine_sources["padding"] = [NULL * 100] * 20
    engine_sources["media"] = [MEDIA * 10]

    async def run():
        registry = RelayRegistry()
        claim = registry.try_open("padding", "test", 1)
        relay = playback.relay_ranked_streams(
            _Engine(), ["padding", "media"], "test", claim,
            registry=registry, attempt_seconds=0.5, startup_budget_seconds=5)
        try:
            return await asyncio.wait_for(anext(relay), 5)
        finally:
            await relay.aclose()

    assert asyncio.run(run()) == MEDIA * 10
