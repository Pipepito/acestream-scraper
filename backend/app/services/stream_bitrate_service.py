"""Probe audio tracks and encoded bitrate from a bounded media sample."""
from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

import httpx
import anyio

from app.config.settings import get_settings
from app.services.stream_relay import _host_identity

SAMPLE_BYTES = 2 * 1024 * 1024


def sample_bitrate(payload: dict) -> int | None:
    """ffprobe's format estimate, or encoded packet bytes over media time."""
    try:
        value = float(payload.get("format", {}).get("bit_rate", 0))
        if math.isfinite(value) and 0 < value <= 1_000_000_000:
            return int(value)
    except (TypeError, ValueError, AttributeError):
        pass
    timestamps, size = [], 0
    for packet in payload.get("packets", []):
        try:
            pts, length = float(packet["pts_time"]), int(packet["size"])
            if math.isfinite(pts) and length > 0:
                timestamps.append(pts)
                size += length
        except (KeyError, TypeError, ValueError):
            continue
    duration = max(timestamps) - min(timestamps) if timestamps else 0
    rate = int(size * 8 / duration) if duration >= 0.5 else 0
    return rate if 0 < rate <= 1_000_000_000 else None


def has_media_packets(payload: dict) -> bool:
    """Stream declarations alone are insufficient: require encoded A/V packets."""
    indexes = {stream.get("index") for stream in payload.get("streams", [])
               if stream.get("codec_type") in ("video", "audio") and stream.get("codec_name")
               and isinstance(stream.get("index"), int)}
    for packet in payload.get("packets", []):
        try:
            if packet.get("stream_index") in indexes and int(packet.get("size", 0)) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


async def probe_media(engine_url: str, playback_url: object, *, timeout: float = 10.0) -> dict | None:
    configured = get_settings().FFMPEG_BINARY_PATH
    sibling = Path(configured).with_name("ffprobe") if configured else None
    binary = str(sibling) if sibling and os.access(sibling, os.X_OK) else shutil.which("ffprobe")
    if not binary or not isinstance(playback_url, str):
        return None
    process = None
    try:
        async with asyncio.timeout(timeout + 5.0):
            # Validate every hop before issuing it. ffprobe receives bytes on stdin
            # and cannot fetch URLs or open files embedded in an upstream playlist.
            async with httpx.AsyncClient(follow_redirects=False, timeout=httpx.Timeout(timeout, read=None)) as client:
                url = httpx.URL(playback_url)
                sample = bytearray()
                deadline = asyncio.get_running_loop().time() + timeout
                for _ in range(4):
                    if url.scheme not in ("http", "https") or _host_identity(url.host) != _host_identity(urlsplit(engine_url).hostname):
                        return None
                    async with client.stream("GET", url) as response:
                        if response.is_redirect:
                            location = response.headers.get("location")
                            if not location:
                                return None
                            url = response.url.join(location)
                            continue
                        if response.status_code != 200:
                            return None
                        # Retain partial data on a stalled/slow source. A fixed
                        # chunk size buffers small arrivals inside httpx, where
                        # cancellation would discard them before ffprobe sees them.
                        with anyio.move_on_after(max(0, deadline - asyncio.get_running_loop().time())):
                            async for chunk in response.aiter_bytes():
                                sample.extend(chunk[:SAMPLE_BYTES - len(sample)])
                                if len(sample) >= SAMPLE_BYTES:
                                    break
                        break
                if not sample:
                    return None
            process = await asyncio.create_subprocess_exec(
                binary, "-v", "error", "-protocol_whitelist", "pipe", "-f", "mpegts",
                "-show_entries", "format=bit_rate:packet=stream_index,pts_time,size:stream=index,codec_type,codec_name,channels,channel_layout:stream_tags=language,title", "-of", "json", "-i", "pipe:0",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await process.communicate(bytes(sample))
            if process.returncode != 0:
                return None
            payload = json.loads(stdout)
            audio = [stream for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"]
            return {"signal_verified": has_media_packets(payload), "bitrate_bps": sample_bitrate(payload), "audio_tracks": [
                {"index": index, "codec": stream.get("codec_name"), "channels": stream.get("channels"),
                 "channel_layout": stream.get("channel_layout"),
                 "language": stream.get("tags", {}).get("language"), "title": stream.get("tags", {}).get("title")}
                for index, stream in enumerate(audio)
            ]}
    except (TimeoutError, OSError, httpx.HTTPError, httpx.InvalidURL, ValueError, TypeError, AttributeError):
        return None
    finally:
        if process is not None and process.returncode is None:
            with anyio.CancelScope(shield=True):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
