"""Real MPEG-TS transitions and bounded subprocess cleanup (when FFmpeg exists)."""
import asyncio
import subprocess
from unittest.mock import Mock

import pytest

from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.tuner_remux import ffmpeg_binary, remux_source
from functools import partial
from app.services.tuner_playback_service import relay_ranked_streams as default_relay_ranked_streams
relay_ranked_streams = partial(default_relay_ranked_streams, experimental_transcoding=True)


@pytest.fixture
def ffmpeg():
    try:
        return ffmpeg_binary()
    except EngineStreamError:
        pytest.skip('FFmpeg is not installed in this test environment')


@pytest.mark.asyncio
@pytest.mark.parametrize("second_codec", ["mpeg2video", "libx264"])
async def test_real_media_switch_keeps_decodable_video_and_announces_new_tables(ffmpeg, tmp_path, monkeypatch, second_codec):
    feeds = {}
    for cid, color in [('one', 'red'), ('two', 'blue')]:
        result = subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i',
            f'color=c={color}:s=160x90:r=10', '-t', '2', '-c:v', 'mpeg2video' if cid == 'one' else second_codec,
            '-f', 'mpegts', 'pipe:1'], capture_output=True, check=True, timeout=15)
        feeds[cid] = result.stdout
    stopped = []
    async def raw(_engine, cid, *args, **kwargs):
        try:
            # Split at arbitrary HTTP boundaries; the remuxer must reconstruct packets.
            for offset in range(0, len(feeds[cid]), 777):
                yield feeds[cid][offset:offset + 777]
            raise EngineStreamError('connection dropped')
        finally:
            stopped.append(cid)
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', raw)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'test', 1)
    iterator = relay_ranked_streams(Mock(), ['one', 'two'], 'test', claim, registry=registry)
    output = bytearray()
    with pytest.raises(EngineStreamError):
        async with asyncio.timeout(15):
            async for chunk in iterator:
                output.extend(chunk)
    assert stopped == ['one', 'two']
    assert registry.count_active() == 0
    assert len(output) % 188 == 0
    versions = set()
    discontinuities = 0
    for offset in range(0, len(output), 188):
        packet = output[offset:offset + 188]
        assert packet[0] == 0x47
        adaptation = (packet[3] >> 4) & 3
        if adaptation in (2, 3) and packet[4] > 0 and packet[5] & 0x80:
            discontinuities += 1
        pid = ((packet[1] & 0x1f) << 8) | packet[2]
        if pid == 0 and packet[1] & 0x40 and adaptation in (1, 3):
            pos = 4 + (1 + packet[4] if adaptation == 3 else 0)
            pos += 1 + packet[pos]
            versions.add((packet[pos + 5] >> 1) & 31)
    assert versions == {0, 1}
    assert discontinuities >= 2
    video = tmp_path / 'switched.ts'
    video.write_bytes(output)
    decoded = subprocess.run([ffmpeg, '-v', 'error', '-i', str(video), '-map', '0:v:0',
        '-f', 'framemd5', 'pipe:1'], capture_output=True, check=True, timeout=15)
    frames = [line for line in decoded.stdout.decode().splitlines() if not line.startswith('#')]
    # Both solid-colour sources decode, not just the first source before its EOF.
    assert len(frames) >= 30
    assert len({line.split(',')[-1].strip() for line in frames}) >= 2


@pytest.mark.asyncio
async def test_cancel_remux_closes_input_and_reaps_child(ffmpeg, monkeypatch):
    original = asyncio.create_subprocess_exec
    children = []
    async def spawn(*args, **kwargs):
        child = await original(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', spawn)
    closed = asyncio.Event()
    entered = asyncio.Event()
    async def source():
        try:
            entered.set()
            await asyncio.Event().wait()
            yield b''
        finally:
            closed.set()
    iterator = remux_source(source(), version=0, offset=0)
    reader = asyncio.create_task(anext(iterator))
    await asyncio.wait_for(entered.wait(), 3)
    reader.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(reader, 5)
    assert closed.is_set()
    assert children[0].returncode is not None
