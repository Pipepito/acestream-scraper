"""Convert guarded HTTP/HLS input to the MPEG-TS transport tuner clients expect.

FFmpeg receives only a session-owned loopback URL. Broadcaster resolution,
headers, redirects and every HLS resource use the shared guarded input proxy.
Video is copied; the optional Plex profile converts audio to stereo AAC/LATM.
No AceStream session is created.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal
import time
from typing import AsyncIterator

import anyio

from app.services.player_http_source import PlayerHTTPSource
from app.services.stream_relay import EngineStreamError, RelayInfo
from app.services.tuner_remux import ffmpeg_binary

logger = logging.getLogger(__name__)


def http_tuner_argv(binary: str, url: str, *, plex_compatible_audio: bool = False) -> list[str]:
    return [
        binary, '-nostdin', '-hide_banner', '-loglevel', 'error',
        '-protocol_whitelist', 'http,tcp,crypto',
        '-format_whitelist', 'hls,mpegts,mov,aac,mp3,webvtt', '-http_proxy', '',
        '-fflags', '+genpts+discardcorrupt', '-probesize', '1000000',
        '-analyzeduration', '1000000', '-i', url,
        '-map', '0:v:0?', '-map', '0:a?', '-c', 'copy',
        *(['-c:a', 'aac', '-b:a', '160k', '-ac', '2'] if plex_compatible_audio else []),
        '-f', 'mpegts', '-mpegts_flags', '+resend_headers+latm' if plex_compatible_audio else '+resend_headers',
        '-muxdelay', '0', '-flush_packets', '1', 'pipe:1',
    ]


async def relay_http_stream(content_id: str, claim: RelayInfo, *, startup_deadline: float, plex_compatible_audio: bool = False) -> AsyncIterator[bytes]:
    source = None
    process = None
    try:
        source = await PlayerHTTPSource.open(content_id, timeout=startup_deadline - time.monotonic())
        source.select_best_variant = True
        spawn = asyncio.create_task(asyncio.create_subprocess_exec(
            *http_tuner_argv(ffmpeg_binary(), source.playback_url, plex_compatible_audio=plex_compatible_audio),
            stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, start_new_session=True,
        ))
        # A cancelled spawn can still create a child; collect and reap it before
        # closing its input proxy or releasing the enclosing tuner slot.
        with anyio.CancelScope(shield=True):
            try:
                process = await asyncio.shield(spawn)
            except asyncio.CancelledError:
                process = await spawn
                raise
        buffered = bytearray()
        while chunk := await process.stdout.read(64 * 1024):
            buffered.extend(chunk)
            complete = len(buffered) // 188 * 188
            if complete:
                claim.bytes_sent += complete
                yield bytes(buffered[:complete])
                del buffered[:complete]
        if await process.wait() != 0:
            # Never expose FFmpeg stderr, signed URLs, headers or upstream text.
            logger.info('HTTP tuner input ended exit_code=%s failures=%s', process.returncode, list(source.failures))
            raise EngineStreamError('HTTP media could not be remuxed for the tuner')
    except (ValueError, OSError) as exc:
        raise EngineStreamError('HTTP media could not be opened for the tuner') from exc
    finally:
        with anyio.CancelScope(shield=True):
            if process is not None:
                # wait() can block even after exit when unread stdout fills the
                # asyncio pipe buffer. Drain concurrently, with bounded memory.
                async def drain():
                    while await process.stdout.read(64 * 1024):
                        pass
                drained = asyncio.create_task(drain())
                if process.returncode is None:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGTERM)
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    await process.wait()
                await drained
            if source is not None:
                await source.close()
