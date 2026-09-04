"""PlayerService: sessions, ffmpeg lifecycle, state machine, reaper (spec 5.1)."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

from app.services.engine_client import EngineClient
from app.services.player_service import PlayerLimitReached, PlayerService

FAKE_FFMPEG = Path(__file__).parent / "fake_ffmpeg.py"
IH = "0" * 40
IH2 = "1" * 40


class FakeSettings:
    def __init__(self, hls_dir, max_sessions=3, start_timeout=45):
        self.PLAYER_HLS_DIR = str(hls_dir)
        self.PLAYER_MAX_SESSIONS = max_sessions
        self.PLAYER_START_TIMEOUT_SECONDS = start_timeout
        self.FFMPEG_BINARY_PATH = ""


def _engine(handler=None):
    def default(request):
        p = request.url.path
        if p == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if "/ace/stat/" in p:
            return httpx.Response(200, json={"response": {"status": "dl", "peers": 3, "speed_down": 500, "speed_up": 10}, "error": None})
        return httpx.Response(200, text="ok")
    return EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler or default)))


@pytest.fixture
def make_service(tmp_path, monkeypatch):
    def factory(mode="normal", ffmpeg=str(FAKE_FFMPEG), handler=None, **settings):
        monkeypatch.setenv("FAKE_FFMPEG_MODE", mode)
        clock = {"now": 1000.0}
        svc = PlayerService(
            settings_getter=lambda: FakeSettings(tmp_path / "hls", **settings),
            engine_factory=lambda: _engine(handler),
            ffmpeg_path=ffmpeg,
            monotonic=lambda: clock["now"],
        )
        svc._clock = clock  # test hook to advance time
        return svc
    return factory


async def _wait(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return False


def test_open_session_spawns_ffmpeg_and_becomes_ready(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert s.state == "starting" and s.viewers == 1
            assert s.process is not None and (s.dir / "ffmpeg.pid").exists()
            assert await _wait(lambda: svc.hls_ready(s))
            await svc.tick()
            assert s.state == "ready"
            assert s.codecs == {"video": "h264", "audio": "ac3"}
            assert s.stats is not None and s.stats.peers == 3
            joined = await svc.open_session(IH)
            assert joined is s and s.viewers == 2
        finally:
            await svc.stop()
    asyncio.run(run())


def test_limit_reached(make_service):
    svc = make_service(max_sessions=1)

    async def run():
        await svc.start()
        try:
            await svc.open_session(IH)
            with pytest.raises(PlayerLimitReached) as exc:
                await svc.open_session(IH2)
            assert exc.value.limit == 1 and exc.value.active == 1
        finally:
            await svc.stop()
    asyncio.run(run())


def test_engine_refusal_creates_error_session(make_service):
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})
    svc = make_service(handler=handler)

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert s.state == "error" and s.error == "engine_refused" and "premium" in s.error_message
            assert s.process is None
        finally:
            await svc.stop()
    asyncio.run(run())


def test_ffmpeg_missing(make_service):
    svc = make_service(ffmpeg=None)
    svc.ffmpeg_path = lambda: None  # type: ignore[method-assign]

    async def run():
        s = await svc.open_session(IH)
        assert s.state == "error" and s.error == "ffmpeg_missing"
    asyncio.run(run())


def test_ffmpeg_exit_before_ready_is_ffmpeg_failed(make_service):
    svc = make_service(mode="exit_early")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: s.state == "error")
            assert s.error == "ffmpeg_failed" and "Connection refused" in s.error_message
        finally:
            await svc.stop()
    asyncio.run(run())


def test_stall_after_start_timeout(make_service):
    svc = make_service(mode="never_ready", start_timeout=1)

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            svc._clock["now"] += 2
            await svc.tick()
            assert s.state == "error" and s.error == "engine_stalled"
            assert "peers" in s.error_message
        finally:
            await svc.stop()
    asyncio.run(run())


def test_flooded_stderr_keeps_session_ready(make_service):
    svc = make_service(mode="flood_stderr")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: svc.hls_ready(s))
            await asyncio.sleep(0.5)
            await svc.tick()
            assert s.state == "ready"
            assert len(s.stderr_tail) <= 20
        finally:
            await svc.stop()
    asyncio.run(run())


def test_reaper_rules(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            # idle regardless of viewers
            svc._clock["now"] += 21
            await svc.tick()
            assert s.state == "stopped" and svc.get(s.id) is None and not s.dir.exists()

            s2 = await svc.open_session(IH)
            svc.touch(s2.id)
            svc.leave(s2.id)
            svc._clock["now"] += 6
            await svc.tick()
            assert s2.state == "stopped"

            s3 = await svc.open_session(IH)
            svc.touch(s3.id)
            svc._clock["now"] += 3
            svc.touch(s3.id)  # status polls keep it alive
            await svc.tick()
            assert s3.state != "stopped"
        finally:
            await svc.stop()
    asyncio.run(run())


def test_error_sessions_are_reaped_after_a_minute(make_service):
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "nope"})
    svc = make_service(handler=handler)

    async def run():
        s = await svc.open_session(IH)
        svc.touch(s.id)
        svc._clock["now"] += 61
        await svc.tick()
        assert svc.get(s.id) is None
    asyncio.run(run())


def test_teardown_tolerates_exited_process_and_keeps_ticking(make_service, monkeypatch):
    svc = make_service(mode="exit_early")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: s.state == "error")
            s2 = await svc.open_session(IH2)
            # Make the first teardown raise inside rmtree; the second session must still be handled.
            import shutil
            real_rmtree = shutil.rmtree
            calls = {"n": 0}

            def flaky(path, ignore_errors=False):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("boom")
                real_rmtree(path, ignore_errors=ignore_errors)
            monkeypatch.setattr(shutil, "rmtree", flaky)
            svc._clock["now"] += 61
            await svc.tick()
            svc._clock["now"] += 61
            await svc.tick()
            assert svc.get(s2.id) is None
        finally:
            monkeypatch.undo()
            await svc.stop()
    asyncio.run(run())


def test_startup_sweep_kills_only_our_ffmpeg(make_service, tmp_path):
    svc = make_service()
    hls = tmp_path / "hls"
    ours = hls / ("a" * 32)
    ours.mkdir(parents=True)
    foreign = hls / "keep-me"
    foreign.mkdir()
    (foreign / "note.txt").write_text("x")
    # A fake process whose cmdline contains our session dir.
    import subprocess
    proc = subprocess.Popen([sys.executable, "-c", f"import time; x={str(ours)!r}; time.sleep(60)"])
    (ours / "ffmpeg.pid").write_text(str(proc.pid))
    # A pid that is not ours (this test process).
    other = hls / ("b" * 32)
    other.mkdir()
    (other / "ffmpeg.pid").write_text(str(os.getpid()))

    async def run():
        await svc.start()
        await svc.stop()
    asyncio.run(run())
    assert proc.poll() is not None, "our stale ffmpeg must be killed"
    assert not ours.exists() and not other.exists()
    assert (foreign / "note.txt").exists()


def test_stop_tears_down_quickly(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        s = await svc.open_session(IH)
        assert await _wait(lambda: svc.hls_ready(s))
        t0 = time.monotonic()
        await svc.stop()
        assert time.monotonic() - t0 < 3.0
        assert s.state == "stopped" and not s.dir.exists()
    asyncio.run(run())


def test_spawn_argv_contains_required_flags(make_service):
    svc = make_service()
    argv = svc.ffmpeg_argv("http://engine/content/x", Path("/tmp/x"))
    assert argv[:9] == [str(FAKE_FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "info", "-nostats", "-rw_timeout", "20000000", "-fflags"]
    assert "-c:a" in argv and argv[argv.index("-c:a") + 1] == "aac"
    assert argv[-1] == "/tmp/x/index.m3u8"


def test_teardown_does_not_swallow_its_own_cancellation(make_service):
    """stop() cancels the service loop mid-tick; a teardown parked on its stderr
    reader must let that cancellation through, or stop() waits for a task that
    never ends."""
    svc = make_service()

    async def run():
        s = await svc.open_session(IH)
        parked = asyncio.Event()

        async def stubborn():
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                parked.set()  # ignore the first cancellation and stay pending
                await asyncio.Event().wait()

        s.reader.cancel()
        s.reader = asyncio.create_task(stubborn())
        teardown = asyncio.create_task(svc._teardown(s))
        await parked.wait()  # the teardown is now waiting on the reader
        teardown.cancel()
        with pytest.raises(asyncio.CancelledError):
            await teardown

    asyncio.run(run())


_STREAM_OK = {
    "response": {
        "playback_url": "http://engine:6878/content/x/1",
        "stat_url": "http://engine:6878/ace/stat/x/s",
        "command_url": "http://engine:6878/ace/cmd/x/s",
        "is_live": 1,
    },
    "error": None,
}
_STAT_OK = {"response": {"status": "dl", "peers": 3, "speed_down": 500, "speed_up": 10}, "error": None}


def test_launch_abandons_a_session_reaped_while_the_engine_answers(make_service):
    """The reaper can stop a session while _launch is still waiting on the
    engine (up to ~20 s). Resuming must not spawn an ffmpeg and a directory
    that nothing tracks, and must hand the engine handle back."""
    gate = threading.Event()
    stops: list[str] = []

    def handler(request):
        path = request.url.path
        if path == "/ace/getstream":
            gate.wait(10)
            return httpx.Response(200, json=_STREAM_OK)
        if "/ace/cmd/" in path:
            stops.append(str(request.url))
            return httpx.Response(200, text="ok")
        return httpx.Response(200, json=_STAT_OK)

    svc = make_service(handler=handler)

    async def run():
        session = None
        try:
            opening = asyncio.create_task(svc.open_session(IH))
            assert await _wait(lambda: bool(svc.sessions))
            session = next(iter(svc.sessions.values()))
            svc._clock["now"] += 21  # idle rule: the reaper takes it away mid-launch
            await svc.tick()
            assert session.state == "stopped" and svc.get(session.id) is None
            gate.set()
            assert await opening is session
            assert session.process is None, "no ffmpeg may be spawned for a stopped session"
            assert not session.dir.exists(), "no directory may be left behind"
            assert stops, "the engine handle the abandoned launch opened must be released"
            assert svc.sessions == {}
        finally:
            gate.set()
            # Only reached when the abort is missing: reap the leak by hand so the
            # assertion is what fails, instead of the loop hanging on its reader.
            if session is not None and session.process is not None:
                session.process.kill()
                await session.process.wait()
            await svc.stop()

    asyncio.run(run())


def test_reopening_after_an_error_retries_instead_of_replaying_the_failure(make_service):
    """The UI's Retry button re-posts the same content_id. Within the 60 s
    error window that must start a new attempt, not hand back the cached
    failure with no engine call at all."""
    attempts = {"n": 0}

    def handler(request):
        path = request.url.path
        if path == "/ace/getstream":
            attempts["n"] += 1
            if attempts["n"] == 1:
                return httpx.Response(200, json={"response": None, "error": "activate premium"})
            return httpx.Response(200, json=_STREAM_OK)
        if "/ace/stat/" in path:
            return httpx.Response(200, json=_STAT_OK)
        return httpx.Response(200, text="ok")

    svc = make_service(handler=handler)

    async def run():
        await svc.start()
        try:
            failed = await svc.open_session(IH)
            assert failed.state == "error" and failed.error == "engine_refused"

            retried = await svc.open_session(IH)
            assert retried is not failed
            assert attempts["n"] == 2, "the retry must reach the engine again"
            assert retried.state == "starting" and retried.viewers == 1
            assert svc.get(failed.id) is None and failed.state == "stopped"
            assert await _wait(lambda: svc.hls_ready(retried))
        finally:
            await svc.stop()

    asyncio.run(run())


def test_stalled_session_releases_its_ffmpeg_and_engine_stream(make_service):
    """A session that flips to ``error`` stops counting toward
    ``PLAYER_MAX_SESSIONS``, so it must not keep an ffmpeg process or an engine
    stream alive behind the freed slot."""
    stops: list[str] = []

    def handler(request):
        path = request.url.path
        if path == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if "/ace/cmd/" in path:
            stops.append(str(request.url))
            return httpx.Response(200, json={"response": "ok", "error": None})
        if "/ace/stat/" in path:
            return httpx.Response(200, json={"response": {"status": "prebuf", "peers": 0, "speed_down": 0, "speed_up": 0}, "error": None})
        return httpx.Response(200, text="ok")

    svc = make_service(mode="never_ready", start_timeout=1, max_sessions=1, handler=handler)

    async def run():
        await svc.start()
        try:
            stalled = await svc.open_session(IH)
            proc = stalled.process
            assert proc is not None
            svc._clock["now"] += 2
            await svc.tick()
            assert stalled.state == "error" and stalled.error == "engine_stalled"
            assert await _wait(lambda: proc.returncode is not None), "the stalled session kept its ffmpeg running"
            assert any("method=stop" in url for url in stops), "the stalled session kept its engine stream"
            # The slot it freed is real: the next channel runs alone, not alongside it.
            second = await svc.open_session(IH2)
            assert second.state == "starting" and second.process is not None
            alive = [s for s in svc.list_sessions() if s.process is not None and s.process.returncode is None]
            assert alive == [second]
        finally:
            await svc.stop()
    asyncio.run(run())


def test_startup_sweep_survives_an_unreadable_hls_dir(make_service, monkeypatch):
    """An unreadable PLAYER_HLS_DIR is a local misconfiguration, not a reason to
    abort startup: the optional player must never take the app down with it."""
    svc = make_service()
    root = svc.hls_dir()
    root.mkdir(parents=True)
    real_iterdir = Path.iterdir

    def refuse(self):
        if self == root:
            raise PermissionError(13, "Permission denied")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", refuse)

    async def run():
        await svc.start()
        await svc.stop()
    asyncio.run(run())


def test_launch_abandons_a_session_that_failed_while_the_engine_answers(make_service):
    """The start-timeout tick can move a session to ``error`` while _launch is
    still waiting on the engine. ``_fail`` has already released everything that
    session owned and freed its slot, so resuming must not hand it a fresh
    engine handle and an ffmpeg that nothing counts or reaps."""
    gate = threading.Event()
    stops: list[str] = []

    def handler(request):
        path = request.url.path
        if path == "/ace/getstream":
            gate.wait(10)
            return httpx.Response(200, json=_STREAM_OK)
        if "/ace/cmd/" in path:
            stops.append(str(request.url))
            return httpx.Response(200, text="ok")
        return httpx.Response(200, json=_STAT_OK)

    svc = make_service(handler=handler, start_timeout=1)

    async def run():
        session = None
        try:
            opening = asyncio.create_task(svc.open_session(IH))
            assert await _wait(lambda: bool(svc.sessions))
            session = next(iter(svc.sessions.values()))
            svc._clock["now"] += 2  # the start timeout fires mid-launch
            await svc.tick()
            assert session.state == "error" and session.error == "engine_stalled"
            gate.set()
            assert await opening is session
            assert session.process is None, "no ffmpeg may be spawned for a failed session"
            assert session.engine_session is None, "a failed session must not own an engine stream"
            assert not session.dir.exists(), "no directory may be left behind"
            assert any("method=stop" in url for url in stops), "the engine handle the abandoned launch opened must be released"
        finally:
            gate.set()
            # Only reached when the abort is missing: reap the leak by hand so the
            # assertion is what fails, instead of the loop hanging on its reader.
            if session is not None and session.process is not None:
                session.process.kill()
                await session.process.wait()
            await svc.stop()

    asyncio.run(run())


def test_tick_reads_session_stats_concurrently(make_service):
    """Two sessions must not queue behind one another: a stat call that only
    answers once both sessions have asked proves the tick fans them out. Run in
    series the first call would block until the barrier times out, and neither
    session would come back with statistics."""
    barrier = threading.Barrier(2, timeout=3)

    def handler(request):
        path = request.url.path
        if path == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if "/ace/stat/" in path:
            barrier.wait()  # BrokenBarrierError once the timeout expires
            return httpx.Response(200, json={"response": {"status": "dl", "peers": 3, "speed_down": 500, "speed_up": 10}, "error": None})
        return httpx.Response(200, text="ok")

    svc = make_service(handler=handler)

    async def run():
        try:
            first = await svc.open_session(IH)
            second = await svc.open_session(IH2)
            await svc.tick()
            assert first.stats is not None and second.stats is not None
            assert first.stats.peers == 3 and second.stats.peers == 3
        finally:
            await svc.stop()
    asyncio.run(run())
