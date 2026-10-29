"""Capture primitives; no DB sessions, global scheduler or arbitrary FFmpeg input."""
import asyncio
import contextlib
from dataclasses import dataclass
import os
import sys
import time
from app.services.engine_client import start_engine_session
from app.services.player_http_source import PlayerHTTPSource


@dataclass
class OwnedProcess:
    process: asyncio.subprocess.Process
    control: int
    reader: asyncio.Task
    progress: dict

    async def close(self):
        if self.control >= 0:
            os.close(self.control)
            self.control = -1
        try:
            await asyncio.wait_for(asyncio.shield(self.process.wait()), 3)
        except TimeoutError:
            # The wrapper's finally owns FFmpeg. TERM requests its bounded
            # shutdown, rather than killing the wrapper before it reaps.
            with contextlib.suppress(ProcessLookupError):
                self.process.terminate()
            await asyncio.wait_for(self.process.wait(), 3)
        await self.reader


def capture_argv(binary, url):
    return [binary, '-nostdin', '-hide_banner', '-loglevel', 'error', '-nostats',
            '-progress', 'pipe:2', '-rw_timeout', '15000000',
            '-protocol_whitelist', 'http,tcp,crypto', '-format_whitelist', 'hls,mpegts,mov,aac,mp3,webvtt',
            '-http_proxy', '', '-i', url, '-map', '0:v:0?', '-map', '0:a?', '-c', 'copy',
            '-f', 'mpegts', '-mpegts_flags', '+resend_headers', '-flush_packets', '1', 'pipe:1']


async def spawn_owned(argv, output_fd, input_fd=None, ownership_fd=None):
    read, write = os.pipe()
    passing = (read, output_fd) if input_fd is None else (read, output_fd, input_fd)
    if ownership_fd is not None:
        passing += (ownership_fd,)
    # FFmpeg needs an inherited input descriptor for local derivatives. The
    # wrapper reopens it as stdin through /dev/fd only with explicit pass_fds.
    spawn = asyncio.create_task(asyncio.create_subprocess_exec(sys.executable, '-m',
        'app.services.recording_process', str(read), str(output_fd), str(ownership_fd if ownership_fd is not None else -1), *argv,
        pass_fds=passing, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        start_new_session=True))
    try:
        try:
            process = await asyncio.shield(spawn)
        except asyncio.CancelledError:
            process = await spawn
            os.close(write)
            write = -1
            await process.communicate()
            raise
    except BaseException:
        if write >= 0:
            os.close(write)
        raise
    finally:
        os.close(read)
    progress = {'media_us': -1, 'changed': time.monotonic()}

    async def drain():
        # Never retain stderr: signed URLs and headers may be present. Parse
        # only the bounded numeric progress protocol, discard everything else.
        buffer = b''
        while chunk := await process.stdout.read(4096):
            buffer = (buffer + chunk)[-8192:]
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                if line.startswith(b'out_time_us='):
                    try:
                        value = int(line.split(b'=', 1)[1])
                        if value > progress['media_us']:
                            progress.update(media_us=value, changed=time.monotonic())
                    except ValueError:
                        pass
    return OwnedProcess(process, write, asyncio.create_task(drain()), progress)


class CaptureInput:
    def __init__(self, client=None):
        self.client = client
        self.session = None
        self.http = None

    async def open(self, cid, deadline):
        if cid.startswith('url:'):
            self.http = await PlayerHTTPSource.open(cid, timeout=max(0, deadline-time.monotonic()))
            self.http.select_best_variant = True
            return self.http.playback_url
        self.session = await start_engine_session(
            lambda: self.client.start(cid, startup_deadline=deadline), self.client.stop)
        # Engine URLs are trusted configuration, but use the guarded media
        # proxy for returned URLs too: no arbitrary redirects reach FFmpeg.
        self.http = PlayerHTTPSource(self.session.playback_url, {})
        await self.http.start()
        return self.http.playback_url

    async def close(self):
        try:
            if self.http:
                await self.http.close()
        finally:
            if self.session:
                await asyncio.to_thread(self.client.stop, self.session)
                self.session = None
            if self.client:
                await asyncio.to_thread(self.client.close)
