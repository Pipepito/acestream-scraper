"""Quiet, coalesced channel refreshes with bounded engine and worker use."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from threading import Event

from app.config.database import SessionLocal
from app.repositories.channel_repository import ChannelRepository
from app.services.channel_status_service import ChannelStatusService
from app.services.probe_queue import ProbePriority

logger = logging.getLogger(__name__)


def refresh_channel(tv_channel_id: int, stopping: Event) -> None:
    # This whole operation runs in a worker: never share the request's DB session
    # or perform synchronous SQL on the serving event loop.
    with SessionLocal() as db:
        repository = ChannelRepository(db)
        channels = repository.get_tuner_streams(tv_channel_id)
        # Verify unknown/offline alternatives first; known online sources can play
        # immediately while this refresh runs.
        channels.sort(key=lambda channel: (channel.is_online is True, -(channel.bitrate_bps or 0), channel.id))
        service = ChannelStatusService(db)

        async def check() -> None:
            for channel in channels:
                if stopping.is_set():
                    break
                if not re.fullmatch(r"[0-9a-fA-F]{40}", channel.id):
                    continue
                checked = channel.last_checked
                if checked is not None:
                    checked = checked.replace(tzinfo=timezone.utc) if checked.tzinfo is None else checked
                    if (datetime.now(timezone.utc) - checked).total_seconds() < 30:
                        continue
                await service.check_channel_status(channel, priority=ProbePriority.PLAYBACK)
        asyncio.run(check())


class TunerProbeService:
    def __init__(self) -> None:
        self.tasks: dict[int, asyncio.Task] = {}
        self.stopping = Event()
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
        task = asyncio.create_task(self._run(tv_channel_id))
        self.tasks[tv_channel_id] = task
        return task

    async def _run(self, tv_channel_id: int) -> None:
        try:
            async with self.slots:
                if not self.stopping.is_set():
                    await asyncio.to_thread(refresh_channel, tv_channel_id, self.stopping)
        except Exception:
            logger.warning("Could not refresh tuner channel sources channel_id=%s", tv_channel_id)
        finally:
            self.tasks.pop(tv_channel_id, None)

    async def stop(self) -> None:
        self.stopping.set()
        # Let the current bounded probe close its engine session and DB before
        # releasing the application's database lock. Queued work exits untouched.
        await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)
        self.slots = None


tuner_probe_service = TunerProbeService()
