"""Experimental CPU transcoding for MPEG-TS recovery within a connection.

FFmpeg receives only bytes from the guarded engine relay, never upstream URLs.
Video is normalized to MPEG-2 and audio to AAC so existing decoder contexts
may survive source codec changes; receiver compatibility is not guaranteed. Each attempt emits fresh PAT/PMT tables with a new version and discontinuity
flags; source timestamps and PIDs are not blindly concatenated.
"""
from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import signal
from typing import AsyncIterator

import anyio

from app.config.settings import get_settings
from app.services.stream_relay import EngineStreamError


def ffmpeg_binary() -> str:
    configured = get_settings().FFMPEG_BINARY_PATH.strip()
    path = configured if configured and os.access(configured, os.X_OK) else shutil.which('ffmpeg')
    if not path:
        raise EngineStreamError('Experimental transcoding recovery requires FFmpeg on the server')
    return path


def remux_argv(binary: str, *, version: int, offset: float) -> list[str]:
    return [
        binary, '-nostdin', '-hide_banner', '-loglevel', 'error',
        '-protocol_whitelist', 'pipe', '-fflags', '+genpts+discardcorrupt',
        '-probesize', '1000000', '-analyzeduration', '1000000', '-f', 'mpegts', '-i', 'pipe:0',
        '-map', '0:v:0', '-map', '0:a?',
        '-c:v', 'mpeg2video', '-threads', '2', '-q:v', '3', '-g', '25', '-bf', '0', '-r', '25',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-ac', '2',
        '-f', 'mpegts', '-mpegts_flags', '+initial_discontinuity+resend_headers',
        '-tables_version', str(version % 32), '-output_ts_offset', f'{max(0.0, offset):.6f}',
        '-mpegts_copyts', '0', '-muxdelay', '0', '-flush_packets', '1', 'pipe:1'
    ]


async def remux_source(source: AsyncIterator[bytes], *, version: int, offset: float) -> AsyncIterator[bytes]:
    process = None
    feeder = None
    try:
        process = await asyncio.create_subprocess_exec(
            *remux_argv(ffmpeg_binary(), version=version, offset=offset),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, start_new_session=True,
        )

        async def feed() -> None:
            try:
                async for chunk in source:
                    process.stdin.write(chunk)
                    await process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                process.stdin.close()

        feeder = asyncio.create_task(feed())
        buffered = bytearray()
        while chunk := await process.stdout.read(64 * 1024):
            buffered.extend(chunk)
            complete = len(buffered) // 188 * 188
            if complete:
                yield bytes(buffered[:complete])
                del buffered[:complete]
        await feeder
        if await process.wait() != 0:
            raise EngineStreamError('The source could not be remuxed as video')
    except OSError as exc:
        raise EngineStreamError('Unable to start TV relay remuxer') from exc
    finally:
        with anyio.CancelScope(shield=True):
            if feeder is not None:
                feeder.cancel()
                await asyncio.gather(feeder, return_exceptions=True)
            await source.aclose()
            if process is not None and process.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    await process.wait()
