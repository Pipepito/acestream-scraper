"""Quiet, coalesced channel refreshes with bounded engine and worker use."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from threading import Event

from app.config.database import SessionLocal
from app.repositories.channel_repository import ChannelRepository
from app.services.channel_status_service import ChannelStatusService
from app.services.probe_queue import ProbePriority
from app.services.tuner_service import supported_tuner_stream

logger = logging.getLogger(__name__)


# What a refresh checks while a channel plays. It used to check every source
# of the channel, one after another, restarted every 60 s and skipping only
# those checked in the last 30 s: a channel with 39 sources had all of them
# checked in 120 s of viewing, with a second engine session open almost all
# the time and half as much CPU again (33 % of a core against 23 % without
# it). On a small ARM machine the audio of the playing source stalled while
# it ran. Now it checks only the next sources the relay would try,
# and leaves alone the ones checked recently.
PLAYBACK_REFRESH_LIMIT = 3
PLAYBACK_REFRESH_MIN_AGE_SECONDS = 600


def refresh_channel(tv_channel_id: int, stopping: Event) -> None:
    """Look at the first PLAYBACK_REFRESH_LIMIT sources the relay would try
    after the one playing (HTTP ones too), and check those not checked in
    the last PLAYBACK_REFRESH_MIN_AGE_SECONDS. Once they are fresh a pass checks
    nothing; it does not walk further down the list. The source playing is
    owned by the relay (the status service skips it) and is not counted.
    `stopping` ends it early (the viewer left, or the application stops)."""
    from app.services.tuner_service import TunerService
    from app.services.stream_relay import relay_registry

    # This whole operation runs in a worker: never share the request's DB session
    # or perform synchronous SQL on the serving event loop.
    with SessionLocal() as db:
        by_id = {channel.id: channel for channel in ChannelRepository(db).get_tuner_streams(tv_channel_id)}
        playing = {info.content_id for info in relay_registry.active()}
        window = [by_id[i] for i in TunerService(db).relay_stream_ids(tv_channel_id)
                  if i in by_id and i not in playing]
        window = window[:PLAYBACK_REFRESH_LIMIT]
        service = ChannelStatusService(db)

        async def check() -> None:
            now = datetime.now(timezone.utc)
            for channel in window:
                if stopping.is_set():
                    break
                if not supported_tuner_stream(channel):
                    continue
                checked = channel.last_checked
                if checked is not None:
                    checked = checked.replace(tzinfo=timezone.utc) if checked.tzinfo is None else checked
                    if (now - checked).total_seconds() < PLAYBACK_REFRESH_MIN_AGE_SECONDS:
                        continue
                await service.check_channel_status(channel, priority=ProbePriority.PLAYBACK)
        asyncio.run(check())


class TunerProbeService:
    def __init__(self) -> None:
        self.tasks: dict[int, asyncio.Task] = {}
        self.stopping = Event()
        # Per channel: set when its viewer leaves, so a refresh does not go on
        # checking sources of a channel nobody watches any more.
        self.channel_stops: dict[int, Event] = {}
        self.slots: asyncio.Semaphore | None = None

    async def start_for_stream(self, content_id: str) -> None:
        def tv_channel_id() -> int | None:
            with SessionLocal() as db:
                return ChannelRepository(db).get_tv_channel_id_for_stream(content_id)
        try:
            channel_id = await asyncio.to_thread(tv_channel_id)
            if channel_id is not None:
                self.start(channel_id)
        except Exception:
            logger.warning('Could not queue TV-channel refresh for browser playback')

    def start(self, tv_channel_id: int) -> asyncio.Task | None:
        existing = self.tasks.get(tv_channel_id)
        if existing is not None:
            return existing
        # Limit queued channels as well as executing probes. Repeated viewers
        # share one refresh; full queues never delay an already-online source.
        if len(self.tasks) >= 32:
            return None
        if self.slots is None:
            self.slots = asyncio.Semaphore(1)
        self.stopping.clear()
        self.channel_stops[tv_channel_id] = Event()
        task = asyncio.create_task(self._run(tv_channel_id))
        self.tasks[tv_channel_id] = task
        return task

    async def _run(self, tv_channel_id: int) -> None:
        try:
            async with self.slots:
                channel_stop = self.channel_stops.get(tv_channel_id) or Event()
                if self.stopping.is_set():
                    channel_stop.set()
                if not channel_stop.is_set():
                    await asyncio.to_thread(refresh_channel, tv_channel_id, channel_stop)
        except Exception:
            logger.warning("Could not refresh tuner channel sources channel_id=%s", tv_channel_id)
        finally:
            self.tasks.pop(tv_channel_id, None)
            self.channel_stops.pop(tv_channel_id, None)

    def stop_channel(self, tv_channel_id: int) -> None:
        """The channel's viewer left: let its refresh end after the current check."""
        stop = self.channel_stops.get(tv_channel_id)
        if stop is not None:
            stop.set()

    async def stop(self) -> None:
        self.stopping.set()
        for channel_stop in list(self.channel_stops.values()):
            channel_stop.set()
        # Let the current bounded probe close its engine session and DB before
        # releasing the application's database lock. Queued work exits untouched.
        await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)
        self.slots = None


tuner_probe_service = TunerProbeService()
