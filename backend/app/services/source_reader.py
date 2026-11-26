"""Reading the bytes of one source: the seam between the TV relay and where
the bytes come from.

The relay decides which source to try, for how long and what its end means;
a ``SourceReader`` only opens one source for one attempt and yields its
MPEG-TS bytes. Two real adapters: the AceStream engine (direct or Acexy) and
an HTTP/broadcaster source remuxed by FFmpeg. ``SourceReaders`` picks one of
them by the kind of source and is a reader itself. Tests use a fake reader.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Callable, Optional, Protocol

import httpx

from app.services.engine_client import EngineClient, EngineUnavailableError
from app.services.stream_relay import RelayInfo, RelayRegistry, relay_engine_stream
from app.services.tuner_http_source import relay_http_stream
from app.utils.stream_kind import stream_kind


@dataclass(frozen=True)
class Attempt:
    """What one attempt at a source gets from the relay."""
    claim: RelayInfo
    #: Absolute monotonic deadline for the first byte, shared with the relay.
    startup_deadline: float
    #: How long a read may stay silent while starting.
    read_seconds: float
    #: Asked when the reader is cancelled or closed: seconds to defer the
    #: engine's final stop (Kodi's second GET).
    stop_linger: Callable[[], float]
    #: Stereo AAC/LATM for Plex, done by the HTTP adapter's own FFmpeg.
    plex_compatible_audio: bool = False


class SourceReader(Protocol):
    def read(self, content_id: str, attempt: Attempt) -> AsyncIterator[bytes]:
        """The source's bytes. Errors surface on iteration, before the first
        byte for a start that fails: EngineRefusedError, EngineUnavailableError,
        EngineStreamError; an empty iterator is a session that ended at once.
        Closing it releases the source."""

    def route(self, content_id: str) -> str:
        """'direct', 'acexy' or 'http': how this source is read (logs)."""

    def close(self) -> None:
        """Release what the reader holds once the relay is done with it."""


class EngineReader:
    """An AceStream source through the playback engine (direct or Acexy)."""

    def __init__(self, engine: Optional[EngineClient], client_label: str, *, registry: RelayRegistry,
                 client_factory: Optional[Callable[..., httpx.AsyncClient]] = None,
                 open_stream: Callable[..., AsyncIterator[bytes]] = relay_engine_stream):
        self.engine = engine
        self.client_label = client_label
        self.registry = registry
        self.client_factory = client_factory
        self._open = open_stream

    def read(self, content_id: str, attempt: Attempt) -> AsyncIterator[bytes]:
        if self.engine is None:
            raise EngineUnavailableError('Acestream Engine URL is not configured')
        return self._open(self.engine, content_id, self.client_label, registry=self.registry,
                          client_factory=self.client_factory, claim=attempt.claim, release_claim=False,
                          stop_linger=attempt.stop_linger, read_seconds=attempt.read_seconds,
                          startup_deadline=attempt.startup_deadline)

    def route(self, content_id: str) -> str:
        return 'acexy' if self.engine is not None and self.engine.use_acexy else 'direct'

    def close(self) -> None:
        if self.engine is not None:
            self.engine.close()


class HttpReader:
    """A stored HTTP/broadcaster source, remuxed to MPEG-TS; no engine."""

    def __init__(self, open_stream: Callable[..., AsyncIterator[bytes]] = relay_http_stream):
        self._open = open_stream

    def read(self, content_id: str, attempt: Attempt) -> AsyncIterator[bytes]:
        return self._open(content_id, attempt.claim, startup_deadline=attempt.startup_deadline,
                          plex_compatible_audio=attempt.plex_compatible_audio)

    def route(self, content_id: str) -> str:
        return 'http'

    def close(self) -> None:
        pass


class SourceReaders:
    """The engine reader for AceStream IDs, the HTTP one for ``url:`` sources."""

    def __init__(self, engine: EngineReader, http: HttpReader):
        self.engine = engine
        self.http = http

    def _for(self, content_id: str) -> SourceReader:
        return self.http if stream_kind(content_id) == 'http' else self.engine

    def read(self, content_id: str, attempt: Attempt) -> AsyncIterator[bytes]:
        return self._for(content_id).read(content_id, attempt)

    def route(self, content_id: str) -> str:
        return self._for(content_id).route(content_id)

    def close(self) -> None:
        self.engine.close()
        self.http.close()
