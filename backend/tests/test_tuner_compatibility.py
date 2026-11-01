"""Tuner rendition selection and Plex AAC/LATM transport compatibility."""
import asyncio
import os
import subprocess
from unittest.mock import Mock

import pytest

from app.services.hls_selection import best_variant
from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.tuner_remux import ffmpeg_binary, compatible_audio_source
from app.services import tuner_playback_service


def test_best_variant_retains_only_associated_audio_and_subtitle_groups():
    master = '''#EXTM3U
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-SESSION-KEY:METHOD=AES-128,URI="key"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="low",NAME="low",URI="low-audio.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="high",NAME="Spanish, main",LANGUAGE="es",URI="es.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="high",NAME="English",LANGUAGE="en",URI="en.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Spanish",URI="subs.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=600000,RESOLUTION=640x360,AUDIO="low"
low.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=4000000,RESOLUTION=1920x1080,AUDIO="high",SUBTITLES="subs",CODECS="avc1.640028,mp4a.40.2"
high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=9000000,RESOLUTION=1280x720,AUDIO="low"
medium.m3u8
#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=100000,URI="trick.m3u8"
'''
    result = best_variant(master)
    assert result.count('#EXT-X-STREAM-INF:') == 1
    assert 'high.m3u8' in result and 'es.m3u8' in result and 'en.m3u8' in result
    assert 'subs.m3u8' in result and 'SESSION-KEY' in result
    assert 'low' not in result and 'medium' not in result and 'trick' not in result


def test_best_variant_falls_back_to_bandwidth_and_leaves_media_playlists_alone():
    assert 'high.ts' in best_variant('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=10\nlow.ts\n'
        '#EXT-X-STREAM-INF:BANDWIDTH=20\nhigh.ts\n')
    media = '#EXTM3U\n#EXTINF:1,\nsegment.ts\n'
    assert best_variant(media) == media


def test_audio_compatibility_setting_is_opt_in_and_persists(client):
    url = '/api/v1/tuner/settings'
    assert client.get(url).json()['plex_compatible_audio'] is False
    assert client.put(url, json={'plex_compatible_audio': True}).json()['plex_compatible_audio'] is True
    assert client.put(url, json={'friendly_name': 'Changed'}).json()['plex_compatible_audio'] is True
    assert client.put(url, json={'plex_compatible_audio': False}).json()['plex_compatible_audio'] is False


@pytest.mark.asyncio
async def test_compatible_engine_output_preserves_1080_video_and_decodes_audio(tmp_path, monkeypatch):
    try:
        runtime = ffmpeg_binary()
    except EngineStreamError:
        pytest.skip('FFmpeg required')
    media = os.environ.get('FFMPEG_TEST_TOOL_PATH', runtime)
    original = subprocess.run([media, '-v', 'error', '-f', 'lavfi', '-i',
        'color=c=blue:s=1920x1080:r=25', '-f', 'lavfi', '-i', 'sine=sample_rate=48000',
        '-t', '3', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '25', '-c:a', 'aac',
        '-f', 'mpegts', 'pipe:1'], check=True, capture_output=True, timeout=20).stdout
    closed = []
    async def raw(*args, **kwargs):
        try:
            for start in range(0, len(original), 777):
                yield original[start:start + 777]
        finally:
            closed.append(True)
    monkeypatch.setattr(tuner_playback_service, 'relay_engine_stream', raw)
    registry = RelayRegistry()
    claim = registry.try_open('test', 'Plex', 1)
    async with asyncio.timeout(10):
        output = b''.join([chunk async for chunk in tuner_playback_service.relay_ranked_streams(
            Mock(), ['test'], 'Plex', claim, registry=registry, plex_compatible_audio=True)])
    assert closed == [True] and registry.count_active() == 0
    path = tmp_path / 'compatible.ts'
    path.write_bytes(output)
    probe = subprocess.run([media, '-hide_banner', '-i', str(path), '-map', '0', '-f', 'null', '-'],
        capture_output=True, timeout=10)
    assert probe.returncode == 0, probe.stderr.decode()
    assert '1920x1080' in probe.stderr.decode()
    assert 'aac_latm' in probe.stderr.decode()
    assert '48000 Hz' in probe.stderr.decode()
    # No video re-encoding: compare the elementary H.264 packet bytes.
    def elementary(data):
        return subprocess.run([media, '-v', 'error', '-i', 'pipe:0', '-map', '0:v:0',
            '-c', 'copy', '-f', 'h264', 'pipe:1'], input=data, capture_output=True, check=True, timeout=10).stdout
    assert elementary(output) == elementary(original)
    # Model Plex's rolling MPEG-TS recorder, then join later and make MKV with
    # decoded LATM audio. This exercises codec discovery beyond the first packet.
    subprocess.run([media, '-v', 'error', '-i', str(path), '-map', '0', '-c', 'copy',
        '-f', 'segment', '-segment_time', '1', str(tmp_path / 'part-%d.ts')],
        check=True, capture_output=True, timeout=10)
    joined = subprocess.run([media, '-v', 'error', '-i', str(tmp_path / 'part-1.ts'),
        '-c:v', 'copy', '-c:a', 'aac', '-f', 'matroska', 'pipe:1'], capture_output=True, timeout=10)
    assert joined.returncode == 0, joined.stderr.decode()
    assert joined.stdout and not joined.stderr


@pytest.mark.asyncio
async def test_compatible_audio_cancellation_closes_source_and_child(monkeypatch):
    try:
        ffmpeg_binary()
    except EngineStreamError:
        pytest.skip('FFmpeg required')
    spawn = asyncio.create_subprocess_exec
    children = []
    async def tracked(*args, **kwargs):
        child = await spawn(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', tracked)
    entered, closed = asyncio.Event(), asyncio.Event()
    async def source():
        try:
            entered.set()
            await asyncio.Event().wait()
            yield b''
        finally:
            closed.set()
    iterator = compatible_audio_source(source())
    read = asyncio.create_task(anext(iterator))
    await asyncio.wait_for(entered.wait(), 2)
    read.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(read, 4)
    assert closed.is_set() and children[0].returncode is not None
