"""A SourceReader played from a script, and a channel environment around it.

``FakeReader({cid: [...]})``: each read of ``cid`` yields the script's bytes
items in order, sleeps for its numbers and raises its exceptions; a source
without a script ends at once. It records what the relay opened, what it
released and whether it closed the reader.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import httpx

from app.services.channel_session import TunerEnvironment
from app.services.stream_relay import RelayRegistry


class FakeReader:
    def __init__(self, scripts=None):
        self.scripts = dict(scripts or {})
        self.opened = []
        self.released = []
        self.attempts = []
        self.closed = False

    def read(self, content_id, attempt):
        self.opened.append(content_id)
        self.attempts.append(attempt)
        return self._play(content_id, list(self.scripts.get(content_id, [])))

    async def _play(self, content_id, script):
        try:
            for item in script:
                if isinstance(item, BaseException):
                    raise item
                if isinstance(item, (int, float)):
                    await asyncio.sleep(item)
                    continue
                yield item
        finally:
            self.released.append(content_id)

    def route(self, content_id):
        return 'http' if content_id.startswith('url:') else 'direct'

    def close(self):
        self.closed = True


def environment(reader, *, candidates, last_resort=(), switch=False, registry=None, probes=None,
                start_seconds=1, budget_seconds=2):
    """A TunerEnvironment that reads every source through ``reader``.
    ``candidates`` / ``last_resort`` are lists or functions of the channel."""
    def choice(value):
        return value if callable(value) else (lambda _tv: list(value))
    settings = SimpleNamespace(experimental_transcoding=False, plex_compatible_audio=False,
                               source_start_seconds=start_seconds, startup_budget_seconds=budget_seconds)
    return TunerEnvironment(
        engine=Mock, settings=lambda: settings, slots=lambda: 1, client_factory=httpx.AsyncClient,
        switch_on_failure=lambda: switch, candidates=choice(candidates), last_resort=choice(last_resort),
        reader=lambda _engine, _label: reader, registry=registry or RelayRegistry(),
        probes=probes or SimpleNamespace(start=Mock(return_value=None), stop_channel=Mock()))
