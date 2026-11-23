"""An in-memory engine at the stream check's ``ProbeEngine`` seam.

Scripted with the engine's own answers, ``(http_status, json_or_None)``,
read the way the real adapter reads them (``engine_probe.read_*``). Each script
is a list whose last item repeats; an exception instance is raised instead, and
a callable is called with the request's arguments and answers in its place.
"""
from __future__ import annotations

from typing import Any, List

from app.services.engine_probe import ProbeSession, read_ready, read_start, read_stats

ENGINE = 'http://engine.test:6878'


def session_answer(engine: str = 'http://127.0.0.1:6878', token: str = 'session', **extra: Any) -> dict:
    """A start answer with a full session, as the engine sends it."""
    response = {
        'is_live': 1,
        'playback_url': f'{engine}/ace/r/hash/{token}',
        'stat_url': f'{engine}/ace/stat/hash/{token}',
        'command_url': f'{engine}/ace/cmd/hash/{token}',
    }
    response.update(extra)
    return {'response': response, 'error': None}


def stat_answer(status: str = 'dl', downloaded: int = 100, **extra: Any) -> tuple:
    return 200, {'response': {'status': status, 'downloaded': downloaded, **extra}}


class FakeProbeEngine:
    def __init__(self, engine_url: str = ENGINE, *, ready: Any = True, start: Any = None, stats: Any = None):
        self.engine_url = engine_url
        self.ready_script: List[Any] = _as_script(ready)
        self.start_script: List[Any] = _as_script(start if start is not None else (200, session_answer()))
        self.stats_script: List[Any] = _as_script(stats if stats is not None else stat_answer())
        self.calls: List[tuple] = []

    def __call__(self, engine_url: str) -> 'FakeProbeEngine':
        """Stand in as the factory too; remembers which URL the check asked for."""
        self.requested_url = self.engine_url = engine_url
        return self

    # -- what the check asked for -------------------------------------------------
    def asked(self, kind: str) -> List[tuple]:
        return [call[1:] for call in self.calls if call[0] == kind]

    @property
    def stopped(self) -> List[str]:
        """The command URL of each session the check stopped."""
        return [call[0] for call in self.asked('stop')]

    # -- ProbeEngine -------------------------------------------------------------
    async def ready(self) -> bool:
        self.calls.append(('ready',))
        answer = _next(self.ready_script)
        return answer if isinstance(answer, bool) else read_ready(*answer)

    async def open_probe(self, content_id: str, identifier: str, pid: str, timeout: float):
        self.calls.append(('open', content_id, identifier, pid, timeout))
        status, payload = _next(self.start_script, content_id, identifier, pid, timeout)
        return read_start(self.engine_url, content_id, status, payload)

    async def stats(self, session: ProbeSession, timeout: float):
        self.calls.append(('stats', session.stat_url, timeout))
        status, payload = _next(self.stats_script, session, timeout)
        return read_stats(status, payload)

    async def stop(self, session: ProbeSession) -> None:
        self.calls.append(('stop', session.command_url))


def _as_script(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else [value]


def _next(script: List[Any], *args: Any) -> Any:
    item = script.pop(0) if len(script) > 1 else script[0]
    if isinstance(item, BaseException):
        raise item
    if callable(item):
        item = item(*args)
        if isinstance(item, BaseException):
            raise item
    return item
