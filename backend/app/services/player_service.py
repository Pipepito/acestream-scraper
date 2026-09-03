"""Web player sessions: one shared ffmpeg (video copy, audio -> AAC, HLS) per
channel, an asyncio reaper/stat loop and a startup sweep (spec 5.1)."""
from __future__ import annotations

import asyncio
import contextlib
import ctypes
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Literal, Optional, TypeVar

from fastapi.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.services.engine_client import (
    EngineClient,
    EngineRefusedError,
    EngineSession,
    EngineStats,
    EngineUnavailableError,
    engine_url_from_settings,
)

logger = logging.getLogger(__name__)

PlayerState = Literal["starting", "ready", "error", "stopped"]
PlayerError = Literal["engine_unavailable", "engine_refused", "engine_stalled", "ffmpeg_missing", "ffmpeg_failed"]

IDLE_SECONDS = 20.0
NO_VIEWERS_SECONDS = 5.0
ERROR_SECONDS = 60.0
TICK_SECONDS = 5.0
STDERR_TAIL = 20
_SESSION_DIR = re.compile(r"^[0-9a-f]{32}$")
_STREAM_LINE = re.compile(r"Stream #0:\d+.*?: (Video|Audio): ([A-Za-z0-9_]+)")

T = TypeVar("T")


class PlayerLimitReached(RuntimeError):
    """More distinct channels were requested than ``PLAYER_MAX_SESSIONS`` allows."""

    def __init__(self, limit: int, active: int):
        super().__init__(f"player session limit reached ({active}/{limit})")
        self.limit = limit
        self.active = active


@dataclass
class PlayerSession:
    id: str
    content_id: str
    dir: Path
    created_at: float
    last_access: float
    state: PlayerState = "starting"
    error: Optional[PlayerError] = None
    error_message: str = ""
    viewers: int = 0
    viewers_zero_since: Optional[float] = None
    engine_session: Optional[EngineSession] = None
    process: Optional[asyncio.subprocess.Process] = None
    codecs: Dict[str, Optional[str]] = field(default_factory=lambda: {"video": None, "audio": None})
    stats: Optional[EngineStats] = None
    stderr_tail: Deque[str] = field(default_factory=lambda: deque(maxlen=STDERR_TAIL))
    error_since: Optional[float] = None
    reader: Optional[asyncio.Task] = None


def _set_pdeathsig() -> None:  # runs in the child between fork and exec (Linux only)
    if sys.platform.startswith("linux"):
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG
        except Exception:  # noqa: BLE001 - a missing prctl must not stop playback
            pass


def _engine_from_settings() -> EngineClient:
    from app.config.database import SessionLocal
    from app.repositories.settings_repository import SettingsRepository

    db = SessionLocal()
    try:
        return EngineClient(engine_url_from_settings(SettingsRepository(db)))
    finally:
        db.close()


class PlayerService:
    """Owns every live web-player session: engine handles, ffmpeg processes,
    their HLS directories and the periodic reaper that removes them."""

    def __init__(
        self,
        *,
        settings_getter: Callable[[], Any] = get_settings,
        engine_factory: Callable[[], EngineClient] = _engine_from_settings,
        ffmpeg_path: Optional[str] = None,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self._settings = settings_getter
        self._engine_factory = engine_factory
        self._ffmpeg_override = ffmpeg_path
        self._now = monotonic
        self.sessions: Dict[str, PlayerSession] = {}
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    # --- configuration -------------------------------------------------------
    def hls_dir(self) -> Path:
        return Path(self._settings().PLAYER_HLS_DIR)

    def ffmpeg_path(self) -> Optional[str]:
        if self._ffmpeg_override:
            return self._ffmpeg_override
        configured = (self._settings().FFMPEG_BINARY_PATH or "").strip()
        if configured and os.access(configured, os.X_OK):
            return configured
        return shutil.which("ffmpeg")

    def capabilities(self) -> dict:
        path = self.ffmpeg_path()
        return {
            "ffmpeg_available": path is not None,
            "ffmpeg_path": path,
            "max_sessions": int(self._settings().PLAYER_MAX_SESSIONS),
            "hls_dir": str(self.hls_dir()),
        }

    def ffmpeg_argv(self, playback_url: str, directory: Path) -> List[str]:
        return [
            str(self.ffmpeg_path()), "-nostdin", "-hide_banner", "-loglevel", "info", "-nostats",
            "-rw_timeout", "20000000", "-fflags", "+genpts+discardcorrupt",
            "-i", playback_url, "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
            "-f", "hls", "-hls_time", "2", "-hls_list_size", "6", "-hls_delete_threshold", "2",
            "-hls_flags", "delete_segments+independent_segments+omit_endlist+temp_file",
            "-hls_segment_type", "mpegts", "-hls_segment_filename", str(directory / "seg%05d.ts"),
            str(directory / "index.m3u8"),
        ]

    # --- lifecycle -----------------------------------------------------------
    async def start(self) -> None:
        self._sweep_stale_dirs()
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._run_loop(), name="player-service-loop")
            self._loop_task.add_done_callback(self._on_loop_done)

    async def stop(self) -> None:
        if self._loop_task is not None:
            self._loop_task.remove_done_callback(self._on_loop_done)
            self._loop_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._loop_task
            self._loop_task = None
        for session in list(self.sessions.values()):
            await self._teardown(session, immediate=True)

    def _on_loop_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        logger.error("Player loop exited unexpectedly: %s; restarting", exc)
        self._loop_task = asyncio.create_task(self._run_loop(), name="player-service-loop")
        self._loop_task.add_done_callback(self._on_loop_done)

    async def _run_loop(self) -> None:
        while True:
            await asyncio.sleep(TICK_SECONDS)
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 - the loop must survive every tick
                logger.exception("Player tick failed")

    def _sweep_stale_dirs(self) -> None:
        """Kill ffmpeg processes left behind by a previous run and drop their
        directories. Only 32-hex directories carrying a pid whose command line
        mentions that directory are ours; anything else is left untouched."""
        root = self.hls_dir()
        if not root.is_dir():
            return
        for entry in root.iterdir():
            if not entry.is_dir() or not _SESSION_DIR.match(entry.name):
                continue
            pid_file = entry / "ffmpeg.pid"
            try:
                pid = int(pid_file.read_text().strip()) if pid_file.exists() else None
            except (OSError, ValueError):
                pid = None
            if pid and _cmdline_mentions(pid, str(entry)):
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(pid, signal.SIGKILL)
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline and _pid_alive(pid):
                    time.sleep(0.05)
            shutil.rmtree(entry, ignore_errors=True)

    # --- sessions ------------------------------------------------------------
    def list_sessions(self) -> List[PlayerSession]:
        return list(self.sessions.values())

    def get(self, session_id: str) -> Optional[PlayerSession]:
        return self.sessions.get(session_id)

    def touch(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is not None:
            session.last_access = self._now()

    def leave(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            return
        session.viewers = max(0, session.viewers - 1)
        if session.viewers == 0 and session.viewers_zero_since is None:
            session.viewers_zero_since = self._now()

    def playlist_path(self, session: PlayerSession) -> Path:
        return session.dir / "index.m3u8"

    def hls_ready(self, session: PlayerSession) -> bool:
        playlist = self.playlist_path(session)
        try:
            lines = playlist.read_text().splitlines()
        except OSError:
            return False
        return sum(1 for line in lines if line.strip().endswith(".ts")) >= 2

    async def open_session(self, content_id: str) -> PlayerSession:
        async with self._lock:
            for existing in self.sessions.values():
                if existing.content_id == content_id and existing.state in ("starting", "ready"):
                    existing.viewers += 1
                    existing.viewers_zero_since = None
                    existing.last_access = self._now()
                    return existing
            limit = int(self._settings().PLAYER_MAX_SESSIONS)
            active = sum(1 for s in self.sessions.values() if s.state in ("starting", "ready"))
            if active >= limit:
                raise PlayerLimitReached(limit, active)
            # Reopening a channel that failed is the player's Retry button. Drop the
            # failed attempt and start a new one instead of replaying its cached
            # error for the minute the reaper takes to clear it.
            retired = [s for s in self.sessions.values() if s.content_id == content_id and s.state == "error"]
            for old in retired:
                self.sessions.pop(old.id, None)
            now = self._now()
            session_id = uuid.uuid4().hex
            session = PlayerSession(
                id=session_id,
                content_id=content_id,
                dir=self.hls_dir() / session_id,
                created_at=now,
                last_access=now,
                viewers=1,
            )
            self.sessions[session.id] = session
        for old in retired:
            try:
                await self._teardown(old)
            except Exception:  # noqa: BLE001 - a failed cleanup must not block the retry
                logger.exception("Could not retire failed player session %s", old.id)
        await self._launch(session)
        return session

    async def _launch(self, session: PlayerSession) -> None:
        ffmpeg = self.ffmpeg_path()
        if ffmpeg is None:
            self._fail(session, "ffmpeg_missing", "ffmpeg is not installed on this server")
            return
        try:
            engine_session = await run_in_threadpool(
                self._engine_call, lambda engine: engine.start(session.content_id)
            )
        except EngineRefusedError as exc:
            self._fail(session, "engine_refused", str(exc))
            return
        except EngineUnavailableError as exc:
            self._fail(session, "engine_unavailable", str(exc))
            return
        if session.state == "stopped":
            # The reaper (or shutdown) tore the session down while the engine was
            # answering — a teardown that already ran would never reap what we are
            # about to create, so hand the engine handle back and spawn nothing.
            await self._stop_engine_session(session.content_id, engine_session)
            return
        session.engine_session = engine_session
        session.dir.mkdir(parents=True, exist_ok=True)
        argv = self.ffmpeg_argv(engine_session.playback_url, session.dir)
        process: Optional[asyncio.subprocess.Process] = None
        try:
            process = await asyncio.create_subprocess_exec(
                *argv, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE, start_new_session=True, preexec_fn=_set_pdeathsig,
            )
        except OSError as exc:
            self._fail(session, "ffmpeg_failed", f"could not start ffmpeg: {exc}")
        if session.state == "stopped":  # torn down during the spawn itself
            if process is not None:
                await self._terminate(process, immediate=True)
            shutil.rmtree(session.dir, ignore_errors=True)
            return
        if process is None:
            return
        session.process = process
        (session.dir / "ffmpeg.pid").write_text(str(process.pid))
        session.reader = asyncio.create_task(self._read_stderr(session), name=f"ffmpeg-stderr-{session.id[:8]}")

    def _engine_call(self, call: Callable[[EngineClient], T]) -> T:
        """Run one blocking engine call, always releasing the client's pool.

        Called through ``run_in_threadpool``: the factory opens a DB session to
        read ``ace_engine_url``, and the client it returns owns an httpx pool
        that would leak if it were not closed after every call.
        """
        engine = self._engine_factory()
        try:
            return call(engine)
        finally:
            engine.close()

    def _fail(self, session: PlayerSession, error: PlayerError, message: str) -> None:
        if session.state == "stopped":
            return
        session.state = "error"
        session.error = error
        session.error_message = message
        session.error_since = self._now()

    async def _read_stderr(self, session: PlayerSession) -> None:
        """Drain ffmpeg's stderr forever so the pipe cannot fill, keeping the
        last lines for error messages and picking the codecs out of them."""
        proc = session.process
        if proc is None or proc.stderr is None:
            return
        stream = proc.stderr
        try:
            while True:
                try:
                    raw = await stream.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    # A progress line without a newline overran the buffer.
                    raw = await stream.read(4096)
                if not raw:
                    break
                line = raw.decode("utf-8", "replace").replace("\r", "\n").strip()
                if not line:
                    continue
                session.stderr_tail.append(line[-300:])
                match = _STREAM_LINE.search(line)
                if match:
                    kind, codec = match.group(1).lower(), match.group(2).lower()
                    if session.codecs.get(kind) is None:
                        session.codecs[kind] = codec
        finally:
            with contextlib.suppress(Exception):
                await proc.wait()
            if session.state != "stopped":
                self._fail(
                    session,
                    "ffmpeg_failed",
                    " | ".join(list(session.stderr_tail)[-5:]) or f"ffmpeg exited with {proc.returncode}",
                )

    # --- periodic work -------------------------------------------------------
    async def tick(self) -> None:
        now = self._now()
        for session in list(self.sessions.values()):
            try:
                await self._tick_session(session, now)
            except Exception:  # noqa: BLE001 - one bad session must not stop the rest
                logger.exception("Player session %s tick failed", session.id)

    async def _tick_session(self, session: PlayerSession, now: float) -> None:
        if session.state in ("starting", "ready") and session.engine_session is not None:
            engine_session = session.engine_session
            try:
                session.stats = await run_in_threadpool(self._engine_call, lambda engine: engine.stat(engine_session))
            except Exception as exc:  # noqa: BLE001 - stats are best effort
                logger.warning("Player stats for %s unavailable: %s", session.content_id, exc)
        if session.state == "starting":
            if self.hls_ready(session):
                session.state = "ready"
            elif now - session.created_at > float(self._settings().PLAYER_START_TIMEOUT_SECONDS):
                stats = session.stats
                detail = f"{stats.peers} peers (status={stats.status})" if stats else "no engine statistics"
                self._fail(session, "engine_stalled", f"the stream did not start: {detail}")
        idle = now - session.last_access > IDLE_SECONDS
        no_viewers = (
            session.viewers == 0
            and session.viewers_zero_since is not None
            and now - session.viewers_zero_since > NO_VIEWERS_SECONDS
        )
        errored = session.state == "error" and session.error_since is not None and now - session.error_since > ERROR_SECONDS
        if idle or no_viewers or errored:
            await self._teardown(session)

    async def _terminate(self, proc: asyncio.subprocess.Process, *, immediate: bool) -> None:
        """Kill one ffmpeg process group and reap it: SIGTERM then SIGKILL after
        5 s, or SIGKILL straight away on shutdown."""
        if proc.returncode is not None:
            return
        try:
            pgid = os.getpgid(proc.pid)
        except ProcessLookupError:
            pgid = None
        with contextlib.suppress(ProcessLookupError):
            if pgid is not None:
                os.killpg(pgid, signal.SIGKILL if immediate else signal.SIGTERM)
        if not immediate:
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    if pgid is not None:
                        os.killpg(pgid, signal.SIGKILL)
        with contextlib.suppress(Exception):
            await asyncio.wait_for(proc.wait(), timeout=2.0)

    async def _stop_engine_session(self, content_id: str, engine_session: EngineSession) -> None:
        try:
            await run_in_threadpool(self._engine_call, lambda engine: engine.stop(engine_session))
        except Exception as exc:  # noqa: BLE001 - a dead engine must not block cleanup
            logger.warning("Engine stop for %s failed: %s", content_id, exc)

    async def _teardown(self, session: PlayerSession, immediate: bool = False) -> None:
        session.state = "stopped"
        if session.process is not None:
            await self._terminate(session.process, immediate=immediate)
        if session.reader is not None:
            session.reader.cancel()
            # gather() absorbs the reader's own CancelledError but still lets a
            # cancellation aimed at *this* teardown through, so stop() cannot
            # end up awaiting a loop task that quietly kept running.
            await asyncio.gather(session.reader, return_exceptions=True)
        if session.engine_session is not None:
            await self._stop_engine_session(session.content_id, session.engine_session)
        try:
            shutil.rmtree(session.dir, ignore_errors=True)
        except Exception:  # noqa: BLE001 - never let cleanup stop the loop
            logger.exception("Could not remove %s", session.dir)
        self.sessions.pop(session.id, None)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _cmdline_mentions(pid: int, needle: str) -> bool:
    proc_path = Path(f"/proc/{pid}/cmdline")
    try:
        if proc_path.exists():
            return needle in proc_path.read_bytes().decode("utf-8", "replace")
        out = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
        return needle in out.stdout
    except Exception:  # noqa: BLE001 - an unreadable process is not ours to kill
        return False


player_service = PlayerService()
