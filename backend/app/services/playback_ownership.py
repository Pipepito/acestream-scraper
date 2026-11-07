"""Process-wide direct-engine ownership across short-lived clients.

Start and final stop for a source share a lock. Network calls happen only in
worker threads. Weak references keep abandoned handles from growing a permanent
registry; normal playback always explicitly releases its session.
"""
from __future__ import annotations

from _thread import RLock
from dataclasses import dataclass, field
from threading import Lock, Timer
from typing import Optional
from weakref import WeakSet, WeakValueDictionary

import httpx


@dataclass(eq=False)
class SourceOwnership:
    lock: RLock = field(default_factory=RLock)
    leases: WeakSet[PlaybackLease] = field(default_factory=WeakSet)
    # A final stop the TV relay deferred (EngineClient.stop linger_seconds);
    # a new start of the same source cancels it.
    pending_stop: Optional[Timer] = None
    # Sessions whose deferred stop a new start cancelled. Stopped with the
    # source's final stop, never before: a stop with any PID could end the
    # session being watched. Kept so none is left running on the engine.
    parked: list = field(default_factory=list)


@dataclass(eq=False)
class PlaybackLease:
    source: SourceOwnership
    released: bool = False


_sources: WeakValueDictionary[tuple[str, str], SourceOwnership] = WeakValueDictionary()
_registry_lock = Lock()


def source_ownership(engine_url: str, content_id: str) -> SourceOwnership:
    url = httpx.URL(engine_url)
    # Local factories can use either spelling for the same engine.
    if url.host in ('localhost', '127.0.0.1', '::1'):
        url = url.copy_with(host='localhost')
    key = (str(url).rstrip('/'), content_id.lower())
    with _registry_lock:
        source = _sources.get(key)
        if source is None:
            source = SourceOwnership()
            _sources[key] = source
        return source
